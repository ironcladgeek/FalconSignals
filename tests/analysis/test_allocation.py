"""Tests for portfolio allocation engine."""

import pytest

from src.analysis.allocation import AllocationEngine
from src.analysis.models import AllocationSuggestion


@pytest.mark.unit
class TestAllocationEngine:
    """Test AllocationEngine functionality."""

    @pytest.fixture
    def allocation_engine(self):
        """Create allocation engine instance."""
        return AllocationEngine(
            total_capital=10000,
            monthly_deposit=500,
            max_position_size_pct=10.0,
            max_sector_concentration_pct=20.0,
        )

    def test_allocation_engine_initialization(self, allocation_engine):
        """Test allocation engine initialization."""
        assert allocation_engine.total_capital == 10000
        assert allocation_engine.monthly_deposit == 500
        assert allocation_engine.max_position_size_pct == 10.0
        assert allocation_engine.max_sector_concentration_pct == 20.0

    def test_allocate_signals_basic(self, allocation_engine):
        """Test basic signal allocation."""
        signals = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 150.0,
                "confidence": 80,
                "final_score": 75,
                "recommendation": "buy",
                "expected_return_min": 5.0,
                "expected_return_max": 15.0,
            },
            {
                "ticker": "MSFT",
                "name": "Microsoft Corp.",
                "market": "us",
                "sector": "Technology",
                "current_price": 300.0,
                "confidence": 75,
                "final_score": 70,
                "recommendation": "buy",
                "expected_return_min": 3.0,
                "expected_return_max": 12.0,
            },
        ]

        allocation = allocation_engine.allocate_signals(signals)

        assert allocation is not None
        assert len(allocation.suggested_positions) > 0
        assert allocation.total_allocated > 0
        assert allocation.total_allocated <= allocation_engine.total_capital

    def test_allocate_signals_empty_list(self, allocation_engine):
        """Test allocation with empty signal list."""
        allocation = allocation_engine.allocate_signals([])

        assert allocation is not None
        assert len(allocation.suggested_positions) == 0
        assert allocation.total_allocated == 0

    def test_allocate_signals_with_existing_positions(self, allocation_engine):
        """Test allocation considering existing positions."""
        signals = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 150.0,
                "confidence": 80,
                "final_score": 75,
                "recommendation": "buy",
                "expected_return_min": 5.0,
                "expected_return_max": 15.0,
            }
        ]

        existing_positions = {
            "AAPL": {
                "quantity": 10,
                "avg_price": 140.0,
                "current_value": 1500.0,
            }
        }

        allocation = allocation_engine.allocate_signals(signals, existing_positions)

        assert allocation is not None
        # Should consider existing position in calculations

    def test_position_size_limits(self, allocation_engine):
        """Test that position size limits are enforced."""
        signals = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 150.0,
                "confidence": 95,  # High confidence
                "final_score": 90,
                "recommendation": "strong_buy",
                "expected_return_min": 10.0,
                "expected_return_max": 25.0,
            }
        ]

        allocation = allocation_engine.allocate_signals(signals)

        # Position should not exceed max_position_size_pct of capital
        max_position_size = allocation_engine.total_capital * (
            allocation_engine.max_position_size_pct / 100
        )
        assert allocation.total_allocated <= max_position_size

    def test_sector_concentration_limits(self, allocation_engine):
        """Test that sector concentration limits are enforced."""
        signals = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 150.0,
                "confidence": 80,
                "final_score": 75,
                "recommendation": "buy",
                "expected_return_min": 5.0,
                "expected_return_max": 15.0,
            },
            {
                "ticker": "MSFT",
                "name": "Microsoft Corp.",
                "market": "us",
                "sector": "Technology",
                "current_price": 300.0,
                "confidence": 80,
                "final_score": 75,
                "recommendation": "buy",
                "expected_return_min": 5.0,
                "expected_return_max": 15.0,
            },
            {
                "ticker": "GOOGL",
                "name": "Alphabet Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 2500.0,
                "confidence": 80,
                "final_score": 75,
                "recommendation": "buy",
                "expected_return_min": 5.0,
                "expected_return_max": 15.0,
            },
        ]

        allocation = allocation_engine.allocate_signals(signals)

        # Technology sector should not exceed max_sector_concentration_pct
        tech_allocations = [
            sugg
            for sugg in allocation.suggested_positions
            if sugg.ticker in ["AAPL", "MSFT", "GOOGL"]  # All tech stocks
        ]
        tech_total = sum(sugg.eur for sugg in tech_allocations)
        max_sector_allocation = allocation_engine.total_capital * (
            allocation_engine.max_sector_concentration_pct / 100
        )

        assert tech_total <= max_sector_allocation

    def test_diversification_scoring(self, allocation_engine):
        """Test diversification score calculation."""
        # Well diversified portfolio
        signals = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 150.0,
                "confidence": 80,
                "final_score": 75,
                "recommendation": "buy",
                "expected_return_min": 5.0,
                "expected_return_max": 15.0,
            },
            {
                "ticker": "JPM",
                "name": "JPMorgan Chase",
                "market": "us",
                "sector": "Financials",
                "current_price": 200.0,
                "confidence": 75,
                "final_score": 70,
                "recommendation": "buy",
                "expected_return_min": 3.0,
                "expected_return_max": 10.0,
            },
            {
                "ticker": "JNJ",
                "name": "Johnson & Johnson",
                "market": "us",
                "sector": "Healthcare",
                "current_price": 180.0,
                "confidence": 70,
                "final_score": 65,
                "recommendation": "buy",
                "expected_return_min": 2.0,
                "expected_return_max": 8.0,
            },
        ]

        allocation = allocation_engine.allocate_signals(signals)

        assert allocation.diversification_score >= 0
        assert allocation.diversification_score <= 100
        # Well diversified portfolio should have reasonable score
        assert allocation.diversification_score > 40

    def test_kelly_criterion_application(self, allocation_engine):
        """Test Kelly criterion application in position sizing."""
        signals = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 150.0,
                "confidence": 90,  # High confidence
                "final_score": 85,
                "recommendation": "strong_buy",
                "expected_return_min": 15.0,
                "expected_return_max": 30.0,
            }
        ]

        allocation = allocation_engine.allocate_signals(signals)

        # High confidence signals should get larger allocations
        assert allocation.total_allocated > 0

    def test_allocation_suggestion_structure(self, allocation_engine):
        """Test that allocation suggestions have correct structure."""
        signals = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 150.0,
                "confidence": 80,
                "final_score": 75,
                "recommendation": "buy",
                "expected_return_min": 5.0,
                "expected_return_max": 15.0,
            }
        ]

        allocation = allocation_engine.allocate_signals(signals)

        suggestion = allocation.suggested_positions[0]
        assert isinstance(suggestion, AllocationSuggestion)
        assert suggestion.ticker == "AAPL"
        assert suggestion.eur > 0
        assert suggestion.percentage > 0
        assert suggestion.percentage <= allocation_engine.max_position_size_pct
        assert suggestion.eur > 0  # Just check it's allocated

    def test_zero_capital_handling(self):
        """Test handling of zero capital."""
        engine = AllocationEngine(total_capital=0, monthly_deposit=0)

        signals = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 150.0,
                "confidence": 80,
                "final_score": 75,
                "recommendation": "buy",
                "expected_return_min": 5.0,
                "expected_return_max": 15.0,
            }
        ]

        allocation = engine.allocate_signals(signals)

        assert allocation.total_allocated == 0
        assert len(allocation.suggested_positions) == 0

    def test_sell_signals_handling(self, allocation_engine):
        """Test handling of sell signals."""
        signals = [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "sector": "Technology",
                "current_price": 150.0,
                "confidence": 80,
                "final_score": 25,  # Low score
                "recommendation": "sell",
                "expected_return_min": -10.0,
                "expected_return_max": -5.0,
            }
        ]

        allocation = allocation_engine.allocate_signals(signals)

        # Sell signals should result in zero or negative allocation
        assert allocation.total_allocated == 0
