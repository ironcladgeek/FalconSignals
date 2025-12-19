"""Unit tests for the portfolio module."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.data.portfolio import PortfolioState, Position, WatchlistItem


class TestPosition:
    """Test suite for Position class."""

    @pytest.fixture
    def sample_position(self):
        """Create a sample position for testing."""
        return Position(
            ticker="AAPL",
            quantity=10.0,
            entry_price=150.0,
            entry_date=datetime(2024, 1, 15),
            metadata={"strategy": "value"},
        )

    def test_position_initialization(self, sample_position):
        """Test position initializes correctly."""
        assert sample_position.ticker == "AAPL"
        assert sample_position.quantity == 10.0
        assert sample_position.entry_price == 150.0
        assert sample_position.entry_date == datetime(2024, 1, 15)
        assert sample_position.metadata == {"strategy": "value"}

    def test_position_default_metadata(self):
        """Test position with default metadata."""
        pos = Position(
            ticker="MSFT",
            quantity=5.0,
            entry_price=300.0,
            entry_date=datetime(2024, 1, 1),
        )
        assert pos.metadata == {}

    def test_cost_basis(self, sample_position):
        """Test cost basis calculation."""
        assert sample_position.cost_basis() == 1500.0  # 10 * 150

    def test_current_value(self, sample_position):
        """Test current value calculation."""
        assert sample_position.current_value(160.0) == 1600.0  # 10 * 160

    def test_unrealized_pnl_profit(self, sample_position):
        """Test unrealized P&L calculation with profit."""
        pnl = sample_position.unrealized_pnl(160.0)
        assert pnl == 100.0  # (160 - 150) * 10

    def test_unrealized_pnl_loss(self, sample_position):
        """Test unrealized P&L calculation with loss."""
        pnl = sample_position.unrealized_pnl(140.0)
        assert pnl == -100.0  # (140 - 150) * 10

    def test_unrealized_return_profit(self, sample_position):
        """Test unrealized return percentage with profit."""
        ret = sample_position.unrealized_return(165.0)
        assert ret == 10.0  # (165 - 150) / 150 * 100 = 10%

    def test_unrealized_return_loss(self, sample_position):
        """Test unrealized return percentage with loss."""
        ret = sample_position.unrealized_return(135.0)
        assert ret == -10.0  # (135 - 150) / 150 * 100 = -10%

    def test_unrealized_return_zero_entry(self):
        """Test unrealized return with zero entry price."""
        pos = Position(
            ticker="TEST",
            quantity=10.0,
            entry_price=0.0,
            entry_date=datetime(2024, 1, 1),
        )
        assert pos.unrealized_return(100.0) == 0

    def test_to_dict(self, sample_position):
        """Test position serialization to dict."""
        data = sample_position.to_dict()

        assert data["ticker"] == "AAPL"
        assert data["quantity"] == 10.0
        assert data["entry_price"] == 150.0
        assert data["entry_date"] == "2024-01-15T00:00:00"
        assert data["metadata"] == {"strategy": "value"}

    def test_from_dict(self):
        """Test position deserialization from dict."""
        data = {
            "ticker": "GOOGL",
            "quantity": 5.0,
            "entry_price": 140.0,
            "entry_date": "2024-02-01T10:30:00",
            "metadata": {"note": "test"},
        }

        pos = Position.from_dict(data)

        assert pos.ticker == "GOOGL"
        assert pos.quantity == 5.0
        assert pos.entry_price == 140.0
        assert pos.entry_date == datetime(2024, 2, 1, 10, 30, 0)
        assert pos.metadata == {"note": "test"}

    def test_from_dict_without_metadata(self):
        """Test position deserialization without metadata."""
        data = {
            "ticker": "MSFT",
            "quantity": 3.0,
            "entry_price": 350.0,
            "entry_date": "2024-03-01T00:00:00",
        }

        pos = Position.from_dict(data)
        # When metadata is not provided, it defaults to empty dict
        assert pos.metadata == {}


class TestWatchlistItem:
    """Test suite for WatchlistItem class."""

    def test_watchlist_item_initialization(self):
        """Test watchlist item initializes correctly."""
        item = WatchlistItem(
            ticker="NVDA",
            notes="AI play",
            target_price=500.0,
            metadata={"priority": "high"},
        )

        assert item.ticker == "NVDA"
        assert item.notes == "AI play"
        assert item.target_price == 500.0
        assert item.added_date is not None
        assert item.metadata == {"priority": "high"}

    def test_watchlist_item_default_values(self):
        """Test watchlist item default values."""
        item = WatchlistItem(ticker="AMZN")

        assert item.ticker == "AMZN"
        assert item.notes is None
        assert item.target_price is None
        assert item.added_date is not None
        assert item.metadata == {}

    def test_watchlist_item_custom_date(self):
        """Test watchlist item with custom date."""
        custom_date = datetime(2024, 1, 1)
        item = WatchlistItem(ticker="TSLA", added_date=custom_date)

        assert item.added_date == custom_date

    def test_to_dict(self):
        """Test watchlist item serialization."""
        item = WatchlistItem(
            ticker="META",
            added_date=datetime(2024, 3, 15),
            notes="Reels growth",
            target_price=400.0,
        )

        data = item.to_dict()

        assert data["ticker"] == "META"
        assert data["added_date"] == "2024-03-15T00:00:00"
        assert data["notes"] == "Reels growth"
        assert data["target_price"] == 400.0

    def test_from_dict(self):
        """Test watchlist item deserialization."""
        data = {
            "ticker": "AMD",
            "added_date": "2024-04-01T12:00:00",
            "notes": "Chip stock",
            "target_price": 200.0,
            "metadata": {"sector": "tech"},
        }

        item = WatchlistItem.from_dict(data)

        assert item.ticker == "AMD"
        assert item.added_date == datetime(2024, 4, 1, 12, 0, 0)
        assert item.notes == "Chip stock"
        assert item.target_price == 200.0
        assert item.metadata == {"sector": "tech"}


class TestPortfolioState:
    """Test suite for PortfolioState class."""

    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_state.json"

    @pytest.fixture
    def portfolio(self, temp_state_file):
        """Create a portfolio instance with temp file."""
        return PortfolioState(temp_state_file)

    def test_portfolio_initialization(self, portfolio):
        """Test portfolio initializes correctly."""
        assert portfolio.positions == {}
        assert portfolio.watchlist == {}
        assert portfolio.last_updated is not None

    def test_add_position(self, portfolio):
        """Test adding a position."""
        portfolio.add_position(
            ticker="AAPL",
            quantity=10.0,
            entry_price=150.0,
            entry_date=datetime(2024, 1, 15),
        )

        assert "AAPL" in portfolio.positions
        assert portfolio.positions["AAPL"].quantity == 10.0
        assert portfolio.positions["AAPL"].entry_price == 150.0

    def test_add_position_default_date(self, portfolio):
        """Test adding a position with default date."""
        portfolio.add_position(ticker="MSFT", quantity=5.0, entry_price=300.0)

        assert "MSFT" in portfolio.positions
        assert portfolio.positions["MSFT"].entry_date is not None

    def test_add_position_updates_existing(self, portfolio):
        """Test that adding same ticker updates position."""
        portfolio.add_position(ticker="AAPL", quantity=10.0, entry_price=150.0)
        portfolio.add_position(ticker="AAPL", quantity=20.0, entry_price=160.0)

        assert portfolio.positions["AAPL"].quantity == 20.0
        assert portfolio.positions["AAPL"].entry_price == 160.0

    def test_remove_position_success(self, portfolio):
        """Test removing an existing position."""
        portfolio.add_position(ticker="AAPL", quantity=10.0, entry_price=150.0)

        result = portfolio.remove_position("AAPL")

        assert result is True
        assert "AAPL" not in portfolio.positions

    def test_remove_position_not_found(self, portfolio):
        """Test removing a non-existent position."""
        result = portfolio.remove_position("NONEXISTENT")
        assert result is False

    def test_get_position_exists(self, portfolio):
        """Test getting an existing position."""
        portfolio.add_position(ticker="AAPL", quantity=10.0, entry_price=150.0)

        pos = portfolio.get_position("AAPL")

        assert pos is not None
        assert pos.ticker == "AAPL"

    def test_get_position_not_found(self, portfolio):
        """Test getting a non-existent position."""
        pos = portfolio.get_position("NONEXISTENT")
        assert pos is None

    def test_add_to_watchlist(self, portfolio):
        """Test adding to watchlist."""
        portfolio.add_to_watchlist(
            ticker="NVDA",
            notes="AI leader",
            target_price=500.0,
        )

        assert "NVDA" in portfolio.watchlist
        assert portfolio.watchlist["NVDA"].notes == "AI leader"
        assert portfolio.watchlist["NVDA"].target_price == 500.0

    def test_remove_from_watchlist_success(self, portfolio):
        """Test removing from watchlist."""
        portfolio.add_to_watchlist(ticker="NVDA")

        result = portfolio.remove_from_watchlist("NVDA")

        assert result is True
        assert "NVDA" not in portfolio.watchlist

    def test_remove_from_watchlist_not_found(self, portfolio):
        """Test removing non-existent watchlist item."""
        result = portfolio.remove_from_watchlist("NONEXISTENT")
        assert result is False

    def test_get_watchlist_item_exists(self, portfolio):
        """Test getting existing watchlist item."""
        portfolio.add_to_watchlist(ticker="TSLA", notes="EV play")

        item = portfolio.get_watchlist_item("TSLA")

        assert item is not None
        assert item.ticker == "TSLA"
        assert item.notes == "EV play"

    def test_get_watchlist_item_not_found(self, portfolio):
        """Test getting non-existent watchlist item."""
        item = portfolio.get_watchlist_item("NONEXISTENT")
        assert item is None

    def test_portfolio_summary(self, portfolio):
        """Test portfolio summary calculation."""
        portfolio.add_position(ticker="AAPL", quantity=10.0, entry_price=150.0)
        portfolio.add_position(ticker="MSFT", quantity=5.0, entry_price=300.0)

        price_map = {"AAPL": 160.0, "MSFT": 320.0}
        summary = portfolio.portfolio_summary(price_map)

        assert summary["num_positions"] == 2
        assert summary["total_cost_basis"] == 3000.0  # 1500 + 1500
        assert summary["total_value"] == 3200.0  # 1600 + 1600
        assert summary["total_pnl"] == 200.0  # 100 + 100
        assert summary["total_return_pct"] == pytest.approx(6.67, rel=0.01)

    def test_portfolio_summary_missing_price(self, portfolio):
        """Test portfolio summary with missing price."""
        portfolio.add_position(ticker="AAPL", quantity=10.0, entry_price=150.0)

        price_map = {}  # No prices
        summary = portfolio.portfolio_summary(price_map)

        assert summary["total_value"] == 0.0
        assert summary["total_pnl"] == -1500.0

    def test_portfolio_summary_empty(self, portfolio):
        """Test portfolio summary with no positions."""
        summary = portfolio.portfolio_summary({})

        assert summary["num_positions"] == 0
        assert summary["total_cost_basis"] == 0.0
        assert summary["total_return_pct"] == 0

    def test_to_dict(self, portfolio):
        """Test portfolio state serialization."""
        portfolio.add_position(ticker="AAPL", quantity=10.0, entry_price=150.0)
        portfolio.add_to_watchlist(ticker="NVDA", notes="AI")

        data = portfolio.to_dict()

        assert "positions" in data
        assert "watchlist" in data
        assert "last_updated" in data
        assert "AAPL" in data["positions"]
        assert "NVDA" in data["watchlist"]

    def test_persistence(self, temp_state_file):
        """Test that state persists across instances."""
        # Create first portfolio and add data
        portfolio1 = PortfolioState(temp_state_file)
        portfolio1.add_position(ticker="AAPL", quantity=10.0, entry_price=150.0)
        portfolio1.add_to_watchlist(ticker="NVDA")

        # Create second portfolio instance
        portfolio2 = PortfolioState(temp_state_file)

        # Verify data persisted
        assert "AAPL" in portfolio2.positions
        assert portfolio2.positions["AAPL"].quantity == 10.0
        assert "NVDA" in portfolio2.watchlist

    def test_load_nonexistent_file(self, temp_state_file):
        """Test loading when file doesn't exist."""
        portfolio = PortfolioState(temp_state_file)

        assert portfolio.positions == {}
        assert portfolio.watchlist == {}

    def test_load_corrupted_file(self, temp_state_file):
        """Test loading corrupted JSON file."""
        # Create corrupted file
        temp_state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_state_file, "w") as f:
            f.write("not valid json {{{")

        # Should handle gracefully
        portfolio = PortfolioState(temp_state_file)

        assert portfolio.positions == {}
        assert portfolio.watchlist == {}

    def test_save_creates_directory(self):
        """Test that save creates parent directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "dir" / "state.json"
            portfolio = PortfolioState(nested_path)
            portfolio.add_position(ticker="AAPL", quantity=10.0, entry_price=150.0)

            # Should have created the file
            assert nested_path.exists()

    def test_last_updated_changes(self, portfolio):
        """Test that last_updated changes on modifications."""
        initial_time = portfolio.last_updated

        import time

        time.sleep(0.01)  # Small delay

        portfolio.add_position(ticker="AAPL", quantity=10.0, entry_price=150.0)

        assert portfolio.last_updated > initial_time
