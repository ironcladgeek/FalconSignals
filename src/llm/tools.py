"""CrewAI tool adapters for analysis functions."""

import json
import time
from datetime import date, datetime
from functools import wraps

from crewai.tools import tool

from src.tools.analysis import TechnicalIndicatorTool
from src.tools.fetchers import FinancialDataFetcherTool, NewsFetcherTool, PriceFetcherTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


def tool_with_timeout(timeout_seconds=30):
    """Decorator to add timeout handling to tool functions.

    Args:
        timeout_seconds: Maximum time to wait for tool execution

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    logger.warning(
                        f"Tool {func.__name__} took {elapsed:.1f}s (exceeded {timeout_seconds}s timeout)"
                    )
                return result
            except TimeoutError as e:
                logger.error(f"Tool {func.__name__} timed out after {timeout_seconds}s: {e}")
                return json.dumps({"error": f"Tool execution timed out after {timeout_seconds}s"})
            except Exception as e:
                logger.error(
                    f"Tool {func.__name__} raised exception: {type(e).__name__}: {e}",
                    exc_info=False,
                )
                return json.dumps({"error": str(e), "error_type": type(e).__name__})

        return wrapper

    return decorator


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code.

    Args:
        obj: Object to serialize

    Returns:
        Serialized representation
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class CrewAIToolAdapter:
    """Adapts existing tools for use with CrewAI agents."""

    def __init__(self, db_path: str = None):
        """Initialize tool adapters.

        Args:
            db_path: Optional path to database for storing analyst ratings
        """
        self.price_fetcher = PriceFetcherTool()
        self.technical_tool = TechnicalIndicatorTool()
        self.news_fetcher = NewsFetcherTool()
        self.fundamental_fetcher = FinancialDataFetcherTool(db_path=db_path)
        # Cache to store data between tool calls
        self._data_cache = {}
        # Initialize tools once
        self._tools = self._create_tools()

    def _create_tools(self) -> list:
        """Create CrewAI-compatible tools.

        Returns:
            List of CrewAI tool instances
        """

        @tool("Fetch Price Data")
        @tool_with_timeout(timeout_seconds=15)
        def fetch_price_data(ticker: str, days_back: int = 60) -> str:
            """Fetch historical and current price data for an instrument.

            Args:
                ticker: Stock ticker symbol
                days_back: Number of days of history to fetch

            Returns:
                JSON string with summary of price data (full data cached for other tools)
            """
            try:
                logger.info(f"Fetching price data for {ticker} ({days_back} days)")
                result = self.price_fetcher.run(ticker, days_back=days_back)
                if "error" in result:
                    logger.error(f"Price fetcher returned error for {ticker}: {result['error']}")
                    return json.dumps({"error": result["error"]})

                # Store full data in cache for technical analysis
                cache_key = f"prices_{ticker}"
                prices_list = result.get("prices", [])
                self._data_cache[cache_key] = prices_list
                logger.debug(f"Cached {len(prices_list)} price points for {ticker}")

                # Return only summary to avoid truncation
                summary = {
                    "ticker": result.get("ticker"),
                    "count": result.get("count", 0),
                    "start_date": result.get("start_date"),
                    "end_date": result.get("end_date"),
                    "latest_price": result.get("latest_price"),
                    "cache_key": cache_key,
                    "message": f"Fetched {result.get('count', 0)} price data points. Use cache_key '{cache_key}' for technical analysis.",
                }

                logger.info(f"Price data fetch successful for {ticker}: {summary['count']} records")
                return json.dumps(summary, default=json_serial)
            except Exception as e:
                logger.error(
                    f"Unexpected error fetching price data for {ticker}: {e}", exc_info=True
                )
                return json.dumps({"error": str(e)})

        @tool("Calculate Technical Indicators")
        @tool_with_timeout(timeout_seconds=15)
        def calculate_technical_indicators(ticker: str) -> str:
            """Calculate technical indicators and return pre-computed analysis.

            This tool performs the mathematical calculations directly (rule-based)
            and returns the results for LLM interpretation.

            Args:
                ticker: Stock ticker symbol

            Returns:
                JSON string with calculated indicators and automated technical analysis
            """
            try:
                logger.info(f"Calculating technical indicators for {ticker}")
                # Use cached price data
                cache_key = f"prices_{ticker}"
                if cache_key not in self._data_cache:
                    logger.warning(
                        f"No cached price data for {ticker}. Call fetch_price_data first."
                    )
                    return json.dumps(
                        {
                            "error": f"No price data cached for {ticker}. Call fetch_price_data first."
                        }
                    )

                prices = self._data_cache[cache_key]
                if not prices:
                    logger.error(f"Cached price list is empty for {ticker}")
                    return json.dumps({"error": "No price data available"})

                logger.debug(f"Using {len(prices)} cached price points for {ticker}")

                # Perform rule-based technical analysis calculations
                result = self.technical_tool.run(prices)
                if "error" in result:
                    logger.error(f"Technical tool returned error for {ticker}: {result['error']}")
                    return json.dumps({"error": result["error"]})

                # Add interpretation hints for the LLM (but calculations are done)
                result["analysis_type"] = "rule_based_calculations"
                result["note"] = (
                    "Technical indicators calculated using mathematical formulas. LLM should interpret these signals."
                )

                logger.info(f"Technical indicators calculated successfully for {ticker}")
                return json.dumps(result, default=json_serial)
            except Exception as e:
                logger.error(
                    f"Unexpected error calculating technical indicators for {ticker}: {e}",
                    exc_info=True,
                )
                return json.dumps({"error": str(e)})

        @tool("Analyze Sentiment")
        @tool_with_timeout(timeout_seconds=20)
        def analyze_sentiment(ticker: str, max_articles: int = 50) -> str:
            """Fetch news and perform LLM-based sentiment analysis.

            This tool fetches news articles and uses LLM to analyze sentiment
            (since providers often don't include sentiment data).
            Includes fallback mechanism if API is unavailable.

            Args:
                ticker: Stock ticker symbol
                max_articles: Maximum number of articles to fetch

            Returns:
                JSON string with news articles for LLM sentiment analysis
            """
            try:
                logger.info(f"Fetching news articles for {ticker}")
                # Fetch news articles with timeout protection
                news_result = self.news_fetcher.run(ticker, limit=max_articles)

                if "error" in news_result:
                    logger.warning(f"News fetch failed for {ticker}: {news_result.get('error')}")
                    # Return neutral fallback - agent can still provide analysis
                    return json.dumps(
                        {
                            "ticker": ticker,
                            "articles": [],
                            "count": 0,
                            "fallback_mode": True,
                            "note": (
                                f"News fetch failed: {news_result.get('error')}. "
                                "Unable to fetch articles for sentiment analysis. "
                                "Please analyze based on available market data and provide neutral to cautious assessment."
                            ),
                        }
                    )

                articles = news_result.get("articles", [])
                logger.debug(f"Fetched {len(articles)} articles for {ticker}")

                if not articles:
                    logger.info(f"No articles found for {ticker}")
                    return json.dumps(
                        {
                            "ticker": ticker,
                            "articles": [],
                            "count": 0,
                            "note": "No news articles available for analysis. Use neutral sentiment assessment.",
                        }
                    )

                # Prepare articles for LLM analysis (limit fields to avoid truncation)
                articles_for_analysis = [
                    {
                        "title": a.get("title", ""),
                        "summary": (
                            a.get("summary", "")[:200] if a.get("summary") else ""
                        ),  # Limit summary length
                        "source": a.get("source", ""),
                        "published_date": a.get("published_date"),
                    }
                    for a in articles[:20]  # Limit to 20 most recent to avoid truncation
                ]

                result = {
                    "ticker": ticker,
                    "articles": articles_for_analysis,
                    "total_articles": len(articles),
                    "analysis_type": "llm_sentiment_analysis_required",
                    "note": (
                        "Articles fetched successfully. LLM should analyze each article's title and summary "
                        "to determine sentiment (positive/negative/neutral), score each article, identify "
                        "key themes and events, and provide an overall sentiment assessment."
                    ),
                }

                logger.info(
                    f"Sentiment analysis prepared for {ticker} with {len(articles_for_analysis)} articles"
                )
                return json.dumps(result, default=json_serial)
            except Exception as e:
                logger.error(
                    f"Unexpected error in sentiment analysis for {ticker}: {e}", exc_info=True
                )
                # Return graceful fallback even on exception
                return json.dumps(
                    {
                        "ticker": ticker,
                        "articles": [],
                        "count": 0,
                        "fallback_mode": True,
                        "error": str(e),
                        "note": (
                            "An error occurred while fetching news articles. "
                            "Please provide sentiment assessment based on other available data sources."
                        ),
                    }
                )

        @tool("Fetch Fundamental Data")
        @tool_with_timeout(timeout_seconds=25)
        def fetch_fundamental_data(ticker: str) -> str:
            """Fetch fundamental data using free tier APIs.

            This tool fetches real fundamental data from free tier endpoints:
            - Analyst recommendations (Finnhub free tier)
            - News sentiment scores (Finnhub free tier)
            - Price momentum context (Yahoo Finance free tier)

            Args:
                ticker: Stock ticker symbol

            Returns:
                JSON string with analyst consensus, sentiment, and momentum data
            """
            try:
                logger.info(f"Fetching fundamental data for {ticker}")
                # Fetch fundamental data using the tool
                fundamental_result = self.fundamental_fetcher.run(ticker)

                if "error" in fundamental_result:
                    logger.warning(
                        f"Fundamental data fetch error for {ticker}: {fundamental_result.get('error')}"
                    )
                    # Return graceful fallback even on error
                    return json.dumps(
                        {
                            "ticker": ticker,
                            "data_availability": "limited",
                            "analyst_consensus": {
                                "available": False,
                                "strong_buy": 0,
                                "buy": 0,
                                "hold": 0,
                                "sell": 0,
                                "strong_sell": 0,
                                "total_analysts": 0,
                                "period": "unknown",
                            },
                            "news_sentiment": {
                                "available": False,
                                "positive": 0,
                                "negative": 0,
                                "neutral": 0,
                                "note": "Unable to fetch sentiment data",
                            },
                            "price_momentum": {
                                "available": False,
                                "change_percent": 0,
                                "trend": "neutral",
                                "latest_price": None,
                                "period_days": 30,
                            },
                            "data_sources": "Limited data availability",
                            "note": (
                                f"Error fetching fundamental data: {fundamental_result.get('error')}. "
                                "Please provide analysis based on available market data."
                            ),
                        }
                    )

                # Extract data components
                analyst_data = fundamental_result.get("analyst_data", {})
                sentiment = fundamental_result.get("sentiment", {})
                price_context = fundamental_result.get("price_context", {})
                metrics = fundamental_result.get("metrics", {})
                data_availability = fundamental_result.get("data_availability", "unknown")

                # Check if we have any real data
                has_analyst_data = analyst_data and analyst_data.get("total_analysts", 0) > 0
                has_sentiment_data = sentiment and (
                    sentiment.get("positive", 0) + sentiment.get("negative", 0) > 0
                )
                has_price_data = price_context and price_context.get("change_percent") is not None
                has_metrics = metrics and any(
                    metrics.get(k)
                    for k in ["valuation", "profitability", "financial_health", "growth"]
                )

                logger.debug(
                    f"Fundamental data for {ticker}: analyst={has_analyst_data}, "
                    f"sentiment={has_sentiment_data}, price={has_price_data}, metrics={has_metrics}"
                )

                # Format for LLM analysis
                result = {
                    "ticker": ticker,
                    "data_availability": data_availability,
                    "analyst_consensus": {
                        "available": has_analyst_data,
                        "strong_buy": analyst_data.get("strong_buy", 0),
                        "buy": analyst_data.get("buy", 0),
                        "hold": analyst_data.get("hold", 0),
                        "sell": analyst_data.get("sell", 0),
                        "strong_sell": analyst_data.get("strong_sell", 0),
                        "total_analysts": analyst_data.get("total_analysts", 0),
                        "period": analyst_data.get("period", "latest"),
                    },
                    "news_sentiment": {
                        "available": has_sentiment_data,
                        "positive": sentiment.get("positive", 0),
                        "negative": sentiment.get("negative", 0),
                        "neutral": sentiment.get("neutral", 0),
                        "note": (
                            "Sentiment from news coverage analysis"
                            if has_sentiment_data
                            else "No sentiment data available"
                        ),
                    },
                    "price_momentum": {
                        "available": has_price_data,
                        "change_percent": price_context.get("change_percent", 0),
                        "trend": price_context.get("trend", "neutral"),
                        "latest_price": price_context.get("latest_price"),
                        "period_days": price_context.get("period_days", 30),
                    },
                    "metrics": {
                        "available": has_metrics,
                        "valuation": metrics.get("valuation", {}),
                        "profitability": metrics.get("profitability", {}),
                        "financial_health": metrics.get("financial_health", {}),
                        "growth": metrics.get("growth", {}),
                    },
                    "data_sources": "Free tier APIs only (Finnhub + Yahoo Finance)",
                    "note": (
                        "Real fundamental data from free tier endpoints. "
                        "IMPORTANT: Use the 'metrics' section to extract financial ratios. "
                        f"Data available: {data_availability}. "
                        "Extract pe_ratio from metrics.valuation.trailing_pe, "
                        "profit_margin from metrics.profitability.profit_margin, etc."
                    ),
                }

                logger.info(f"Fundamental analysis prepared for {ticker}")
                return json.dumps(result, default=json_serial)
            except Exception as e:
                logger.error(
                    f"Unexpected error fetching fundamental data for {ticker}: {e}", exc_info=True
                )
                # Return graceful fallback even on exception
                return json.dumps(
                    {
                        "ticker": ticker,
                        "data_availability": "unavailable",
                        "analyst_consensus": {
                            "available": False,
                            "strong_buy": 0,
                            "buy": 0,
                            "hold": 0,
                            "sell": 0,
                            "strong_sell": 0,
                            "total_analysts": 0,
                            "period": "unknown",
                        },
                        "news_sentiment": {
                            "available": False,
                            "positive": 0,
                            "negative": 0,
                            "neutral": 0,
                            "note": "Unable to fetch sentiment data",
                        },
                        "price_momentum": {
                            "available": False,
                            "change_percent": 0,
                            "trend": "neutral",
                            "latest_price": None,
                            "period_days": 30,
                        },
                        "data_sources": "No data available",
                        "error": str(e),
                        "note": (
                            "An error occurred while fetching fundamental data. "
                            "Please provide analysis based on available technical indicators and other market data."
                        ),
                    }
                )

        return [
            fetch_price_data,
            calculate_technical_indicators,
            analyze_sentiment,
            fetch_fundamental_data,
        ]

    def get_crewai_tools(self) -> list:
        """Get all tools as CrewAI-compatible tool list.

        Returns:
            List of CrewAI tool instances
        """
        return self._tools
