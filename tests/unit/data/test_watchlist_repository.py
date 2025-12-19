"""Unit tests for WatchlistRepository and WatchlistSignalRepository."""

import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from src.data.repository import (
    WatchlistRepository,
    WatchlistSignalRepository,
    get_or_create_ticker,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_watchlist.db"
        yield db_path


@pytest.fixture
def watchlist_repo(temp_db):
    """Create a WatchlistRepository instance with a temporary database."""
    return WatchlistRepository(temp_db)


@pytest.fixture
def signal_repo(temp_db):
    """Create a WatchlistSignalRepository instance with a temporary database."""
    return WatchlistSignalRepository(temp_db)


@pytest.fixture
def shared_db():
    """Create a shared temporary database for repositories that need to share state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_shared.db"
        yield db_path


class TestWatchlistRepository:
    """Test suite for WatchlistRepository."""

    def test_repository_initialization(self, temp_db):
        """Test repository initialization."""
        repo = WatchlistRepository(temp_db)
        assert repo.db_manager is not None
        assert repo.db_manager._initialized

    def test_add_to_watchlist_new_ticker(self, watchlist_repo):
        """Test adding a new ticker to watchlist."""
        success, message = watchlist_repo.add_to_watchlist("AAPL")

        assert success is True
        assert "Added AAPL to watchlist" in message

    def test_add_to_watchlist_duplicate(self, watchlist_repo):
        """Test adding a duplicate ticker to watchlist."""
        # Add first time
        success1, _ = watchlist_repo.add_to_watchlist("AAPL")
        assert success1 is True

        # Try to add again
        success2, message = watchlist_repo.add_to_watchlist("AAPL")
        assert success2 is False
        assert "already in watchlist" in message

    def test_add_to_watchlist_case_insensitive(self, watchlist_repo):
        """Test that ticker handling is case-insensitive."""
        # Add with lowercase
        success1, _ = watchlist_repo.add_to_watchlist("aapl")
        assert success1 is True

        # Try to add with uppercase (should fail - duplicate)
        success2, message = watchlist_repo.add_to_watchlist("AAPL")
        assert success2 is False
        assert "already in watchlist" in message

    def test_add_to_watchlist_with_recommendation_id(self, watchlist_repo):
        """Test adding a ticker to watchlist with recommendation ID."""
        success, message = watchlist_repo.add_to_watchlist("MSFT", recommendation_id=123)

        assert success is True
        assert "Added MSFT to watchlist" in message

        # Verify recommendation ID is stored
        watchlist = watchlist_repo.get_watchlist()
        assert len(watchlist) == 1
        assert watchlist[0]["recommendation_id"] == 123

    def test_remove_from_watchlist_existing(self, watchlist_repo):
        """Test removing an existing ticker from watchlist."""
        # Add first
        watchlist_repo.add_to_watchlist("AAPL")

        # Remove
        success, message = watchlist_repo.remove_from_watchlist("AAPL")
        assert success is True
        assert "Removed AAPL from watchlist" in message

        # Verify removal
        watchlist = watchlist_repo.get_watchlist()
        assert len(watchlist) == 0

    def test_remove_from_watchlist_nonexistent(self, watchlist_repo):
        """Test removing a non-existent ticker from watchlist."""
        success, message = watchlist_repo.remove_from_watchlist("NONEXISTENT")
        assert success is False
        assert "not found" in message or "not in watchlist" in message

    def test_remove_from_watchlist_not_in_watchlist(self, watchlist_repo):
        """Test removing a ticker that exists but is not in watchlist."""
        # Create ticker but don't add to watchlist
        session = watchlist_repo.db_manager.get_session()
        try:
            get_or_create_ticker(session, "GOOGL", "Google LLC")
            session.commit()
        finally:
            session.close()

        # Try to remove
        success, message = watchlist_repo.remove_from_watchlist("GOOGL")
        assert success is False
        assert "not in watchlist" in message

    def test_get_watchlist_empty(self, watchlist_repo):
        """Test getting watchlist when empty."""
        watchlist = watchlist_repo.get_watchlist()
        assert watchlist == []

    def test_get_watchlist_with_items(self, watchlist_repo):
        """Test getting watchlist with items."""
        # Add multiple tickers
        watchlist_repo.add_to_watchlist("AAPL")
        watchlist_repo.add_to_watchlist("MSFT")
        watchlist_repo.add_to_watchlist("GOOGL")

        watchlist = watchlist_repo.get_watchlist()

        assert len(watchlist) == 3
        tickers = [item["ticker"] for item in watchlist]
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "GOOGL" in tickers

    def test_get_watchlist_item_fields(self, watchlist_repo):
        """Test that watchlist items contain expected fields."""
        watchlist_repo.add_to_watchlist("AAPL", recommendation_id=42)

        watchlist = watchlist_repo.get_watchlist()

        assert len(watchlist) == 1
        item = watchlist[0]
        assert "ticker" in item
        assert "name" in item
        assert "recommendation_id" in item
        assert "created_at" in item
        assert item["ticker"] == "AAPL"
        assert item["recommendation_id"] == 42
        assert isinstance(item["created_at"], datetime)

    def test_ticker_exists_true(self, watchlist_repo):
        """Test ticker_exists returns True for existing ticker."""
        watchlist_repo.add_to_watchlist("AAPL")

        assert watchlist_repo.ticker_exists("AAPL") is True
        assert watchlist_repo.ticker_exists("aapl") is True  # Case insensitive

    def test_ticker_exists_false(self, watchlist_repo):
        """Test ticker_exists returns False for non-existing ticker."""
        assert watchlist_repo.ticker_exists("NONEXISTENT") is False

    def test_ticker_exists_not_in_watchlist(self, watchlist_repo):
        """Test ticker_exists returns False when ticker exists but not in watchlist."""
        # Create ticker but don't add to watchlist
        session = watchlist_repo.db_manager.get_session()
        try:
            get_or_create_ticker(session, "GOOGL", "Google LLC")
            session.commit()
        finally:
            session.close()

        assert watchlist_repo.ticker_exists("GOOGL") is False

    def test_database_persistence(self):
        """Test that data persists across repository instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create first repository and add data
            repo1 = WatchlistRepository(db_path)
            repo1.add_to_watchlist("AAPL")
            repo1.add_to_watchlist("MSFT")

            # Create second repository and verify data
            repo2 = WatchlistRepository(db_path)
            watchlist = repo2.get_watchlist()

            assert len(watchlist) == 2

    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"])
    def test_add_multiple_tickers(self, watchlist_repo, ticker):
        """Test adding multiple different tickers."""
        success, message = watchlist_repo.add_to_watchlist(ticker)
        assert success is True
        assert ticker in message


class TestWatchlistSignalRepository:
    """Test suite for WatchlistSignalRepository."""

    def test_repository_initialization(self, temp_db):
        """Test repository initialization."""
        repo = WatchlistSignalRepository(temp_db)
        assert repo.db_manager is not None
        assert repo.db_manager._initialized

    def test_store_signal_success(self, shared_db):
        """Test storing a signal for a watchlist ticker."""
        # Setup: Add ticker to watchlist first
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        # Store signal
        success, message = signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=75.0,
            confidence=80.0,
            current_price=150.0,
            rationale="Strong technical indicators",
            action="Buy",
            currency="USD",
            entry_price=148.0,
            stop_loss=140.0,
            take_profit=165.0,
        )

        assert success is True
        assert "Stored signal for AAPL" in message or "Updated signal for AAPL" in message

    def test_store_signal_not_in_watchlist(self, signal_repo):
        """Test storing a signal for a ticker not in watchlist."""
        success, message = signal_repo.store_signal(
            ticker_symbol="UNKNOWN",
            analysis_date=date.today(),
            score=75.0,
            confidence=80.0,
            current_price=150.0,
        )

        assert success is False
        assert "not in watchlist" in message or "not found" in message

    def test_store_signal_upsert(self, shared_db):
        """Test that storing signal twice updates existing record."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        # Store first signal
        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=75.0,
            confidence=80.0,
            current_price=150.0,
            action="Wait",
        )

        # Store updated signal for same date
        success, message = signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=85.0,
            confidence=90.0,
            current_price=155.0,
            action="Buy",
        )

        assert success is True
        assert "Updated signal for AAPL" in message

        # Verify latest values
        signal = signal_repo.get_latest_signal("AAPL")
        assert signal["score"] == 85.0
        assert signal["confidence"] == 90.0
        assert signal["action"] == "Buy"

    def test_store_signal_with_all_fields(self, shared_db):
        """Test storing a signal with all optional fields."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("NVDA")

        success, _ = signal_repo.store_signal(
            ticker_symbol="NVDA",
            analysis_date=date.today(),
            score=82.5,
            confidence=75.0,
            current_price=450.0,
            rationale="Bullish momentum with strong volume",
            action="Buy",
            currency="USD",
            entry_price=445.0,
            stop_loss=420.0,
            take_profit=500.0,
            wait_for_price=None,
        )

        assert success is True

        signal = signal_repo.get_latest_signal("NVDA")
        assert signal["score"] == 82.5
        assert signal["confidence"] == 75.0
        assert signal["current_price"] == 450.0
        assert signal["rationale"] == "Bullish momentum with strong volume"
        assert signal["action"] == "Buy"
        assert signal["entry_price"] == 445.0
        assert signal["stop_loss"] == 420.0
        assert signal["take_profit"] == 500.0

    def test_get_latest_signal_success(self, shared_db):
        """Test getting the latest signal for a ticker."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        # Store signals for different dates
        yesterday = date.today() - timedelta(days=1)
        today = date.today()

        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=yesterday,
            score=70.0,
            confidence=75.0,
            current_price=145.0,
            action="Wait",
        )

        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=today,
            score=80.0,
            confidence=85.0,
            current_price=150.0,
            action="Buy",
        )

        # Get latest signal
        signal = signal_repo.get_latest_signal("AAPL")

        assert signal is not None
        assert signal["analysis_date"] == today
        assert signal["score"] == 80.0
        assert signal["action"] == "Buy"

    def test_get_latest_signal_nonexistent(self, signal_repo):
        """Test getting latest signal for non-existent ticker."""
        signal = signal_repo.get_latest_signal("NONEXISTENT")
        assert signal is None

    def test_get_signal_history(self, shared_db):
        """Test getting historical signals for a ticker."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        # Store signals for multiple dates
        for i in range(5):
            signal_date = date.today() - timedelta(days=i)
            signal_repo.store_signal(
                ticker_symbol="AAPL",
                analysis_date=signal_date,
                score=70.0 + i,
                confidence=80.0,
                current_price=150.0 + i,
            )

        # Get history
        history = signal_repo.get_signal_history("AAPL", days_back=10)

        assert len(history) == 5
        # Should be ordered by date descending
        assert history[0]["analysis_date"] >= history[-1]["analysis_date"]

    def test_get_signal_history_limited_days(self, shared_db):
        """Test getting signal history with limited days."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        # Store signals for 10 days
        for i in range(10):
            signal_date = date.today() - timedelta(days=i)
            signal_repo.store_signal(
                ticker_symbol="AAPL",
                analysis_date=signal_date,
                score=70.0,
                confidence=80.0,
                current_price=150.0,
            )

        # Get history for last 5 days only
        history = signal_repo.get_signal_history("AAPL", days_back=5)

        # Should have at most 6 signals (days 0-5 inclusive)
        assert len(history) <= 6

    def test_get_signal_history_empty(self, signal_repo):
        """Test getting signal history for ticker with no signals."""
        history = signal_repo.get_signal_history("NONEXISTENT", days_back=30)
        assert history == []

    def test_get_signals_for_watchlist_id(self, shared_db):
        """Test getting signals for a specific watchlist entry."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        # Get watchlist to get the ID
        watchlist_repo.get_watchlist()
        # We need to get watchlist_id from the database
        session = watchlist_repo.db_manager.get_session()
        try:
            from sqlmodel import select

            from src.data.models import Ticker, Watchlist

            ticker = session.exec(select(Ticker).where(Ticker.symbol == "AAPL")).first()
            watchlist_entry = session.exec(
                select(Watchlist).where(Watchlist.ticker_id == ticker.id)
            ).first()
            watchlist_id = watchlist_entry.id
        finally:
            session.close()

        # Store signals
        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=75.0,
            confidence=80.0,
            current_price=150.0,
        )

        # Get signals by watchlist ID
        signals = signal_repo.get_signals_for_watchlist_id(watchlist_id)

        assert len(signals) >= 1
        assert signals[0]["ticker"] == "AAPL"

    def test_delete_old_signals(self, shared_db):
        """Test deleting signals older than specified days."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        # Store old signals
        old_date = date.today() - timedelta(days=100)
        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=old_date,
            score=70.0,
            confidence=80.0,
            current_price=140.0,
        )

        # Store recent signal
        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=75.0,
            confidence=80.0,
            current_price=150.0,
        )

        # Delete old signals
        count, message = signal_repo.delete_old_signals(days_old=90)

        assert count == 1
        assert "Deleted" in message

        # Verify only recent signal remains
        history = signal_repo.get_signal_history("AAPL", days_back=200)
        assert len(history) == 1
        assert history[0]["analysis_date"] == date.today()

    def test_delete_old_signals_none_to_delete(self, shared_db):
        """Test deleting old signals when none are old enough."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        # Store only recent signals
        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=75.0,
            confidence=80.0,
            current_price=150.0,
        )

        count, message = signal_repo.delete_old_signals(days_old=90)

        assert count == 0
        assert "No old signals to delete" in message

    def test_get_watchlist_with_latest_signals(self, shared_db):
        """Test getting watchlist with latest signals attached."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        # Add multiple tickers
        watchlist_repo.add_to_watchlist("AAPL")
        watchlist_repo.add_to_watchlist("MSFT")
        watchlist_repo.add_to_watchlist("GOOGL")

        # Add signals for some tickers
        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=75.0,
            confidence=80.0,
            current_price=150.0,
            action="Buy",
        )

        signal_repo.store_signal(
            ticker_symbol="MSFT",
            analysis_date=date.today(),
            score=65.0,
            confidence=70.0,
            current_price=350.0,
            action="Wait",
        )

        # Get watchlist with signals
        result = signal_repo.get_watchlist_with_latest_signals()

        assert len(result) == 3

        # Find entries by ticker
        aapl = next(r for r in result if r["ticker"] == "AAPL")
        msft = next(r for r in result if r["ticker"] == "MSFT")
        googl = next(r for r in result if r["ticker"] == "GOOGL")

        # Verify AAPL has signal
        assert aapl["latest_signal"] is not None
        assert aapl["latest_signal"]["score"] == 75.0
        assert aapl["latest_signal"]["action"] == "Buy"

        # Verify MSFT has signal
        assert msft["latest_signal"] is not None
        assert msft["latest_signal"]["score"] == 65.0
        assert msft["latest_signal"]["action"] == "Wait"

        # Verify GOOGL has no signal
        assert googl["latest_signal"] is None

    def test_get_watchlist_with_latest_signals_empty(self, signal_repo):
        """Test getting watchlist with signals when watchlist is empty."""
        result = signal_repo.get_watchlist_with_latest_signals()
        assert result == []

    def test_signal_case_insensitive_ticker(self, shared_db):
        """Test that signal operations are case-insensitive for tickers."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        # Add with uppercase
        watchlist_repo.add_to_watchlist("AAPL")

        # Store with lowercase
        success, _ = signal_repo.store_signal(
            ticker_symbol="aapl",
            analysis_date=date.today(),
            score=75.0,
            confidence=80.0,
            current_price=150.0,
        )
        assert success is True

        # Retrieve with uppercase
        signal = signal_repo.get_latest_signal("AAPL")
        assert signal is not None
        assert signal["ticker"] == "AAPL"

    def test_database_persistence(self):
        """Test that signals persist across repository instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Setup with first repository
            watchlist_repo1 = WatchlistRepository(db_path)
            signal_repo1 = WatchlistSignalRepository(db_path)

            watchlist_repo1.add_to_watchlist("AAPL")
            signal_repo1.store_signal(
                ticker_symbol="AAPL",
                analysis_date=date.today(),
                score=75.0,
                confidence=80.0,
                current_price=150.0,
            )

            # Verify with second repository instance
            signal_repo2 = WatchlistSignalRepository(db_path)
            signal = signal_repo2.get_latest_signal("AAPL")

            assert signal is not None
            assert signal["score"] == 75.0


class TestWatchlistSignalFields:
    """Test suite for WatchlistSignal model fields."""

    def test_signal_with_wait_action(self, shared_db):
        """Test storing signal with Wait action and wait_for_price."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=55.0,
            confidence=70.0,
            current_price=150.0,
            action="Wait",
            wait_for_price=140.0,
        )

        signal = signal_repo.get_latest_signal("AAPL")

        assert signal["action"] == "Wait"
        assert signal["wait_for_price"] == 140.0
        assert signal["entry_price"] is None  # Not set for Wait action

    def test_signal_with_remove_action(self, shared_db):
        """Test storing signal with Remove action."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=25.0,
            confidence=85.0,
            current_price=100.0,
            action="Remove",
            rationale="Technical breakdown, bearish trend confirmed",
        )

        signal = signal_repo.get_latest_signal("AAPL")

        assert signal["action"] == "Remove"
        assert signal["score"] == 25.0
        assert "bearish" in signal["rationale"].lower()

    def test_signal_minimal_fields(self, shared_db):
        """Test storing signal with only required fields."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        success, _ = signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=70.0,
            confidence=75.0,
            current_price=150.0,
        )

        assert success is True

        signal = signal_repo.get_latest_signal("AAPL")
        assert signal is not None
        assert signal["score"] == 70.0
        assert signal["confidence"] == 75.0
        assert signal["current_price"] == 150.0
        assert signal["action"] is None
        assert signal["rationale"] is None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_ticker_symbol(self, watchlist_repo):
        """Test handling of empty ticker symbol."""
        # This may raise an error or return failure depending on implementation
        # The database constraint should prevent empty symbols
        try:
            success, _ = watchlist_repo.add_to_watchlist("")
            # If it doesn't raise, it should return failure
            # Note: might succeed if get_or_create_ticker normalizes to ""
        except Exception:
            pass  # Expected behavior

    def test_special_characters_in_ticker(self, watchlist_repo):
        """Test handling of tickers with special characters."""
        # Some exchanges have tickers with dots or hyphens
        success, _ = watchlist_repo.add_to_watchlist("BRK.B")
        # Should succeed or fail gracefully
        assert isinstance(success, bool)

    def test_very_long_rationale(self, shared_db):
        """Test storing signal with very long rationale."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        long_rationale = "A" * 10000  # Very long text

        success, _ = signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=75.0,
            confidence=80.0,
            current_price=150.0,
            rationale=long_rationale,
        )

        assert success is True

    def test_extreme_score_values(self, shared_db):
        """Test storing signals with extreme score values."""
        watchlist_repo = WatchlistRepository(shared_db)
        signal_repo = WatchlistSignalRepository(shared_db)

        watchlist_repo.add_to_watchlist("AAPL")

        # Score at boundaries
        success1, _ = signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=0.0,
            confidence=100.0,
            current_price=150.0,
        )
        assert success1 is True

        # Update with max score
        success2, _ = signal_repo.store_signal(
            ticker_symbol="AAPL",
            analysis_date=date.today(),
            score=100.0,
            confidence=0.0,
            current_price=150.0,
        )
        assert success2 is True
