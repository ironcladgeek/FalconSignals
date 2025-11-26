"""Abstract data provider interface and implementations."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from src.data.models import (
    AnalystRating,
    FinancialStatement,
    InstrumentMetadata,
    InstrumentType,
    Market,
    NewsArticle,
    StockPrice,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DataProvider(ABC):
    """Abstract base class for financial data providers."""

    def __init__(self, name: str):
        """Initialize data provider.

        Args:
            name: Provider name (e.g., 'yahoo_finance', 'alpha_vantage')
        """
        self.name = name
        self.is_available = False

    @abstractmethod
    def get_stock_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[StockPrice]:
        """Fetch stock price data.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            List of StockPrice objects

        Raises:
            ValueError: If ticker is invalid
            RuntimeError: If API call fails
        """

    @abstractmethod
    def get_latest_price(self, ticker: str) -> StockPrice:
        """Fetch latest stock price.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest StockPrice object

        Raises:
            ValueError: If ticker is invalid
            RuntimeError: If API call fails
        """

    def get_financial_statements(
        self,
        ticker: str,
        statement_type: str = "income_statement",
        limit: int = 5,
    ) -> list[FinancialStatement]:
        """Fetch financial statements.

        Args:
            ticker: Stock ticker symbol
            statement_type: Type of statement (income_statement, balance_sheet, cash_flow)
            limit: Number of periods to fetch

        Returns:
            List of FinancialStatement objects

        Raises:
            NotImplementedError: If provider doesn't support this
        """
        raise NotImplementedError(f"Provider {self.name} does not support financial statements")

    def get_news(
        self,
        ticker: str,
        limit: int = 10,
        max_age_hours: int = 24,
    ) -> list[NewsArticle]:
        """Fetch news articles.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of articles
            max_age_hours: Maximum age of articles in hours

        Returns:
            List of NewsArticle objects

        Raises:
            NotImplementedError: If provider doesn't support this
        """
        raise NotImplementedError(f"Provider {self.name} does not support news fetching")

    def get_analyst_ratings(self, ticker: str) -> Optional[AnalystRating]:
        """Fetch analyst ratings and consensus.

        Args:
            ticker: Stock ticker symbol

        Returns:
            AnalystRating object or None if not available

        Raises:
            NotImplementedError: If provider doesn't support this
        """
        raise NotImplementedError(f"Provider {self.name} does not support analyst ratings")

    def get_instrument_metadata(self, ticker: str) -> InstrumentMetadata:
        """Fetch instrument metadata.

        Args:
            ticker: Stock ticker symbol

        Returns:
            InstrumentMetadata object

        Raises:
            ValueError: If ticker is invalid
            RuntimeError: If API call fails
        """
        raise NotImplementedError(f"Provider {self.name} does not support metadata fetching")

    def validate_ticker(self, ticker: str) -> bool:
        """Validate if ticker exists.

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if ticker is valid, False otherwise
        """
        try:
            self.get_latest_price(ticker)
            return True
        except Exception:
            return False

    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(name={self.name})>"


class DataProviderFactory:
    """Factory for creating data providers."""

    _providers = {}

    @classmethod
    def register(cls, name: str, provider_class: type[DataProvider]) -> None:
        """Register a provider.

        Args:
            name: Provider identifier
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
        logger.debug(f"Registered data provider: {name}")

    @classmethod
    def create(cls, name: str, **kwargs) -> DataProvider:
        """Create provider instance.

        Args:
            name: Provider identifier
            **kwargs: Additional arguments for provider

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not registered
        """
        if name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"Unknown provider: {name}. Available: {available}")
        provider_class = cls._providers[name]
        logger.debug(f"Creating provider instance: {name}")
        return provider_class(**kwargs)

    @classmethod
    def get_available(cls) -> list[str]:
        """Get list of available providers.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    @classmethod
    def reset(cls) -> None:
        """Clear all registered providers."""
        cls._providers.clear()
