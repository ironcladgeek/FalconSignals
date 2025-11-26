"""Data normalization and validation pipeline."""

import math
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from src.data.models import (
    FinancialStatement,
    InstrumentMetadata,
    InstrumentType,
    Market,
    NewsArticle,
    StockPrice,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DataNormalizer:
    """Normalize and clean financial data."""

    @staticmethod
    def normalize_stock_price(price: StockPrice) -> StockPrice:
        """Normalize stock price data.

        Handles:
        - NaN and infinite values
        - Negative prices (set to 0)
        - Zero volume replacement
        - Currency consistency

        Args:
            price: StockPrice to normalize

        Returns:
            Normalized StockPrice
        """
        # Replace NaN with 0 for prices
        open_price = (
            0
            if (math.isnan(price.open_price) or math.isinf(price.open_price))
            else max(0, price.open_price)
        )
        high_price = (
            0
            if (math.isnan(price.high_price) or math.isinf(price.high_price))
            else max(0, price.high_price)
        )
        low_price = (
            0
            if (math.isnan(price.low_price) or math.isinf(price.low_price))
            else max(0, price.low_price)
        )
        close_price = (
            0
            if (math.isnan(price.close_price) or math.isinf(price.close_price))
            else max(0, price.close_price)
        )
        adjusted_close = price.adjusted_close
        if adjusted_close is not None:
            adjusted_close = (
                0
                if (math.isnan(adjusted_close) or math.isinf(adjusted_close))
                else max(0, adjusted_close)
            )

        # Handle zero/nan volume
        volume = max(0, price.volume) if price.volume is not None else 0

        return StockPrice(
            ticker=price.ticker.upper(),
            name=price.name,
            market=price.market,
            instrument_type=price.instrument_type,
            date=price.date,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            adjusted_close=adjusted_close,
            currency=price.currency or "USD",
        )

    @staticmethod
    def normalize_financial_statement(
        statement: FinancialStatement,
    ) -> FinancialStatement:
        """Normalize financial statement data.

        Handles:
        - NaN and infinite values
        - Negative values handling
        - Unit consistency

        Args:
            statement: FinancialStatement to normalize

        Returns:
            Normalized FinancialStatement
        """
        value = statement.value
        if math.isnan(value) or math.isinf(value):
            value = 0

        return FinancialStatement(
            ticker=statement.ticker.upper(),
            name=statement.name,
            statement_type=statement.statement_type.lower(),
            fiscal_year=statement.fiscal_year,
            fiscal_quarter=statement.fiscal_quarter,
            report_date=statement.report_date,
            metric=statement.metric.lower(),
            value=value,
            unit=statement.unit or "USD",
        )

    @staticmethod
    def normalize_news_article(article: NewsArticle) -> NewsArticle:
        """Normalize news article data.

        Handles:
        - Empty or None fields
        - Sentiment score bounds

        Args:
            article: NewsArticle to normalize

        Returns:
            Normalized NewsArticle
        """
        sentiment_score = article.sentiment_score
        if sentiment_score is not None:
            # Clamp sentiment score to [-1, 1]
            sentiment_score = max(-1, min(1, sentiment_score))

        importance = article.importance
        if importance is not None:
            # Clamp importance to [0, 100]
            importance = max(0, min(100, importance))

        return NewsArticle(
            ticker=article.ticker.upper(),
            title=article.title or "",
            summary=article.summary,
            source=article.source or "Unknown",
            url=article.url or "",
            published_date=article.published_date,
            sentiment=article.sentiment.lower() if article.sentiment else None,
            sentiment_score=sentiment_score,
            importance=importance,
        )

    @staticmethod
    def normalize_metadata(
        metadata: InstrumentMetadata,
    ) -> InstrumentMetadata:
        """Normalize instrument metadata.

        Handles:
        - Empty fields
        - Case normalization

        Args:
            metadata: InstrumentMetadata to normalize

        Returns:
            Normalized InstrumentMetadata
        """
        return InstrumentMetadata(
            ticker=metadata.ticker.upper(),
            name=metadata.name or metadata.ticker,
            market=metadata.market,
            instrument_type=metadata.instrument_type,
            sector=metadata.sector.lower() if metadata.sector else None,
            industry=metadata.industry.lower() if metadata.industry else None,
            currency=metadata.currency or "USD",
            last_updated=metadata.last_updated,
        )


class DataValidator:
    """Validate financial data quality."""

    @staticmethod
    def validate_stock_price(price: StockPrice) -> bool:
        """Validate stock price data.

        Checks:
        - Price consistency (high >= low >= close >= 0)
        - Volume is non-negative
        - Date is reasonable

        Args:
            price: StockPrice to validate

        Returns:
            True if valid, False otherwise
        """
        # Check price ordering
        if not (price.high_price >= price.close_price >= price.low_price >= 0):
            logger.warning(
                f"Invalid price ordering for {price.ticker}: "
                f"H={price.high_price} C={price.close_price} L={price.low_price}"
            )
            return False

        # Check volume
        if price.volume < 0:
            logger.warning(f"Negative volume for {price.ticker}: {price.volume}")
            return False

        # Check date (reasonable range: last 50 years)
        cutoff = datetime.now().replace(year=datetime.now().year - 50)
        if price.date < cutoff:
            logger.warning(f"Date out of range for {price.ticker}: {price.date}")
            return False

        return True

    @staticmethod
    def validate_news_article(article: NewsArticle) -> bool:
        """Validate news article data.

        Checks:
        - Required fields not empty
        - Sentiment score in valid range
        - Date is reasonable

        Args:
            article: NewsArticle to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not article.title or not article.url:
            logger.warning(f"Missing required fields in news article for {article.ticker}")
            return False

        # Check sentiment score
        if article.sentiment_score is not None:
            if not (-1 <= article.sentiment_score <= 1):
                logger.warning(
                    f"Invalid sentiment score for {article.ticker}: {article.sentiment_score}"
                )
                return False

        # Check date (reasonable range: last 30 days)
        cutoff = datetime.now().replace(
            year=datetime.now().year,
            month=max(1, datetime.now().month - 1),
        )
        if article.published_date < cutoff:
            logger.debug(f"Old news article for {article.ticker}: {article.published_date}")

        return True

    @staticmethod
    def validate_financial_statement(statement: FinancialStatement) -> bool:
        """Validate financial statement data.

        Checks:
        - Fiscal year is reasonable
        - Fiscal quarter is valid (1-4)
        - Report date is reasonable

        Args:
            statement: FinancialStatement to validate

        Returns:
            True if valid, False otherwise
        """
        # Check fiscal year (reasonable range)
        current_year = datetime.now().year
        if not (1990 <= statement.fiscal_year <= current_year + 1):
            logger.warning(f"Invalid fiscal year for {statement.ticker}: {statement.fiscal_year}")
            return False

        # Check fiscal quarter
        if statement.fiscal_quarter is not None:
            if not (1 <= statement.fiscal_quarter <= 4):
                logger.warning(
                    f"Invalid fiscal quarter for {statement.ticker}: {statement.fiscal_quarter}"
                )
                return False

        # Check report date
        if statement.report_date > datetime.now():
            logger.warning(f"Future report date for {statement.ticker}: {statement.report_date}")
            return False

        return True


class DataProcessor:
    """Process and clean data collections."""

    @staticmethod
    def normalize_prices(
        prices: list[StockPrice],
    ) -> list[StockPrice]:
        """Normalize list of prices.

        Args:
            prices: List of StockPrice objects

        Returns:
            List of normalized StockPrice objects
        """
        normalized = []
        for price in prices:
            try:
                normalized_price = DataNormalizer.normalize_stock_price(price)
                if DataValidator.validate_stock_price(normalized_price):
                    normalized.append(normalized_price)
                else:
                    logger.warning(f"Skipping invalid price: {price.ticker}")
            except Exception as e:
                logger.error(f"Error normalizing price {price.ticker}: {e}")

        logger.info(f"Normalized {len(prices)} to {len(normalized)} valid prices")
        return normalized

    @staticmethod
    def calculate_returns(
        prices: list[StockPrice],
        periods: list[int] = None,
    ) -> dict[str, dict[str, float]]:
        """Calculate returns for price data.

        Args:
            prices: List of StockPrice objects sorted by date
            periods: List of periods in days (e.g., [1, 7, 30])

        Returns:
            Dictionary with returns by ticker and period
        """
        if periods is None:
            periods = [1, 7, 30]

        returns = {}

        if not prices or len(prices) < 2:
            return returns

        # Group by ticker
        by_ticker = {}
        for price in prices:
            if price.ticker not in by_ticker:
                by_ticker[price.ticker] = []
            by_ticker[price.ticker].append(price)

        # Calculate returns
        for ticker, ticker_prices in by_ticker.items():
            ticker_prices.sort(key=lambda p: p.date)
            current_price = ticker_prices[-1].close_price

            returns[ticker] = {}
            for period in periods:
                # Find price from period days ago
                target_date = ticker_prices[-1].date.replace(
                    day=max(1, ticker_prices[-1].day - period)
                )
                matching = [p for p in ticker_prices if p.date <= target_date]

                if matching:
                    past_price = matching[-1].close_price
                    if past_price > 0:
                        return_pct = (current_price - past_price) / past_price * 100
                        returns[ticker][f"{period}d"] = round(return_pct, 2)

        return returns
