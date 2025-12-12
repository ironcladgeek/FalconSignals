"""Unified news collection with source prioritization and deduplication.

Provides a single source of truth for news data per ticker with configurable
source prioritization and article count targets.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from src.data.models import NewsArticle
from src.data.providers import DataProvider, DataProviderFactory
from src.utils.logging import get_logger

logger = get_logger(__name__)


class NewsSourceConfig:
    """Configuration for a news source."""

    def __init__(
        self,
        name: str,
        priority: int = 1,
        enabled: bool = True,
        max_articles: int = 50,
    ):
        """Initialize news source config.

        Args:
            name: Provider name (e.g., 'alpha_vantage', 'finnhub')
            priority: Priority order (lower = higher priority)
            enabled: Whether this source is enabled
            max_articles: Maximum articles to fetch from this source
        """
        self.name = name
        self.priority = priority
        self.enabled = enabled
        self.max_articles = max_articles


class UnifiedNewsAggregator:
    """Unified news collection with source prioritization and deduplication.

    Fetches news from multiple sources based on priority, deduplicates articles,
    and stores them in a single cache file per ticker.
    """

    def __init__(
        self,
        sources: Optional[list[NewsSourceConfig]] = None,
        target_article_count: int = 50,
        max_age_days: int = 7,
        cache_manager=None,
    ):
        """Initialize news aggregator.

        Args:
            sources: List of news source configurations. Defaults to Alpha Vantage + Finnhub.
            target_article_count: Target number of articles to fetch
            max_age_days: Maximum age of articles to include
            cache_manager: Optional cache manager for storing aggregated news
        """
        self.target_article_count = target_article_count
        self.max_age_days = max_age_days
        self.cache_manager = cache_manager

        # Default sources if not provided
        if sources is None:
            self.sources = [
                NewsSourceConfig(name="alpha_vantage", priority=1, max_articles=50),
                NewsSourceConfig(name="finnhub", priority=2, max_articles=50),
            ]
        else:
            self.sources = sources

        # Sort sources by priority
        self.sources = sorted(self.sources, key=lambda s: s.priority)

        # Initialize providers
        self._providers: dict[str, DataProvider] = {}
        for source in self.sources:
            if source.enabled:
                try:
                    provider = DataProviderFactory.create(source.name)
                    if provider.is_available:
                        self._providers[source.name] = provider
                        logger.debug(f"Initialized news provider: {source.name}")
                    else:
                        logger.debug(f"Provider {source.name} not available (missing API key?)")
                except Exception as e:
                    logger.warning(f"Could not initialize provider {source.name}: {e}")

    def fetch_news(
        self,
        ticker: str,
        lookback_days: Optional[int] = None,
        as_of_date: Optional[datetime] = None,
    ) -> list[NewsArticle]:
        """Fetch news articles from all enabled sources.

        Fetches from sources in priority order until target article count is reached.
        Deduplicates articles by URL and title similarity.

        Args:
            ticker: Stock ticker symbol
            lookback_days: Number of days to look back (default: max_age_days)
            as_of_date: Historical date for backtesting (default: now)

        Returns:
            List of deduplicated news articles sorted by date (newest first)
        """
        if lookback_days is None:
            lookback_days = self.max_age_days

        if as_of_date is None:
            as_of_date = datetime.now()

        # Check cache first
        cache_key = self._make_cache_key(ticker, as_of_date)
        if self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for news: {ticker}")
                return [NewsArticle(**a) for a in cached.get("articles", [])]

        # Fetch from sources in priority order
        all_articles: list[NewsArticle] = []
        sources_used = []

        for source in self.sources:
            if not source.enabled or source.name not in self._providers:
                continue

            if len(all_articles) >= self.target_article_count:
                logger.debug(
                    f"Reached target article count ({self.target_article_count}), "
                    f"skipping remaining sources"
                )
                break

            try:
                provider = self._providers[source.name]
                remaining_needed = self.target_article_count - len(all_articles)
                limit = min(source.max_articles, remaining_needed + 20)  # Fetch extra for dedup

                articles = provider.get_news(
                    ticker,
                    limit=limit,
                    as_of_date=as_of_date,
                )

                if articles:
                    # Filter by date range
                    cutoff_date = as_of_date - timedelta(days=lookback_days)
                    filtered = [
                        a for a in articles if self._parse_date(a.published_date) >= cutoff_date
                    ]

                    all_articles.extend(filtered)
                    sources_used.append(source.name)
                    logger.info(f"Fetched {len(filtered)} articles from {source.name} for {ticker}")

            except Exception as e:
                logger.warning(f"Error fetching news from {source.name} for {ticker}: {e}")

        # Deduplicate
        unique_articles = self._deduplicate(all_articles)

        # Sort by date (newest first)
        unique_articles.sort(
            key=lambda a: self._parse_date(a.published_date),
            reverse=True,
        )

        # Trim to target count
        result = unique_articles[: self.target_article_count]

        # Cache the results
        if self.cache_manager and result:
            self._cache_articles(ticker, result, sources_used, as_of_date)

        logger.info(
            f"Aggregated {len(result)} unique articles for {ticker} from sources: {sources_used}"
        )

        return result

    def get_sentiment_summary(
        self,
        articles: list[NewsArticle],
    ) -> dict[str, Any]:
        """Calculate sentiment summary from articles.

        Args:
            articles: List of news articles

        Returns:
            Dictionary with sentiment metrics
        """
        if not articles:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "avg_sentiment_score": 0.0,
                "overall_sentiment": "neutral",
            }

        positive = sum(1 for a in articles if a.sentiment == "positive")
        negative = sum(1 for a in articles if a.sentiment == "negative")
        neutral = sum(1 for a in articles if a.sentiment == "neutral")
        total = len(articles)

        # Calculate average sentiment score
        scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Determine overall sentiment
        if avg_score > 0.1:
            overall = "positive"
        elif avg_score < -0.1:
            overall = "negative"
        else:
            overall = "neutral"

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_pct": round(100 * positive / total, 1) if total > 0 else 0,
            "negative_pct": round(100 * negative / total, 1) if total > 0 else 0,
            "neutral_pct": round(100 * neutral / total, 1) if total > 0 else 0,
            "avg_sentiment_score": round(avg_score, 3),
            "overall_sentiment": overall,
        }

    def _deduplicate(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        """Remove duplicate articles based on URL and title similarity.

        Args:
            articles: List of articles to deduplicate

        Returns:
            List of unique articles
        """
        seen_urls = set()
        seen_titles = set()
        unique = []

        for article in articles:
            # Check URL uniqueness
            if article.url in seen_urls:
                continue

            # Check title similarity (normalize for comparison)
            normalized_title = self._normalize_title(article.title)
            if normalized_title in seen_titles:
                continue

            seen_urls.add(article.url)
            seen_titles.add(normalized_title)
            unique.append(article)

        if len(articles) != len(unique):
            logger.debug(f"Deduplicated {len(articles)} -> {len(unique)} articles")

        return unique

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison.

        Args:
            title: Article title

        Returns:
            Normalized title (lowercase, stripped, no extra spaces)
        """
        import re

        # Convert to lowercase and strip
        normalized = title.lower().strip()

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        # Remove common prefixes/suffixes that vary between sources
        for prefix in ["breaking:", "update:", "exclusive:"]:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :].strip()

        return normalized

    def _parse_date(self, date_value) -> datetime:
        """Parse date from various formats.

        Args:
            date_value: Date as string or datetime

        Returns:
            datetime object
        """
        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            # Try common formats
            formats = [
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_value[:19], fmt[:19])
                except ValueError:
                    continue

            # Fallback: try parsing with dateutil if available
            try:
                from dateutil import parser

                return parser.parse(date_value)
            except (ImportError, ValueError):
                pass

        # Default to now if parsing fails
        logger.warning(f"Could not parse date: {date_value}")
        return datetime.now()

    def _make_cache_key(self, ticker: str, as_of_date: datetime) -> str:
        """Create cache key for news data.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Reference date

        Returns:
            Cache key string
        """
        date_str = as_of_date.strftime("%Y-%m-%d")
        return f"unified_news:{ticker}:{date_str}"

    def _cache_articles(
        self,
        ticker: str,
        articles: list[NewsArticle],
        sources: list[str],
        as_of_date: datetime,
    ) -> None:
        """Cache aggregated articles.

        Args:
            ticker: Stock ticker symbol
            articles: List of articles to cache
            sources: List of source names used
            as_of_date: Reference date
        """
        if not self.cache_manager:
            return

        cache_key = self._make_cache_key(ticker, as_of_date)
        cache_data = {
            "ticker": ticker,
            "articles": [a.model_dump() for a in articles],
            "count": len(articles),
            "sources": sources,
            "fetched_at": datetime.now().isoformat(),
            "as_of_date": as_of_date.isoformat(),
        }

        # Cache for 4 hours (news TTL)
        self.cache_manager.set(cache_key, cache_data, ttl_hours=4)
        logger.debug(f"Cached {len(articles)} articles for {ticker}")

    def get_available_sources(self) -> list[str]:
        """Get list of available (initialized) news sources.

        Returns:
            List of provider names that are available
        """
        return list(self._providers.keys())

    def get_source_stats(self) -> dict[str, Any]:
        """Get statistics about news sources.

        Returns:
            Dictionary with source statistics
        """
        return {
            "configured_sources": [s.name for s in self.sources if s.enabled],
            "available_sources": self.get_available_sources(),
            "target_article_count": self.target_article_count,
            "max_age_days": self.max_age_days,
        }
