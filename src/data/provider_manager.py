"""Provider manager with automatic fallback logic."""

from datetime import datetime
from typing import Optional

from src.data.models import NewsArticle, StockPrice
from src.data.providers import DataProvider, DataProviderFactory
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
    ):
        """Initialize provider manager.

        Args:
            primary_provider: Primary provider name (default: alpha_vantage)
            backup_providers: List of backup provider names (default: [yahoo_finance, finnhub])
        """
        self.primary_provider_name = primary_provider
        self.backup_provider_names = backup_providers or ["yahoo_finance", "finnhub"]

        # Initialize providers
        self.primary_provider = self._create_provider(primary_provider)
        self.backup_providers = [self._create_provider(name) for name in self.backup_provider_names]

        # Track provider health
        self.provider_failures = {}

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
    ) -> list[NewsArticle]:
        """Fetch news articles with automatic fallback.

        Prioritizes providers with sentiment analysis (Alpha Vantage, Finnhub).

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles

        Returns:
            List of NewsArticle objects

        Raises:
            RuntimeError: If all providers fail
        """
        logger.debug(
            f"ProviderManager: Fetching news for {ticker} from primary provider: {self.primary_provider_name}"
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
                articles = provider.get_news(ticker, limit)

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
