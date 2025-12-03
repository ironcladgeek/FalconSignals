"""Historical data fetcher for backtesting and historical analysis.

This module provides tools to fetch data as it would have been available
on a specific date in the past, with strict date filtering to prevent
future data leakage.
"""

from datetime import datetime, timedelta

from src.data.models import HistoricalContext
from src.data.providers import DataProvider
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HistoricalDataFetcher:
    """Fetch historical data as of a specific date.

    This fetcher ensures that only data available up to a specific date
    is returned, preventing look-ahead bias in backtesting.
    """

    def __init__(self, provider: DataProvider):
        """Initialize historical data fetcher.

        Args:
            provider: DataProvider instance for fetching data
        """
        self.provider = provider

    def fetch_as_of_date(
        self,
        ticker: str,
        as_of_date,  # Can be datetime or date
        lookback_days: int = 365,
    ) -> HistoricalContext:
        """Fetch all data as it would have been available on as_of_date.

        This method implements strict date filtering to prevent future data leakage.
        Only data with dates <= as_of_date is included in the result.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Date for which to fetch data (datetime or date object)
            lookback_days: Number of historical days to include

        Returns:
            HistoricalContext with all available data as of the given date

        Raises:
            ValueError: If ticker is invalid
            RuntimeError: If data fetching fails
        """
        # Convert date to datetime if needed
        if hasattr(as_of_date, "date") and callable(as_of_date.date):
            # It's a datetime object
            as_of_datetime = as_of_date
            as_of_date_only = as_of_date.date()
        else:
            # It's already a date object
            as_of_date_only = as_of_date
            as_of_datetime = datetime.combine(as_of_date, datetime.max.time())

        logger.debug(
            f"Fetching historical data for {ticker} as of {as_of_date_only} "
            f"({lookback_days} day lookback)"
        )

        context = HistoricalContext(
            ticker=ticker,
            as_of_date=as_of_datetime,
            lookback_days=lookback_days,
            data_available=True,
            missing_data_warnings=[],
        )

        # Calculate start date
        start_date = as_of_datetime - timedelta(days=lookback_days)
        logger.debug(f"Fetching price data from {start_date} to {as_of_datetime}")

        try:
            # Fetch price data with strict date filtering
            all_prices = self.provider.get_stock_prices(ticker, start_date, as_of_datetime)

            # Filter to only include data up to as_of_date (no future data)
            filtered_prices = [
                price for price in all_prices if price.date.date() <= as_of_date_only
            ]

            if not filtered_prices:
                logger.warning(f"No price data found for {ticker} up to {as_of_date_only}")
                context.data_available = False
                context.missing_data_warnings.append(
                    f"No price data available for {ticker} up to {as_of_date_only}"
                )
            else:
                # Check data completeness
                if len(filtered_prices) < lookback_days * 0.4:
                    # Less than 40% of expected trading days
                    warning = (
                        f"Sparse price data: only {len(filtered_prices)} days "
                        f"found (expected ~{lookback_days // 5} trading days)"
                    )
                    logger.warning(warning)
                    context.missing_data_warnings.append(warning)

                context.price_data = filtered_prices
                logger.debug(f"Fetched {len(filtered_prices)} price points for {ticker}")

        except Exception as e:
            logger.error(f"Error fetching price data for {ticker}: {e}")
            context.data_available = False
            context.missing_data_warnings.append(f"Price data fetch error: {str(e)}")

        # Fetch fundamentals (if supported)
        try:
            statements = self.provider.get_financial_statements(ticker)
            # Filter to only statements available before as_of_date
            filtered_statements = [
                stmt for stmt in statements if stmt.report_date.date() <= as_of_date_only
            ]
            context.fundamentals = filtered_statements
            if filtered_statements:
                logger.debug(
                    f"Fetched {len(filtered_statements)} financial statements for {ticker}"
                )
            else:
                context.missing_data_warnings.append(
                    f"No financial statements found for {ticker} before {as_of_date_only}"
                )
        except NotImplementedError:
            logger.debug(f"Provider {self.provider.name} does not support financial statements")
        except Exception as e:
            logger.warning(f"Error fetching financial statements for {ticker}: {e}")
            context.missing_data_warnings.append(f"Fundamentals fetch error: {str(e)}")

        # Fetch news (if supported)
        try:
            news_articles = self.provider.get_news(ticker)
            # Filter to only news published before as_of_date
            filtered_news = [
                article
                for article in news_articles
                if article.published_date.date() <= as_of_date_only
            ]
            context.news = filtered_news
            if filtered_news:
                logger.debug(f"Fetched {len(filtered_news)} news articles for {ticker}")
        except NotImplementedError:
            logger.debug(f"Provider {self.provider.name} does not support news fetching")
        except Exception as e:
            logger.warning(f"Error fetching news for {ticker}: {e}")
            context.missing_data_warnings.append(f"News fetch error: {str(e)}")

        # Fetch analyst ratings (if supported)
        try:
            rating = self.provider.get_analyst_ratings(ticker)
            # Filter to most recent rating before as_of_date
            if rating and rating.rating_date.date() <= as_of_date_only:
                context.analyst_ratings = rating
                logger.debug(f"Fetched analyst ratings for {ticker}")
        except NotImplementedError:
            logger.debug(f"Provider {self.provider.name} does not support analyst ratings")
        except Exception as e:
            logger.warning(f"Error fetching analyst ratings for {ticker}: {e}")

        # Fetch metadata (if supported)
        try:
            metadata = self.provider.get_instrument_metadata(ticker)
            context.metadata = metadata
            logger.debug(f"Fetched metadata for {ticker}")
        except NotImplementedError:
            logger.debug(f"Provider {self.provider.name} does not support metadata fetching")
        except Exception as e:
            logger.warning(f"Error fetching metadata for {ticker}: {e}")

        logger.debug(
            f"Historical context complete for {ticker}: "
            f"data_available={context.data_available}, "
            f"warnings={len(context.missing_data_warnings)}"
        )

        return context

    def validate_date(self, as_of_date: datetime) -> bool:
        """Validate that the given date is in the past.

        Args:
            as_of_date: Date to validate

        Returns:
            True if date is in the past, False otherwise
        """
        if as_of_date.date() > datetime.now().date():
            logger.warning(f"Historical analysis date {as_of_date} is in the future")
            return False
        return True
