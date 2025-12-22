"""Unit tests for TradingJournalRepository."""

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from src.data.repository import TradingJournalRepository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_trading_journal.db"
        yield db_path


@pytest.fixture
def journal_repo(temp_db):
    """Create a TradingJournalRepository instance with a temporary database."""
    return TradingJournalRepository(temp_db)


class TestTradingJournalRepository:
    """Test suite for TradingJournalRepository."""

    def test_repository_initialization(self, temp_db):
        """Test repository initialization."""
        repo = TradingJournalRepository(temp_db)
        assert repo.db_manager is not None
        assert repo.db_manager._initialized

    def test_create_trade_success(self, journal_repo):
        """Test creating a new trade successfully."""
        entry_date = date.today()
        success, message, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=entry_date,
            entry_price=150.0,
            position_size=10,
            position_type="long",
            fees_entry=5.0,
            stop_loss=140.0,
            take_profit=165.0,
            description="First test trade",
        )

        assert success is True
        assert "Trade created successfully" in message
        assert trade_id is not None
        assert isinstance(trade_id, int)

    def test_create_trade_invalid_position_type(self, journal_repo):
        """Test creating a trade with invalid position type."""
        success, message, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
            position_type="sideways",  # Invalid
        )

        assert success is False
        assert "Invalid position type" in message
        assert trade_id is None

    def test_create_trade_invalid_entry_price(self, journal_repo):
        """Test creating a trade with invalid entry price."""
        success, message, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=-150.0,  # Invalid
            position_size=10,
        )

        assert success is False
        assert "Entry price must be positive" in message
        assert trade_id is None

    def test_create_trade_invalid_position_size(self, journal_repo):
        """Test creating a trade with invalid position size."""
        success, message, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=0,  # Invalid
        )

        assert success is False
        assert "Position size must be positive" in message
        assert trade_id is None

    def test_create_trade_negative_fees(self, journal_repo):
        """Test creating a trade with negative fees."""
        success, message, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
            fees_entry=-5.0,  # Invalid
        )

        assert success is False
        assert "Entry fees cannot be negative" in message
        assert trade_id is None

    def test_create_trade_short_position(self, journal_repo):
        """Test creating a short position."""
        success, message, trade_id = journal_repo.create_trade(
            ticker_symbol="TSLA",
            entry_date=date.today(),
            entry_price=200.0,
            position_size=5,
            position_type="short",
            fees_entry=3.0,
        )

        assert success is True
        assert trade_id is not None

        # Verify the trade details
        trade = journal_repo.get_trade_by_id(trade_id)
        assert trade is not None
        assert trade["position_type"] == "short"
        assert trade["ticker_symbol"] == "TSLA"

    def test_create_trade_calculates_total_entry_amount(self, journal_repo):
        """Test that total_entry_amount is calculated correctly."""
        entry_price = 150.0
        position_size = 10
        fees_entry = 5.0
        expected_total = (entry_price * position_size) + fees_entry

        success, message, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=entry_price,
            position_size=position_size,
            fees_entry=fees_entry,
        )

        assert success is True

        trade = journal_repo.get_trade_by_id(trade_id)
        assert trade["total_entry_amount"] == expected_total

    def test_update_trade_stop_loss(self, journal_repo):
        """Test updating stop loss for an open trade."""
        # Create trade
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
            stop_loss=140.0,
        )
        assert success is True

        # Update stop loss
        success, message = journal_repo.update_trade(trade_id, stop_loss=145.0)
        assert success is True
        assert "updated successfully" in message

        # Verify update
        trade = journal_repo.get_trade_by_id(trade_id)
        assert trade["stop_loss"] == 145.0

    def test_update_trade_take_profit(self, journal_repo):
        """Test updating take profit for an open trade."""
        # Create trade
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
            take_profit=165.0,
        )
        assert success is True

        # Update take profit
        success, message = journal_repo.update_trade(trade_id, take_profit=170.0)
        assert success is True

        # Verify update
        trade = journal_repo.get_trade_by_id(trade_id)
        assert trade["take_profit"] == 170.0

    def test_update_trade_description(self, journal_repo):
        """Test updating description for an open trade."""
        # Create trade
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
            description="Original description",
        )
        assert success is True

        # Update description
        new_description = "Updated description with more details"
        success, message = journal_repo.update_trade(trade_id, description=new_description)
        assert success is True

        # Verify update
        trade = journal_repo.get_trade_by_id(trade_id)
        assert trade["description"] == new_description

    def test_update_trade_nonexistent(self, journal_repo):
        """Test updating a non-existent trade."""
        success, message = journal_repo.update_trade(999, stop_loss=100.0)
        assert success is False
        assert "not found" in message

    def test_update_trade_closed(self, journal_repo):
        """Test that updating a closed trade fails."""
        # Create and close trade
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today() - timedelta(days=5),
            entry_price=150.0,
            position_size=10,
        )
        assert success is True

        success, _, _ = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=160.0,
        )
        assert success is True

        # Try to update closed trade
        success, message = journal_repo.update_trade(trade_id, stop_loss=140.0)
        assert success is False
        assert "Cannot update closed trade" in message

    def test_close_trade_long_position_profit(self, journal_repo):
        """Test closing a long position with profit."""
        # Create trade
        entry_price = 150.0
        position_size = 10
        fees_entry = 5.0
        exit_price = 160.0
        fees_exit = 5.0

        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today() - timedelta(days=5),
            entry_price=entry_price,
            position_size=position_size,
            fees_entry=fees_entry,
        )
        assert success is True

        # Close trade
        success, message, profit_loss = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=exit_price,
            fees_exit=fees_exit,
        )

        assert success is True
        assert profit_loss is not None
        assert profit_loss > 0  # Should be profitable

        # Verify calculations
        expected_profit = (exit_price * position_size - fees_exit) - (
            entry_price * position_size + fees_entry
        )
        assert profit_loss == pytest.approx(expected_profit)

        # Verify trade status
        trade = journal_repo.get_trade_by_id(trade_id)
        assert trade["status"] == "closed"
        assert trade["profit_loss"] == pytest.approx(expected_profit)

    def test_close_trade_long_position_loss(self, journal_repo):
        """Test closing a long position with loss."""
        # Create trade
        entry_price = 150.0
        position_size = 10
        fees_entry = 5.0
        exit_price = 140.0
        fees_exit = 5.0

        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today() - timedelta(days=5),
            entry_price=entry_price,
            position_size=position_size,
            fees_entry=fees_entry,
        )
        assert success is True

        # Close trade
        success, message, profit_loss = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=exit_price,
            fees_exit=fees_exit,
        )

        assert success is True
        assert profit_loss is not None
        assert profit_loss < 0  # Should be a loss

    def test_close_trade_short_position_profit(self, journal_repo):
        """Test closing a short position with profit."""
        # Create short trade
        entry_price = 150.0
        position_size = 10
        fees_entry = 5.0
        exit_price = 140.0  # Price went down, profit for short
        fees_exit = 5.0

        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="TSLA",
            entry_date=date.today() - timedelta(days=5),
            entry_price=entry_price,
            position_size=position_size,
            position_type="short",
            fees_entry=fees_entry,
        )
        assert success is True

        # Close trade
        success, message, profit_loss = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=exit_price,
            fees_exit=fees_exit,
        )

        assert success is True
        assert profit_loss is not None
        assert profit_loss > 0  # Should be profitable for short

    def test_close_trade_short_position_loss(self, journal_repo):
        """Test closing a short position with loss."""
        # Create short trade
        entry_price = 150.0
        position_size = 10
        fees_entry = 5.0
        exit_price = 160.0  # Price went up, loss for short
        fees_exit = 5.0

        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="TSLA",
            entry_date=date.today() - timedelta(days=5),
            entry_price=entry_price,
            position_size=position_size,
            position_type="short",
            fees_entry=fees_entry,
        )
        assert success is True

        # Close trade
        success, message, profit_loss = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=exit_price,
            fees_exit=fees_exit,
        )

        assert success is True
        assert profit_loss is not None
        assert profit_loss < 0  # Should be a loss for short

    def test_close_trade_invalid_exit_price(self, journal_repo):
        """Test closing a trade with invalid exit price."""
        # Create trade
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today() - timedelta(days=5),
            entry_price=150.0,
            position_size=10,
        )
        assert success is True

        # Try to close with invalid price
        success, message, profit_loss = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=-160.0,  # Invalid
        )

        assert success is False
        assert "Exit price must be positive" in message
        assert profit_loss is None

    def test_close_trade_negative_fees(self, journal_repo):
        """Test closing a trade with negative fees."""
        # Create trade
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today() - timedelta(days=5),
            entry_price=150.0,
            position_size=10,
        )
        assert success is True

        # Try to close with negative fees
        success, message, profit_loss = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=160.0,
            fees_exit=-5.0,  # Invalid
        )

        assert success is False
        assert "Exit fees cannot be negative" in message
        assert profit_loss is None

    def test_close_trade_nonexistent(self, journal_repo):
        """Test closing a non-existent trade."""
        success, message, profit_loss = journal_repo.close_trade(
            trade_id=999,
            exit_date=date.today(),
            exit_price=160.0,
        )

        assert success is False
        assert "not found" in message
        assert profit_loss is None

    def test_close_trade_already_closed(self, journal_repo):
        """Test closing an already closed trade."""
        # Create and close trade
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today() - timedelta(days=5),
            entry_price=150.0,
            position_size=10,
        )
        assert success is True

        # Close first time
        success, _, _ = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=160.0,
        )
        assert success is True

        # Try to close again
        success, message, profit_loss = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=165.0,
        )

        assert success is False
        assert "already closed" in message
        assert profit_loss is None

    def test_get_open_trades(self, journal_repo):
        """Test getting all open trades."""
        # Create multiple trades
        journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
        )
        journal_repo.create_trade(
            ticker_symbol="MSFT",
            entry_date=date.today(),
            entry_price=300.0,
            position_size=5,
        )
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="GOOGL",
            entry_date=date.today() - timedelta(days=5),
            entry_price=120.0,
            position_size=8,
        )

        # Close one trade
        journal_repo.close_trade(trade_id=trade_id, exit_date=date.today(), exit_price=125.0)

        # Get open trades
        open_trades = journal_repo.get_open_trades()
        assert len(open_trades) == 2
        assert all(trade["status"] == "open" for trade in open_trades)
        assert {trade["ticker_symbol"] for trade in open_trades} == {"AAPL", "MSFT"}

    def test_get_open_trades_filtered_by_ticker(self, journal_repo):
        """Test getting open trades filtered by ticker."""
        # Create multiple trades
        journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
        )
        journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today() - timedelta(days=1),
            entry_price=148.0,
            position_size=5,
        )
        journal_repo.create_trade(
            ticker_symbol="MSFT",
            entry_date=date.today(),
            entry_price=300.0,
            position_size=5,
        )

        # Get open trades for AAPL
        open_trades = journal_repo.get_open_trades(ticker_symbol="AAPL")
        assert len(open_trades) == 2
        assert all(trade["ticker_symbol"] == "AAPL" for trade in open_trades)

    def test_get_open_trades_empty(self, journal_repo):
        """Test getting open trades when there are none."""
        open_trades = journal_repo.get_open_trades()
        assert len(open_trades) == 0

    def test_get_closed_trades(self, journal_repo):
        """Test getting all closed trades."""
        # Create and close multiple trades
        for i in range(3):
            success, _, trade_id = journal_repo.create_trade(
                ticker_symbol=f"STOCK{i}",
                entry_date=date.today() - timedelta(days=10 - i),
                entry_price=100.0 + i * 10,
                position_size=10,
            )
            journal_repo.close_trade(
                trade_id=trade_id,
                exit_date=date.today() - timedelta(days=5 - i),
                exit_price=110.0 + i * 10,
            )

        # Create one open trade
        journal_repo.create_trade(
            ticker_symbol="OPEN",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
        )

        # Get closed trades
        closed_trades = journal_repo.get_closed_trades()
        assert len(closed_trades) == 3
        assert all(trade["status"] == "closed" for trade in closed_trades)

    def test_get_closed_trades_filtered_by_ticker(self, journal_repo):
        """Test getting closed trades filtered by ticker."""
        # Create and close trades for different tickers
        for ticker in ["AAPL", "AAPL", "MSFT"]:
            success, _, trade_id = journal_repo.create_trade(
                ticker_symbol=ticker,
                entry_date=date.today() - timedelta(days=5),
                entry_price=150.0,
                position_size=10,
            )
            journal_repo.close_trade(
                trade_id=trade_id,
                exit_date=date.today(),
                exit_price=160.0,
            )

        # Get closed trades for AAPL
        closed_trades = journal_repo.get_closed_trades(ticker_symbol="AAPL")
        assert len(closed_trades) == 2
        assert all(trade["ticker_symbol"] == "AAPL" for trade in closed_trades)

    def test_get_closed_trades_filtered_by_date_range(self, journal_repo):
        """Test getting closed trades filtered by date range."""
        # Create and close trades on different dates
        for i in range(5):
            success, _, trade_id = journal_repo.create_trade(
                ticker_symbol="AAPL",
                entry_date=date.today() - timedelta(days=10),
                entry_price=150.0,
                position_size=10,
            )
            journal_repo.close_trade(
                trade_id=trade_id,
                exit_date=date.today() - timedelta(days=i),
                exit_price=160.0,
            )

        # Get trades closed in last 3 days
        start_date = date.today() - timedelta(days=3)
        closed_trades = journal_repo.get_closed_trades(start_date=start_date)
        assert len(closed_trades) == 4  # Days 0, 1, 2, 3

    def test_get_closed_trades_empty(self, journal_repo):
        """Test getting closed trades when there are none."""
        # Create only open trades
        journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
        )

        closed_trades = journal_repo.get_closed_trades()
        assert len(closed_trades) == 0

    def test_get_trade_by_id_exists(self, journal_repo):
        """Test getting a trade by ID when it exists."""
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
            description="Test trade",
        )
        assert success is True

        trade = journal_repo.get_trade_by_id(trade_id)
        assert trade is not None
        assert trade["id"] == trade_id
        assert trade["ticker_symbol"] == "AAPL"
        assert trade["entry_price"] == 150.0
        assert trade["description"] == "Test trade"

    def test_get_trade_by_id_not_exists(self, journal_repo):
        """Test getting a trade by ID when it doesn't exist."""
        trade = journal_repo.get_trade_by_id(999)
        assert trade is None

    def test_get_trade_history(self, journal_repo):
        """Test getting trade history for a ticker."""
        # Create multiple trades for same ticker
        for i in range(5):
            success, _, trade_id = journal_repo.create_trade(
                ticker_symbol="AAPL",
                entry_date=date.today() - timedelta(days=i),
                entry_price=150.0 + i,
                position_size=10,
            )
            if i < 3:  # Close first 3
                journal_repo.close_trade(
                    trade_id=trade_id,
                    exit_date=date.today(),
                    exit_price=160.0,
                )

        # Get trade history
        history = journal_repo.get_trade_history("AAPL")
        assert len(history) == 5
        assert history[0]["ticker_symbol"] == "AAPL"

    def test_get_trade_history_with_limit(self, journal_repo):
        """Test getting trade history with limit."""
        # Create many trades
        for i in range(10):
            journal_repo.create_trade(
                ticker_symbol="AAPL",
                entry_date=date.today() - timedelta(days=i),
                entry_price=150.0,
                position_size=10,
            )

        # Get limited history
        history = journal_repo.get_trade_history("AAPL", limit=5)
        assert len(history) == 5

    def test_get_trade_history_empty(self, journal_repo):
        """Test getting trade history for ticker with no trades."""
        history = journal_repo.get_trade_history("NONEXISTENT")
        assert len(history) == 0

    def test_get_performance_summary_all_trades(self, journal_repo):
        """Test getting performance summary for all closed trades."""
        # Create and close trades with different outcomes
        trades_data = [
            (150.0, 160.0),  # Profit
            (150.0, 140.0),  # Loss
            (150.0, 165.0),  # Profit
        ]

        for entry_price, exit_price in trades_data:
            success, _, trade_id = journal_repo.create_trade(
                ticker_symbol="AAPL",
                entry_date=date.today() - timedelta(days=5),
                entry_price=entry_price,
                position_size=10,
                fees_entry=5.0,
            )
            journal_repo.close_trade(
                trade_id=trade_id,
                exit_date=date.today(),
                exit_price=exit_price,
                fees_exit=5.0,
            )

        # Get summary
        summary = journal_repo.get_performance_summary()
        assert summary["total_trades"] == 3
        assert summary["winning_trades"] == 2
        assert summary["losing_trades"] == 1
        assert summary["win_rate"] == pytest.approx(66.67, rel=0.01)
        assert summary["total_profit_loss"] != 0
        assert "avg_profit_loss" in summary
        assert "total_fees" in summary

    def test_get_performance_summary_filtered_by_ticker(self, journal_repo):
        """Test getting performance summary filtered by ticker."""
        # Create trades for different tickers
        for ticker in ["AAPL", "MSFT"]:
            success, _, trade_id = journal_repo.create_trade(
                ticker_symbol=ticker,
                entry_date=date.today() - timedelta(days=5),
                entry_price=150.0,
                position_size=10,
            )
            journal_repo.close_trade(
                trade_id=trade_id,
                exit_date=date.today(),
                exit_price=160.0,
            )

        # Get summary for AAPL only
        summary = journal_repo.get_performance_summary(ticker_symbol="AAPL")
        assert summary["total_trades"] == 1

    def test_get_performance_summary_no_trades(self, journal_repo):
        """Test getting performance summary when there are no closed trades."""
        summary = journal_repo.get_performance_summary()
        assert summary["total_trades"] == 0
        assert summary["total_profit_loss"] == 0.0
        assert summary["win_rate"] == 0.0

    def test_case_insensitive_ticker_handling(self, journal_repo):
        """Test that ticker symbols are handled case-insensitively."""
        # Create trade with lowercase
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="aapl",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
        )
        assert success is True

        # Query with uppercase
        trades = journal_repo.get_open_trades(ticker_symbol="AAPL")
        assert len(trades) == 1
        assert trades[0]["ticker_symbol"] == "AAPL"

    def test_multiple_open_trades_same_ticker(self, journal_repo):
        """Test creating multiple open trades for the same ticker."""
        # Create multiple open positions
        for i in range(3):
            success, _, _ = journal_repo.create_trade(
                ticker_symbol="AAPL",
                entry_date=date.today() - timedelta(days=i),
                entry_price=150.0 + i,
                position_size=10,
            )
            assert success is True

        # Verify all are tracked
        open_trades = journal_repo.get_open_trades(ticker_symbol="AAPL")
        assert len(open_trades) == 3

    def test_profit_loss_percentage_calculation(self, journal_repo):
        """Test that profit/loss percentage is calculated correctly."""
        entry_price = 100.0
        position_size = 10
        fees_entry = 5.0
        exit_price = 110.0
        fees_exit = 5.0

        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today() - timedelta(days=5),
            entry_price=entry_price,
            position_size=position_size,
            fees_entry=fees_entry,
        )
        assert success is True

        success, _, profit_loss = journal_repo.close_trade(
            trade_id=trade_id,
            exit_date=date.today(),
            exit_price=exit_price,
            fees_exit=fees_exit,
        )
        assert success is True

        # Verify percentage calculation
        trade = journal_repo.get_trade_by_id(trade_id)
        total_entry = (entry_price * position_size) + fees_entry
        expected_pct = (profit_loss / total_entry) * 100
        assert trade["profit_loss_pct"] == pytest.approx(expected_pct, rel=0.01)

    def test_trade_with_recommendation_link(self, journal_repo):
        """Test creating a trade linked to a recommendation."""
        success, _, trade_id = journal_repo.create_trade(
            ticker_symbol="AAPL",
            entry_date=date.today(),
            entry_price=150.0,
            position_size=10,
            recommendation_id=42,
        )
        assert success is True

        trade = journal_repo.get_trade_by_id(trade_id)
        assert trade["recommendation_id"] == 42
