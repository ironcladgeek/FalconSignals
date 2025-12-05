"""Provider manager with automatic fallback logic."""

from datetime import date, datetime
from pathlib import Path
from typing import Optional

from src.data.models import AnalystRating, NewsArticle, StockPrice
from src.data.providers import DataProvider, DataProviderFactory
from src.data.repository import AnalystRatingsRepository
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ProviderManager:
    """Manages multiple data providers with automatic fallback.

    Tries primary provider first, then falls back to backup providers
    in priority order on failure. Tracks provider health and availability.
    """

    def __init__(
        self,
        primary_provider: str = "alpha_vantage",
        backup_providers: list[str] = None,
        db_path: Path | str | None = None,
    ):
        """Initialize provider manager.

        Args:
            primary_provider: Primary provider name (default: alpha_vantage)
            backup_providers: List of backup provider names (default: [yahoo_finance, finnhub])
            db_path: Optional path to database for storing analyst ratings
        """
        self.primary_provider_name = primary_provider
        self.backup_provider_names = backup_providers or ["yahoo_finance", "finnhub"]

        # Initialize providers
        self.primary_provider = self._create_provider(primary_provider)
        self.backup_providers = [self._create_provider(name) for name in self.backup_provider_names]

        # Track provider health
        self.provider_failures = {}

        # Initialize repository for historical data storage
        self.repository = None
        if db_path:
            try:
                self.repository = AnalystRatingsRepository(db_path)
                logger.debug(f"Analyst ratings repository initialized at {db_path}")
            except Exception as e:
                logger.warning(f"Failed to initialize analyst ratings repository: {e}")

        logger.debug(
            f"Provider manager initialized: primary={primary_provider}, "
            f"backups={self.backup_provider_names}"
        )

    def _create_provider(self, name: str) -> DataProvider:
        """Create provider instance.

        Args:
            name: Provider name

        Returns:
            Provider instance
        """
        try:
            provider = DataProviderFactory.create(name)
            logger.debug(f"Created provider: {name} (available={provider.is_available})")
            return provider
        except Exception as e:
            logger.error(f"Failed to create provider {name}: {e}")

            # Create a dummy unavailable provider
            class UnavailableProvider(DataProvider):
                def __init__(self):
                    super().__init__(name)
                    self.is_available = False

                def get_stock_prices(self, ticker, start_date, end_date):
                    raise NotImplementedError(f"Provider {name} is not available")

                def get_latest_price(self, ticker):
                    raise NotImplementedError(f"Provider {name} is not available")

            return UnavailableProvider()

    def get_stock_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[StockPrice]:
        """Fetch stock prices with automatic fallback.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            List of StockPrice objects

        Raises:
            RuntimeError: If all providers fail
        """
        providers_to_try = [self.primary_provider] + self.backup_providers
        errors = []

        for provider in providers_to_try:
            if not provider.is_available:
                logger.debug(f"Skipping unavailable provider: {provider.name}")
                continue

            try:
                logger.debug(
                    f"Fetching prices for {ticker} using {provider.name} "
                    f"({start_date.date()} to {end_date.date()})"
                )
                prices = provider.get_stock_prices(ticker, start_date, end_date)

                if prices:
                    logger.debug(f"Successfully fetched {len(prices)} prices from {provider.name}")
                    self._record_success(provider.name)
                    return prices
                else:
                    logger.warning(f"No prices returned from {provider.name}")

            except NotImplementedError as e:
                logger.debug(f"Provider {provider.name} doesn't support prices: {e}")
                errors.append(f"{provider.name}: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"Error fetching prices from {provider.name}: {e}")
                self._record_failure(provider.name)
                errors.append(f"{provider.name}: {str(e)}")
                continue

        # All providers failed
        error_msg = f"All providers failed for {ticker} prices: " + "; ".join(errors)
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def get_latest_price(self, ticker: str) -> StockPrice:
        """Fetch latest price with automatic fallback.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest StockPrice object

        Raises:
            RuntimeError: If all providers fail
        """
        providers_to_try = [self.primary_provider] + self.backup_providers
        errors = []

        for provider in providers_to_try:
            if not provider.is_available:
                logger.debug(f"Skipping unavailable provider: {provider.name}")
                continue

            try:
                logger.debug(f"Fetching latest price for {ticker} using {provider.name}")
                price = provider.get_latest_price(ticker)

                if price:
                    logger.debug(f"Successfully fetched latest price from {provider.name}")
                    self._record_success(provider.name)
                    return price

            except NotImplementedError as e:
                logger.debug(f"Provider {provider.name} doesn't support latest price: {e}")
                errors.append(f"{provider.name}: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"Error fetching latest price from {provider.name}: {e}")
                self._record_failure(provider.name)
                errors.append(f"{provider.name}: {str(e)}")
                continue

        # All providers failed
        error_msg = f"All providers failed for {ticker} latest price: " + "; ".join(errors)
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def get_news(
        self,
        ticker: str,
        limit: int = 50,
        as_of_date: datetime | None = None,
    ) -> list[NewsArticle]:
        """Fetch news articles with automatic fallback.

        Prioritizes providers with sentiment analysis (Alpha Vantage, Finnhub).
        Supports historical news fetching for backtesting.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles
            as_of_date: Optional date for historical news (only fetch news before this date)

        Returns:
            List of NewsArticle objects

        Raises:
            RuntimeError: If all providers fail
        """
        logger.debug(
            f"ProviderManager: Fetching news for {ticker} from primary provider: {self.primary_provider_name} "
            f"(as_of_date={as_of_date})"
        )
        # Prioritize providers with news sentiment capabilities
        providers_to_try = [self.primary_provider] + self.backup_providers
        errors = []

        for provider in providers_to_try:
            if not provider.is_available:
                logger.debug(f"Skipping unavailable provider: {provider.name}")
                continue

            try:
                logger.debug(f"Fetching news for {ticker} using {provider.name}")
                articles = provider.get_news(ticker, limit, as_of_date=as_of_date)

                if articles:
                    logger.debug(
                        f"Successfully fetched {len(articles)} articles from {provider.name}"
                    )
                    self._record_success(provider.name)
                    return articles
                else:
                    logger.debug(f"No articles returned from {provider.name}")

            except NotImplementedError as e:
                logger.debug(f"Provider {provider.name} doesn't support news: {e}")
                errors.append(f"{provider.name}: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"Error fetching news from {provider.name}: {e}")
                self._record_failure(provider.name)
                errors.append(f"{provider.name}: {str(e)}")
                continue

        # All providers failed
        error_msg = f"All providers failed for {ticker} news: " + "; ".join(errors)
        logger.warning(error_msg)  # Warn instead of error for news (not critical)
        return []  # Return empty list instead of raising

    def get_company_info(self, ticker: str) -> Optional[dict]:
        """Fetch company information with automatic fallback.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with company info or None if not available
        """
        # Prioritize providers with company info capabilities
        providers_to_try = [self.primary_provider] + self.backup_providers
        errors = []

        for provider in providers_to_try:
            if not provider.is_available:
                logger.debug(f"Skipping unavailable provider: {provider.name}")
                continue

            # Check if provider has get_company_info method
            if not hasattr(provider, "get_company_info"):
                logger.debug(f"Provider {provider.name} doesn't have get_company_info")
                continue

            try:
                logger.debug(f"Fetching company info for {ticker} using {provider.name}")
                info = provider.get_company_info(ticker)

                if info:
                    logger.debug(f"Successfully fetched company info from {provider.name}")
                    self._record_success(provider.name)
                    return info
                else:
                    logger.debug(f"No company info returned from {provider.name}")

            except Exception as e:
                logger.warning(f"Error fetching company info from {provider.name}: {e}")
                self._record_failure(provider.name)
                errors.append(f"{provider.name}: {str(e)}")
                continue

        # All providers failed
        logger.warning(f"All providers failed for {ticker} company info")
        return None

    def get_analyst_ratings(
        self,
        ticker: str,
        as_of_date: date | datetime | None = None,
        auto_persist: bool = True,
    ) -> Optional[AnalystRating]:
        """Fetch analyst ratings with database caching.

        Checks the database first for historical data, then falls back to APIs
        for current data. Can optionally store fetched data in database.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Optional historical date to fetch ratings as of
            auto_persist: If True, store fetched ratings in database

        Returns:
            AnalystRating object or None if not available

        Example:
            # Get latest ratings from API (and store in DB)
            ratings = manager.get_analyst_ratings("AAPL")

            # Get historical ratings from DB (if available)
            ratings = manager.get_analyst_ratings("AAPL", as_of_date=date(2024, 6, 1))
        """
        ticker = ticker.upper()

        # Check database first if historical date requested
        if as_of_date and self.repository:
            if isinstance(as_of_date, datetime):
                as_of_date = as_of_date.date()

            # Convert to period (first day of month)
            period_date = as_of_date.replace(day=1)
            db_ratings = self.repository.get_ratings(ticker, period_date)

            if db_ratings:
                logger.debug(
                    f"Found analyst ratings for {ticker} in database (period: {period_date})"
                )
                return db_ratings
            else:
                logger.debug(
                    f"No database ratings found for {ticker} (period: {period_date}), "
                    f"skipping API fetch for historical date"
                )
                return None

        # Fetch from APIs for current data
        providers_to_try = [self.primary_provider] + self.backup_providers
        errors = []

        for provider in providers_to_try:
            if not provider.is_available:
                logger.debug(f"Skipping unavailable provider: {provider.name}")
                continue

            # Check if provider has get_analyst_ratings method
            if not hasattr(provider, "get_analyst_ratings"):
                logger.debug(f"Provider {provider.name} doesn't have get_analyst_ratings")
                continue

            try:
                logger.debug(f"Fetching analyst ratings for {ticker} using {provider.name}")
                ratings = provider.get_analyst_ratings(ticker)

                if ratings:
                    logger.debug(f"Successfully fetched analyst ratings from {provider.name}")

                    # Store in database if enabled
                    if auto_persist and self.repository:
                        try:
                            self.repository.store_ratings(ratings, data_source=provider.name)
                            logger.debug(f"Stored analyst ratings for {ticker} in database")
                        except Exception as e:
                            logger.warning(f"Failed to store analyst ratings in database: {e}")

                    self._record_success(provider.name)
                    return ratings
                else:
                    logger.debug(f"No analyst ratings returned from {provider.name}")

            except Exception as e:
                logger.warning(f"Error fetching analyst ratings from {provider.name}: {e}")
                self._record_failure(provider.name)
                errors.append(f"{provider.name}: {str(e)}")
                continue

        # All providers failed
        logger.warning(f"All providers failed for {ticker} analyst ratings")
        return None

    def _record_success(self, provider_name: str) -> None:
        """Record successful provider call.

        Args:
            provider_name: Provider name
        """
        if provider_name in self.provider_failures:
            del self.provider_failures[provider_name]

    def _record_failure(self, provider_name: str) -> None:
        """Record failed provider call.

        Args:
            provider_name: Provider name
        """
        if provider_name not in self.provider_failures:
            self.provider_failures[provider_name] = 0
        self.provider_failures[provider_name] += 1

        if self.provider_failures[provider_name] >= 3:
            logger.warning(
                f"Provider {provider_name} has failed {self.provider_failures[provider_name]} times"
            )

    def get_health_status(self) -> dict:
        """Get provider health status.

        Returns:
            Dictionary with provider health information
        """
        return {
            "primary_provider": {
                "name": self.primary_provider.name,
                "available": self.primary_provider.is_available,
                "failures": self.provider_failures.get(self.primary_provider.name, 0),
            },
            "backup_providers": [
                {
                    "name": provider.name,
                    "available": provider.is_available,
                    "failures": self.provider_failures.get(provider.name, 0),
                }
                for provider in self.backup_providers
            ],
        }
