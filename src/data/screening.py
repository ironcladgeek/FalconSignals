"""Instrument screening and filtering module."""

from dataclasses import dataclass

from src.data.models import InstrumentMetadata, InstrumentType, Market, StockPrice
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScreeningCriteria:
    """Criteria for instrument screening."""

    markets: list[Market] = None
    instrument_types: list[InstrumentType] = None
    exclude_penny_stocks: bool = True
    min_price: float = 1.0
    min_volume_usd: float = 1_000_000
    exclude_tickers: list[str] = None

    def __post_init__(self):
        """Set defaults."""
        if self.markets is None:
            self.markets = [Market.NORDIC, Market.EU, Market.US]
        if self.instrument_types is None:
            self.instrument_types = [InstrumentType.STOCK, InstrumentType.ETF]
        if self.exclude_tickers is None:
            self.exclude_tickers = []


class InstrumentScreener:
    """Screen and filter financial instruments."""

    @staticmethod
    def screen_price(
        price: StockPrice,
        criteria: ScreeningCriteria,
    ) -> bool:
        """Check if stock price meets screening criteria.

        Args:
            price: StockPrice to evaluate
            criteria: ScreeningCriteria for filtering

        Returns:
            True if passes screening, False otherwise
        """
        # Check market
        if price.market not in criteria.markets:
            return False

        # Check instrument type
        if price.instrument_type not in criteria.instrument_types:
            return False

        # Check excluded tickers
        if price.ticker in criteria.exclude_tickers:
            return False

        # Check penny stock filter
        if criteria.exclude_penny_stocks and price.close_price < criteria.min_price:
            logger.debug(
                f"Filtered {price.ticker}: price {price.close_price} < {criteria.min_price}"
            )
            return False

        # Check minimum volume
        volume_usd = price.close_price * price.volume
        if volume_usd < criteria.min_volume_usd:
            logger.debug(
                f"Filtered {price.ticker}: volume ${volume_usd:,.0f} "
                f"< ${criteria.min_volume_usd:,.0f}"
            )
            return False

        return True

    @staticmethod
    def screen_instrument(
        instrument: InstrumentMetadata,
        criteria: ScreeningCriteria,
    ) -> bool:
        """Check if instrument metadata meets screening criteria.

        Args:
            instrument: InstrumentMetadata to evaluate
            criteria: ScreeningCriteria for filtering

        Returns:
            True if passes screening, False otherwise
        """
        # Check market
        if instrument.market not in criteria.markets:
            return False

        # Check instrument type
        if instrument.instrument_type not in criteria.instrument_types:
            return False

        # Check excluded tickers
        if instrument.ticker in criteria.exclude_tickers:
            return False

        return True

    @staticmethod
    def filter_prices(
        prices: list[StockPrice],
        criteria: ScreeningCriteria,
    ) -> list[StockPrice]:
        """Filter list of stock prices.

        Args:
            prices: List of StockPrice objects
            criteria: ScreeningCriteria for filtering

        Returns:
            Filtered list of StockPrice objects
        """
        filtered = []
        for price in prices:
            if InstrumentScreener.screen_price(price, criteria):
                filtered.append(price)

        logger.debug(f"Filtered {len(prices)} prices to {len(filtered)} instruments")
        return filtered

    @staticmethod
    def filter_instruments(
        instruments: list[InstrumentMetadata],
        criteria: ScreeningCriteria,
    ) -> list[InstrumentMetadata]:
        """Filter list of instruments.

        Args:
            instruments: List of InstrumentMetadata objects
            criteria: ScreeningCriteria for filtering

        Returns:
            Filtered list of InstrumentMetadata objects
        """
        filtered = []
        for instrument in instruments:
            if InstrumentScreener.screen_instrument(instrument, criteria):
                filtered.append(instrument)

        logger.debug(
            f"Filtered {len(instruments)} instruments to {len(filtered)} matching criteria"
        )
        return filtered

    @staticmethod
    def get_unique_tickers(prices: list[StockPrice]) -> list[str]:
        """Get unique tickers from prices.

        Args:
            prices: List of StockPrice objects

        Returns:
            List of unique tickers
        """
        return list(dict.fromkeys(p.ticker for p in prices))
