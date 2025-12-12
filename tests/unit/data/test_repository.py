"""Unit tests for AnalystRatingsRepository."""

import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from src.data.models import AnalystData, AnalystRating
from src.data.repository import AnalystRatingsRepository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield db_path


@pytest.fixture
def repository(temp_db):
    """Create a repository instance with a temporary database."""
    return AnalystRatingsRepository(temp_db)


@pytest.fixture
def sample_rating():
    """Create a sample AnalystRating for testing."""
    return AnalystRating(
        ticker="AAPL",
        name="Apple Inc.",
        rating_date=datetime(2024, 6, 15, 12, 0, 0),
        rating="buy",
        price_target=200.0,
        num_analysts=25,
        consensus="buy",
    )


class TestAnalystRatingsRepository:
    """Test suite for AnalystRatingsRepository."""

    def test_repository_initialization(self, temp_db):
        """Test repository initialization."""
        repo = AnalystRatingsRepository(temp_db)
        assert repo.db_manager is not None
        assert repo.db_manager._initialized

    def test_store_ratings_new(self, repository, sample_rating):
        """Test storing a new analyst rating."""
        result = repository.store_ratings(sample_rating, data_source="Finnhub")
        assert result is True

    def test_store_ratings_multiple(self, repository, sample_rating):
        """Test storing multiple analyst ratings."""
        # Store initial rating
        assert repository.store_ratings(sample_rating, data_source="Finnhub")

        # Store same rating again (should update)
        assert repository.store_ratings(sample_rating, data_source="Finnhub")

        # Store for different month
        rating2 = AnalystRating(
            ticker="AAPL",
            name="Apple Inc.",
            rating_date=datetime(2024, 7, 15, 12, 0, 0),
            rating="hold",
            price_target=195.0,
            num_analysts=25,
            consensus="hold",
        )
        assert repository.store_ratings(rating2, data_source="Finnhub")

        # Store for different ticker
        rating3 = AnalystRating(
            ticker="MSFT",
            name="Microsoft Corporation",
            rating_date=datetime(2024, 6, 15, 12, 0, 0),
            rating="buy",
            price_target=450.0,
            num_analysts=30,
            consensus="buy",
        )
        assert repository.store_ratings(rating3, data_source="Finnhub")

    def test_get_ratings_existing(self, repository, sample_rating):
        """Test retrieving an existing rating."""
        repository.store_ratings(sample_rating, data_source="Finnhub")

        period = date(2024, 6, 1)
        retrieved = repository.get_ratings("AAPL", period)

        assert retrieved is not None
        assert retrieved.ticker == "AAPL"
        assert retrieved.num_analysts == 25

    def test_get_ratings_nonexistent(self, repository):
        """Test retrieving a non-existent rating."""
        period = date(2024, 6, 1)
        retrieved = repository.get_ratings("NONEXISTENT", period)
        assert retrieved is None

    def test_get_latest_ratings(self, repository):
        """Test retrieving the latest rating for a ticker."""
        # Store ratings for multiple months
        rating1 = AnalystRating(
            ticker="AAPL",
            name="Apple Inc.",
            rating_date=datetime(2024, 5, 15, 12, 0, 0),
            rating="hold",
            price_target=190.0,
            num_analysts=20,
            consensus="hold",
        )
        rating2 = AnalystRating(
            ticker="AAPL",
            name="Apple Inc.",
            rating_date=datetime(2024, 6, 15, 12, 0, 0),
            rating="buy",
            price_target=200.0,
            num_analysts=25,
            consensus="buy",
        )
        rating3 = AnalystRating(
            ticker="AAPL",
            name="Apple Inc.",
            rating_date=datetime(2024, 7, 15, 12, 0, 0),
            rating="strong_buy",
            price_target=210.0,
            num_analysts=25,
            consensus="strong_buy",
        )

        repository.store_ratings(rating1, data_source="Finnhub")
        repository.store_ratings(rating2, data_source="Finnhub")
        repository.store_ratings(rating3, data_source="Finnhub")

        latest = repository.get_latest_ratings("AAPL")

        assert latest is not None
        assert latest.num_analysts == 25
        # The latest should be from July (2024-07-01)
        assert latest.rating_date.month == 7

    def test_get_ratings_history(self, repository):
        """Test retrieving historical ratings over a date range."""
        # Store ratings for multiple months
        for month in range(1, 7):
            rating = AnalystRating(
                ticker="AAPL",
                name="Apple Inc.",
                rating_date=datetime(2024, month, 15, 12, 0, 0),
                rating="buy",
                price_target=180.0 + (month * 2),
                num_analysts=20 + month,
                consensus="buy",
            )
            repository.store_ratings(rating, data_source="Finnhub")

        # Get history from Feb to May
        history = repository.get_ratings_history("AAPL", date(2024, 2, 1), date(2024, 5, 1))

        assert len(history) == 4  # Feb, Mar, Apr, May
        assert history[0].rating_date.month == 2
        assert history[-1].rating_date.month == 5

    def test_get_ratings_history_empty(self, repository):
        """Test retrieving history with no matching records."""
        history = repository.get_ratings_history("NONEXISTENT", date(2024, 1, 1), date(2024, 12, 1))
        assert history == []

    def test_delete_ratings(self, repository, sample_rating):
        """Test deleting analyst ratings."""
        repository.store_ratings(sample_rating, data_source="Finnhub")

        period = date(2024, 6, 1)
        retrieved = repository.get_ratings("AAPL", period)
        assert retrieved is not None

        # Delete the rating
        result = repository.delete_ratings("AAPL", period)
        assert result is True

        # Verify deletion
        retrieved = repository.get_ratings("AAPL", period)
        assert retrieved is None

    def test_delete_ratings_nonexistent(self, repository):
        """Test deleting a non-existent rating."""
        result = repository.delete_ratings("NONEXISTENT", date(2024, 6, 1))
        assert result is False

    def test_get_all_tickers_with_data(self, repository):
        """Test retrieving all tickers with stored data."""
        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]

        for ticker in tickers:
            rating = AnalystRating(
                ticker=ticker,
                name=f"Company {ticker}",
                rating_date=datetime(2024, 6, 15, 12, 0, 0),
                rating="buy",
                price_target=100.0,
                num_analysts=20,
                consensus="buy",
            )
            repository.store_ratings(rating, data_source="Finnhub")

        all_tickers = repository.get_all_tickers_with_data()

        assert len(all_tickers) == 4
        for ticker in tickers:
            assert ticker in all_tickers

    def test_get_all_tickers_empty(self, repository):
        """Test getting tickers when database is empty."""
        tickers = repository.get_all_tickers_with_data()
        assert tickers == []

    def test_get_data_count(self, repository):
        """Test counting total records in database."""
        assert repository.get_data_count() == 0

        # Add some records
        for month in range(1, 4):
            rating = AnalystRating(
                ticker="AAPL",
                name="Apple Inc.",
                rating_date=datetime(2024, month, 15, 12, 0, 0),
                rating="buy",
                price_target=180.0,
                num_analysts=20,
                consensus="buy",
            )
            repository.store_ratings(rating, data_source="Finnhub")

        assert repository.get_data_count() == 3

    def test_upsert_behavior(self, repository, sample_rating):
        """Test that storing a rating twice updates the existing record."""
        # Store first time
        assert repository.store_ratings(sample_rating, data_source="Finnhub")
        initial_count = repository.get_data_count()

        # Store again with different data
        updated_rating = AnalystRating(
            ticker="AAPL",
            name="Apple Inc.",
            rating_date=datetime(2024, 6, 15, 12, 0, 0),
            rating="hold",
            price_target=190.0,
            num_analysts=28,
            consensus="hold",
        )
        assert repository.store_ratings(updated_rating, data_source="Finnhub")

        # Count should remain the same (upsert, not insert)
        assert repository.get_data_count() == initial_count

        # Verify the data was updated
        period = date(2024, 6, 1)
        retrieved = repository.get_ratings("AAPL", period)
        assert retrieved.num_analysts == 28

    def test_period_calculation(self):
        """Test period calculation helper method."""
        # Test with datetime
        dt = datetime(2024, 6, 15, 12, 30, 45)
        period = AnalystRatingsRepository._get_period_start(dt)
        assert period == date(2024, 6, 1)

        # Test with date
        d = date(2024, 6, 15)
        period = AnalystRatingsRepository._get_period_start(d)
        assert period == date(2024, 6, 1)

        # Test edge case: first day of month
        d = date(2024, 6, 1)
        period = AnalystRatingsRepository._get_period_start(d)
        assert period == date(2024, 6, 1)

        # Test edge case: last day of month
        d = date(2024, 6, 30)
        period = AnalystRatingsRepository._get_period_start(d)
        assert period == date(2024, 6, 1)

    def test_rating_parsing(self):
        """Test rating parsing helper method."""
        # Test strong_buy
        rating = AnalystRating(
            ticker="AAPL",
            name="Apple",
            rating_date=datetime.now(),
            rating="buy",
            num_analysts=10,
            consensus="strong_buy",
        )
        sb, b, h, s, ss = AnalystRatingsRepository._parse_ratings(rating)
        assert sb == 4  # 40% of 10
        assert b == 3  # 30% of 10
        assert h == 2  # 20% of 10

        # Test hold
        rating = AnalystRating(
            ticker="AAPL",
            name="Apple",
            rating_date=datetime.now(),
            rating="hold",
            num_analysts=10,
            consensus="hold",
        )
        sb, b, h, s, ss = AnalystRatingsRepository._parse_ratings(rating)
        assert h >= 3  # Centered on hold

    def test_analyst_data_to_rating_conversion(self):
        """Test conversion from AnalystData to AnalystRating."""
        from src.data.models import Ticker

        # Create a ticker first
        ticker = Ticker(symbol="AAPL", name="Apple Inc.", market="us", instrument_type="stock")

        analyst_data = AnalystData(
            ticker_id=1,  # Would be set by database
            ticker_obj=ticker,  # Relationship object
            period=date(2024, 6, 1),
            strong_buy=5,
            buy=8,
            hold=5,
            sell=2,
            strong_sell=0,
            total_analysts=20,
            data_source="Finnhub",
        )

        rating = analyst_data.to_analyst_rating()

        assert rating.ticker == "AAPL"
        assert rating.name == "Apple Inc."
        assert rating.num_analysts == 20
        assert rating.consensus == "buy"  # Most common rating

    def test_case_insensitive_ticker(self, repository):
        """Test that ticker handling is case-insensitive."""
        rating = AnalystRating(
            ticker="aapl",  # lowercase
            name="Apple Inc.",
            rating_date=datetime(2024, 6, 15, 12, 0, 0),
            rating="buy",
            price_target=200.0,
            num_analysts=25,
            consensus="buy",
        )

        repository.store_ratings(rating, data_source="Finnhub")

        # Retrieve with uppercase
        period = date(2024, 6, 1)
        retrieved = repository.get_ratings("AAPL", period)
        assert retrieved is not None

        # Retrieve with lowercase
        retrieved = repository.get_ratings("aapl", period)
        assert retrieved is not None

    def test_database_persistence(self):
        """Test that data persists across repository instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create first repository and store data
            repo1 = AnalystRatingsRepository(db_path)
            rating = AnalystRating(
                ticker="AAPL",
                name="Apple Inc.",
                rating_date=datetime(2024, 6, 15, 12, 0, 0),
                rating="buy",
                price_target=200.0,
                num_analysts=25,
                consensus="buy",
            )
            repo1.store_ratings(rating, data_source="Finnhub")

            # Create second repository and retrieve data
            repo2 = AnalystRatingsRepository(db_path)
            period = date(2024, 6, 1)
            retrieved = repo2.get_ratings("AAPL", period)

            assert retrieved is not None
            assert retrieved.ticker == "AAPL"
            assert retrieved.num_analysts == 25

    def test_multiple_data_sources(self, repository, sample_rating):
        """Test storing ratings from different data sources."""
        # Store same rating from different sources
        repository.store_ratings(sample_rating, data_source="Finnhub")
        repository.store_ratings(sample_rating, data_source="AlphaVantage")

        # Both should be in database (different source)
        assert repository.get_data_count() >= 2

    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"])
    def test_multiple_tickers(self, repository, ticker):
        """Test storing ratings for multiple tickers."""
        rating = AnalystRating(
            ticker=ticker,
            name=f"Company {ticker}",
            rating_date=datetime(2024, 6, 15, 12, 0, 0),
            rating="buy",
            price_target=100.0,
            num_analysts=20,
            consensus="buy",
        )
        assert repository.store_ratings(rating, data_source="Finnhub")

        period = date(2024, 6, 1)
        retrieved = repository.get_ratings(ticker, period)
        assert retrieved is not None
        assert retrieved.ticker == ticker


class TestAnalystDataModel:
    """Test suite for AnalystData SQLModel."""

    def test_analyst_data_creation(self):
        """Test creating an AnalystData instance."""
        from src.data.models import Ticker

        ticker = Ticker(symbol="AAPL", name="Apple Inc.", market="us", instrument_type="stock")

        data = AnalystData(
            ticker_id=1,  # Would be assigned by database
            ticker_obj=ticker,  # Relationship
            period=date(2024, 6, 1),
            strong_buy=5,
            buy=8,
            hold=5,
            sell=2,
            strong_sell=0,
            total_analysts=20,
            data_source="Finnhub",
        )

        assert data.ticker_id == 1
        assert data.ticker_obj.symbol == "AAPL"
        assert data.total_analysts == 20
        assert data.fetched_at is not None

    def test_analyst_data_consensus(self):
        """Test consensus calculation from AnalystData."""
        # Test strong_buy consensus
        data = AnalystData(
            ticker="AAPL",
            period=date(2024, 6, 1),
            strong_buy=10,
            buy=3,
            hold=2,
            sell=1,
            strong_sell=0,
            total_analysts=16,
            data_source="Finnhub",
        )

        rating = data.to_analyst_rating()
        assert rating.consensus == "strong_buy"

        # Test sell consensus
        data = AnalystData(
            ticker="AAPL",
            period=date(2024, 6, 1),
            strong_buy=1,
            buy=2,
            hold=3,
            sell=10,
            strong_sell=4,
            total_analysts=20,
            data_source="Finnhub",
        )

        rating = data.to_analyst_rating()
        assert rating.consensus == "sell"
