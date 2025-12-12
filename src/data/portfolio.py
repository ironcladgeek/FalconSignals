"""Portfolio state management and watchlist persistence."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class Position:
    """Represents a portfolio position."""

    def __init__(
        self,
        ticker: str,
        quantity: float,
        entry_price: float,
        entry_date: datetime,
        metadata: dict[str, Any] = None,
    ):
        """Initialize position.

        Args:
            ticker: Stock ticker symbol
            quantity: Number of shares/units
            entry_price: Entry price
            entry_date: Entry date
            metadata: Additional position metadata
        """
        self.ticker = ticker
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.metadata = metadata or {}

    def cost_basis(self) -> float:
        """Calculate cost basis.

        Returns:
            Total cost (quantity * entry_price)
        """
        return self.quantity * self.entry_price

    def current_value(self, current_price: float) -> float:
        """Calculate current value.

        Args:
            current_price: Current price per unit

        Returns:
            Total current value
        """
        return self.quantity * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L.

        Args:
            current_price: Current price per unit

        Returns:
            Unrealized profit/loss
        """
        return self.current_value(current_price) - self.cost_basis()

    def unrealized_return(self, current_price: float) -> float:
        """Calculate unrealized return percentage.

        Args:
            current_price: Current price per unit

        Returns:
            Unrealized return as percentage
        """
        if self.entry_price == 0:
            return 0
        return (current_price - self.entry_price) / self.entry_price * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Position as dictionary
        """
        return {
            "ticker": self.ticker,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "entry_date": self.entry_date.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Position":
        """Create position from dictionary.

        Args:
            data: Position dictionary

        Returns:
            Position instance
        """
        return cls(
            ticker=data["ticker"],
            quantity=data["quantity"],
            entry_price=data["entry_price"],
            entry_date=datetime.fromisoformat(data["entry_date"]),
            metadata=data.get("metadata"),
        )


class WatchlistItem:
    """Represents a watchlist item."""

    def __init__(
        self,
        ticker: str,
        added_date: datetime = None,
        notes: str = None,
        target_price: float = None,
        metadata: dict[str, Any] = None,
    ):
        """Initialize watchlist item.

        Args:
            ticker: Stock ticker symbol
            added_date: Date added to watchlist
            notes: Personal notes about the item
            target_price: Target price
            metadata: Additional metadata
        """
        self.ticker = ticker
        self.added_date = added_date or datetime.now()
        self.notes = notes
        self.target_price = target_price
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            WatchlistItem as dictionary
        """
        return {
            "ticker": self.ticker,
            "added_date": self.added_date.isoformat(),
            "notes": self.notes,
            "target_price": self.target_price,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WatchlistItem":
        """Create watchlist item from dictionary.

        Args:
            data: Item dictionary

        Returns:
            WatchlistItem instance
        """
        return cls(
            ticker=data["ticker"],
            added_date=datetime.fromisoformat(data["added_date"]),
            notes=data.get("notes"),
            target_price=data.get("target_price"),
            metadata=data.get("metadata"),
        )


class PortfolioState:
    """Manages portfolio state and persistence."""

    def __init__(self, state_file: str | Path = "data/portfolio_state.json"):
        """Initialize portfolio state.

        Args:
            state_file: Path to state JSON file
        """
        self.state_file = Path(state_file)
        self.positions: dict[str, Position] = {}
        self.watchlist: dict[str, WatchlistItem] = {}
        self.last_updated = datetime.now()
        self._load()

    def to_dict(self) -> dict[str, Any]:
        """Convert portfolio state to dictionary.

        Returns:
            Dictionary representation of portfolio state
        """
        return {
            "positions": {ticker: pos.to_dict() for ticker, pos in self.positions.items()},
            "watchlist": {ticker: item.to_dict() for ticker, item in self.watchlist.items()},
            "last_updated": self.last_updated.isoformat(),
        }

    def add_position(
        self,
        ticker: str,
        quantity: float,
        entry_price: float,
        entry_date: datetime = None,
    ) -> None:
        """Add or update position.

        Args:
            ticker: Stock ticker symbol
            quantity: Number of shares
            entry_price: Entry price
            entry_date: Entry date (defaults to now)
        """
        if entry_date is None:
            entry_date = datetime.now()

        self.positions[ticker] = Position(
            ticker=ticker,
            quantity=quantity,
            entry_price=entry_price,
            entry_date=entry_date,
        )
        self.last_updated = datetime.now()
        logger.debug(f"Added position: {ticker} x{quantity} @ {entry_price}")
        self._save()

    def remove_position(self, ticker: str) -> bool:
        """Remove position.

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if removed, False if not found
        """
        if ticker in self.positions:
            del self.positions[ticker]
            self.last_updated = datetime.now()
            logger.debug(f"Removed position: {ticker}")
            self._save()
            return True
        return False

    def get_position(self, ticker: str) -> Optional[Position]:
        """Get position.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Position or None
        """
        return self.positions.get(ticker)

    def add_to_watchlist(
        self,
        ticker: str,
        notes: str = None,
        target_price: float = None,
    ) -> None:
        """Add item to watchlist.

        Args:
            ticker: Stock ticker symbol
            notes: Personal notes
            target_price: Target price
        """
        self.watchlist[ticker] = WatchlistItem(
            ticker=ticker,
            notes=notes,
            target_price=target_price,
        )
        self.last_updated = datetime.now()
        logger.debug(f"Added to watchlist: {ticker}")
        self._save()

    def remove_from_watchlist(self, ticker: str) -> bool:
        """Remove item from watchlist.

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if removed, False if not found
        """
        if ticker in self.watchlist:
            del self.watchlist[ticker]
            self.last_updated = datetime.now()
            logger.debug(f"Removed from watchlist: {ticker}")
            self._save()
            return True
        return False

    def get_watchlist_item(self, ticker: str) -> Optional[WatchlistItem]:
        """Get watchlist item.

        Args:
            ticker: Stock ticker symbol

        Returns:
            WatchlistItem or None
        """
        return self.watchlist.get(ticker)

    def portfolio_summary(self, price_map: dict[str, float]) -> dict[str, Any]:
        """Calculate portfolio summary.

        Args:
            price_map: Dictionary of ticker -> current price

        Returns:
            Portfolio summary with totals
        """
        total_cost = 0
        total_value = 0
        total_pnl = 0

        for ticker, position in self.positions.items():
            current_price = price_map.get(ticker, 0)
            total_cost += position.cost_basis()
            total_value += position.current_value(current_price)
            total_pnl += position.unrealized_pnl(current_price)

        return {
            "num_positions": len(self.positions),
            "total_cost_basis": round(total_cost, 2),
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_return_pct": round(total_pnl / total_cost * 100, 2) if total_cost > 0 else 0,
        }

    def _load(self) -> None:
        """Load state from file."""
        if not self.state_file.exists():
            logger.debug(f"No existing state file: {self.state_file}")
            return

        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)

            # Load positions
            for ticker, pos_data in data.get("positions", {}).items():
                self.positions[ticker] = Position.from_dict(pos_data)

            # Load watchlist
            for ticker, item_data in data.get("watchlist", {}).items():
                self.watchlist[ticker] = WatchlistItem.from_dict(item_data)

            if data.get("last_updated"):
                self.last_updated = datetime.fromisoformat(data["last_updated"])

            logger.debug(
                f"Loaded state: {len(self.positions)} positions, "
                f"{len(self.watchlist)} watchlist items"
            )

        except Exception as e:
            logger.error(f"Failed to load portfolio state: {e}")

    def _save(self) -> None:
        """Save state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "positions": {ticker: pos.to_dict() for ticker, pos in self.positions.items()},
                "watchlist": {ticker: item.to_dict() for ticker, item in self.watchlist.items()},
                "last_updated": self.last_updated.isoformat(),
            }

            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Portfolio state saved to {self.state_file}")

        except Exception as e:
            logger.error(f"Failed to save portfolio state: {e}")
