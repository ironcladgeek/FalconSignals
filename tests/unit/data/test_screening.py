"""Unit tests for the screening module."""

from datetime import datetime

import pytest

from src.data.models import InstrumentMetadata, InstrumentType, Market, StockPrice
from src.data.screening import InstrumentScreener, ScreeningCriteria


def make_stock_price(
    ticker: str,
    name: str,
    close_price: float,
    volume: int,
    market: Market = Market.US,
    instrument_type: InstrumentType = InstrumentType.STOCK,
) -> StockPrice:
    """Helper to create StockPrice with required fields."""
    return StockPrice(
        ticker=ticker,
        name=name,
        close_price=close_price,
        volume=volume,
        market=market,
        instrument_type=instrument_type,
        date=datetime(2024, 1, 15),
        open_price=close_price * 0.99,
        high_price=close_price * 1.01,
        low_price=close_price * 0.98,
    )


class TestScreeningCriteria:
    """Test suite for ScreeningCriteria dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        criteria = ScreeningCriteria()

        assert criteria.markets == [Market.NORDIC, Market.EU, Market.US]
        assert criteria.instrument_types == [InstrumentType.STOCK, InstrumentType.ETF]
        assert criteria.exclude_penny_stocks is True
        assert criteria.min_price == 1.0
        assert criteria.min_volume_usd == 1_000_000
        assert criteria.exclude_tickers == []

    def test_custom_values(self):
        """Test custom values are accepted."""
        criteria = ScreeningCriteria(
            markets=[Market.US],
            instrument_types=[InstrumentType.STOCK],
            exclude_penny_stocks=False,
            min_price=5.0,
            min_volume_usd=500_000,
            exclude_tickers=["AAPL", "MSFT"],
        )

        assert criteria.markets == [Market.US]
        assert criteria.instrument_types == [InstrumentType.STOCK]
        assert criteria.exclude_penny_stocks is False
        assert criteria.min_price == 5.0
        assert criteria.min_volume_usd == 500_000
        assert criteria.exclude_tickers == ["AAPL", "MSFT"]

    def test_partial_custom_values(self):
        """Test partial custom values with defaults for others."""
        criteria = ScreeningCriteria(markets=[Market.US], min_price=10.0)

        assert criteria.markets == [Market.US]
        assert criteria.instrument_types == [InstrumentType.STOCK, InstrumentType.ETF]
        assert criteria.min_price == 10.0
        assert criteria.exclude_tickers == []


class TestInstrumentScreener:
    """Test suite for InstrumentScreener class."""

    @pytest.fixture
    def default_criteria(self):
        """Create default screening criteria."""
        return ScreeningCriteria()

    @pytest.fixture
    def sample_stock_price(self):
        """Create a sample StockPrice for testing."""
        return make_stock_price(
            ticker="AAPL",
            name="Apple Inc.",
            close_price=150.0,
            volume=10_000_000,
            market=Market.US,
            instrument_type=InstrumentType.STOCK,
        )

    @pytest.fixture
    def sample_instrument(self):
        """Create a sample InstrumentMetadata for testing."""
        return InstrumentMetadata(
            ticker="AAPL",
            name="Apple Inc.",
            market=Market.US,
            instrument_type=InstrumentType.STOCK,
            last_updated=datetime(2024, 1, 15),
        )

    def test_screen_price_passes(self, default_criteria, sample_stock_price):
        """Test that valid stock passes screening."""
        result = InstrumentScreener.screen_price(sample_stock_price, default_criteria)
        assert result is True

    def test_screen_price_fails_market(self, default_criteria, sample_stock_price):
        """Test filtering by market."""
        criteria = ScreeningCriteria(markets=[Market.EU])
        result = InstrumentScreener.screen_price(sample_stock_price, criteria)
        assert result is False

    def test_screen_price_fails_instrument_type(self, default_criteria, sample_stock_price):
        """Test filtering by instrument type."""
        criteria = ScreeningCriteria(instrument_types=[InstrumentType.ETF])
        result = InstrumentScreener.screen_price(sample_stock_price, criteria)
        assert result is False

    def test_screen_price_fails_excluded_ticker(self, default_criteria, sample_stock_price):
        """Test filtering by excluded tickers."""
        criteria = ScreeningCriteria(exclude_tickers=["AAPL"])
        result = InstrumentScreener.screen_price(sample_stock_price, criteria)
        assert result is False

    def test_screen_price_fails_penny_stock(self, default_criteria):
        """Test filtering penny stocks."""
        penny_stock = make_stock_price(
            ticker="PENNY",
            name="Penny Stock Inc.",
            close_price=0.50,
            volume=100_000_000,
            market=Market.US,
            instrument_type=InstrumentType.STOCK,
        )
        result = InstrumentScreener.screen_price(penny_stock, default_criteria)
        assert result is False

    def test_screen_price_passes_penny_stock_disabled(self):
        """Test penny stock passes when filter disabled."""
        criteria = ScreeningCriteria(exclude_penny_stocks=False)
        penny_stock = make_stock_price(
            ticker="PENNY",
            name="Penny Stock Inc.",
            close_price=0.50,
            volume=100_000_000,
            market=Market.US,
            instrument_type=InstrumentType.STOCK,
        )
        result = InstrumentScreener.screen_price(penny_stock, criteria)
        assert result is True

    def test_screen_price_fails_low_volume(self, default_criteria):
        """Test filtering low volume stocks."""
        low_volume_stock = make_stock_price(
            ticker="LOW",
            name="Low Volume Inc.",
            close_price=100.0,
            volume=1_000,
            market=Market.US,
            instrument_type=InstrumentType.STOCK,
        )
        result = InstrumentScreener.screen_price(low_volume_stock, default_criteria)
        assert result is False

    def test_screen_price_passes_high_volume(self, default_criteria):
        """Test high volume stock passes."""
        high_volume_stock = make_stock_price(
            ticker="HIGH",
            name="High Volume Inc.",
            close_price=10.0,
            volume=200_000,
            market=Market.US,
            instrument_type=InstrumentType.STOCK,
        )
        result = InstrumentScreener.screen_price(high_volume_stock, default_criteria)
        assert result is True

    def test_screen_instrument_passes(self, default_criteria, sample_instrument):
        """Test that valid instrument passes screening."""
        result = InstrumentScreener.screen_instrument(sample_instrument, default_criteria)
        assert result is True

    def test_screen_instrument_fails_market(self, sample_instrument):
        """Test filtering instrument by market."""
        criteria = ScreeningCriteria(markets=[Market.NORDIC])
        result = InstrumentScreener.screen_instrument(sample_instrument, criteria)
        assert result is False

    def test_screen_instrument_fails_type(self, sample_instrument):
        """Test filtering instrument by type."""
        criteria = ScreeningCriteria(instrument_types=[InstrumentType.ETF])
        result = InstrumentScreener.screen_instrument(sample_instrument, criteria)
        assert result is False

    def test_screen_instrument_fails_excluded(self, sample_instrument):
        """Test filtering instrument by excluded ticker."""
        criteria = ScreeningCriteria(exclude_tickers=["AAPL"])
        result = InstrumentScreener.screen_instrument(sample_instrument, criteria)
        assert result is False

    def test_filter_prices(self, default_criteria):
        """Test filtering list of prices."""
        prices = [
            make_stock_price(
                ticker="GOOD1",
                name="Good Stock 1",
                close_price=100.0,
                volume=50_000,
                market=Market.US,
                instrument_type=InstrumentType.STOCK,
            ),
            make_stock_price(
                ticker="BAD",
                name="Bad Stock",
                close_price=0.50,
                volume=100_000,
                market=Market.US,
                instrument_type=InstrumentType.STOCK,
            ),
            make_stock_price(
                ticker="GOOD2",
                name="Good Stock 2",
                close_price=200.0,
                volume=10_000,
                market=Market.US,
                instrument_type=InstrumentType.STOCK,
            ),
        ]

        filtered = InstrumentScreener.filter_prices(prices, default_criteria)

        assert len(filtered) == 2
        assert all(p.ticker.startswith("GOOD") for p in filtered)

    def test_filter_prices_empty_list(self, default_criteria):
        """Test filtering empty list."""
        filtered = InstrumentScreener.filter_prices([], default_criteria)
        assert filtered == []

    def test_filter_instruments(self):
        """Test filtering list of instruments by market."""
        # Create US-only criteria to test filtering
        us_only_criteria = ScreeningCriteria(
            markets=[Market.US],
            instrument_types=[InstrumentType.STOCK, InstrumentType.ETF],
        )

        instruments = [
            InstrumentMetadata(
                ticker="US1",
                name="US Stock 1",
                market=Market.US,
                instrument_type=InstrumentType.STOCK,
                last_updated=datetime(2024, 1, 15),
            ),
            InstrumentMetadata(
                ticker="EU1",
                name="European Stock",
                market=Market.EU,
                instrument_type=InstrumentType.STOCK,
                last_updated=datetime(2024, 1, 15),
            ),
            InstrumentMetadata(
                ticker="US2",
                name="US Stock 2",
                market=Market.US,
                instrument_type=InstrumentType.ETF,
                last_updated=datetime(2024, 1, 15),
            ),
        ]

        filtered = InstrumentScreener.filter_instruments(instruments, us_only_criteria)

        assert len(filtered) == 2
        tickers = [i.ticker for i in filtered]
        assert "US1" in tickers
        assert "US2" in tickers
        assert "EU1" not in tickers

    def test_filter_instruments_empty_list(self, default_criteria):
        """Test filtering empty instruments list."""
        filtered = InstrumentScreener.filter_instruments([], default_criteria)
        assert filtered == []

    def test_get_unique_tickers(self):
        """Test getting unique tickers from prices."""
        prices = [
            make_stock_price(ticker="AAPL", name="Apple", close_price=150.0, volume=100),
            make_stock_price(ticker="MSFT", name="Microsoft", close_price=300.0, volume=100),
            make_stock_price(ticker="AAPL", name="Apple", close_price=151.0, volume=100),
        ]

        unique = InstrumentScreener.get_unique_tickers(prices)

        assert len(unique) == 2
        assert "AAPL" in unique
        assert "MSFT" in unique

    def test_get_unique_tickers_empty(self):
        """Test getting unique tickers from empty list."""
        unique = InstrumentScreener.get_unique_tickers([])
        assert unique == []

    def test_get_unique_tickers_preserves_order(self):
        """Test that unique tickers preserves first occurrence order."""
        prices = [
            make_stock_price(ticker="AAPL", name="Apple", close_price=150.0, volume=100),
            make_stock_price(ticker="MSFT", name="Microsoft", close_price=300.0, volume=100),
            make_stock_price(ticker="GOOGL", name="Google", close_price=140.0, volume=100),
        ]

        unique = InstrumentScreener.get_unique_tickers(prices)

        assert unique == ["AAPL", "MSFT", "GOOGL"]
