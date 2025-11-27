"""Portfolio allocation engine with position sizing and diversification management."""

from datetime import datetime
from typing import Any

from src.analysis.models import AllocationSuggestion, PortfolioAllocation
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AllocationEngine:
    """Manages portfolio position sizing and allocation suggestions."""

    def __init__(
        self,
        total_capital: float,
        monthly_deposit: float,
        max_position_size_pct: float = 10.0,
        max_sector_concentration_pct: float = 20.0,
        min_diversification_score: float = 60.0,
    ):
        """Initialize allocation engine.

        Args:
            total_capital: Total available capital in EUR
            monthly_deposit: Monthly deposit amount in EUR
            max_position_size_pct: Maximum single position size (% of capital)
            max_sector_concentration_pct: Maximum sector concentration (% of capital)
            min_diversification_score: Minimum diversification score target
        """
        self.total_capital = total_capital
        self.monthly_deposit = monthly_deposit
        self.max_position_size_pct = max_position_size_pct
        self.max_sector_concentration_pct = max_sector_concentration_pct
        self.min_diversification_score = min_diversification_score

        logger.info(
            f"Allocation engine initialized: capital={total_capital}€, "
            f"monthly_deposit={monthly_deposit}€"
        )

    def allocate_signals(
        self,
        signals: list[dict[str, Any]],
        existing_positions: dict[str, dict[str, Any]] | None = None,
    ) -> PortfolioAllocation:
        """Generate allocation suggestions from investment signals.

        Args:
            signals: List of investment signals with scores and recommendations
            existing_positions: Current portfolio positions by ticker

        Returns:
            Portfolio allocation suggestion
        """
        existing_positions = existing_positions or {}

        # Calculate available capital for new allocations
        allocated_capital = sum(pos.get("value", 0) for pos in existing_positions.values())
        available_for_allocation = max(0, self.total_capital - allocated_capital)

        logger.info(
            f"Allocating from {available_for_allocation}€ available capital "
            f"({allocated_capital}€ already allocated)"
        )

        # Rank signals by recommendation strength and confidence
        ranked_signals = self._rank_signals(signals)

        # Generate position suggestions
        suggested_positions: list[AllocationSuggestion] = []
        current_capital_used = 0.0
        current_sector_allocation: dict[str, float] = {}
        current_market_allocation: dict[str, float] = {}

        for signal in ranked_signals:
            if current_capital_used >= available_for_allocation * 0.95:  # Leave 5% buffer
                break

            ticker = signal.get("ticker", "UNKNOWN")
            sector = signal.get("sector") or "Unknown"
            market = signal.get("market") or "unknown"
            current_price = signal.get("current_price", 0)
            confidence = signal.get("confidence", 0)
            final_score = signal.get("final_score", 50)

            # Skip low-confidence signals
            if confidence < 50:
                logger.debug(f"Skipping {ticker}: low confidence ({confidence}%)")
                continue

            # Calculate position size using Kelly criterion (modified)
            max_position_eur = self.total_capital * (self.max_position_size_pct / 100)
            expected_return = (
                signal.get("expected_return_max", 0) + signal.get("expected_return_min", 0)
            ) / 2
            win_rate = confidence / 100.0

            # Modified Kelly: position_size = (win_rate * avg_return - (1 - win_rate)) / avg_return
            if expected_return > 0:
                kelly_fraction = ((win_rate * expected_return) - (1 - win_rate)) / max(
                    expected_return, 1
                )
                kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
                position_size = max_position_eur * kelly_fraction
            else:
                position_size = 0

            # Enforce constraints
            position_size = self._apply_constraints(
                position_size,
                ticker,
                sector,
                market,
                current_capital_used,
                available_for_allocation,
                current_sector_allocation,
                current_market_allocation,
            )

            if position_size <= 0:
                logger.debug(f"Skipping {ticker}: position size constraint violation")
                continue

            # Create allocation suggestion
            shares = position_size / current_price if current_price > 0 else 0
            allocation = AllocationSuggestion(
                ticker=ticker,
                eur=round(position_size, 2),
                percentage=round((position_size / self.total_capital) * 100, 2),
                shares=round(shares, 2) if shares > 0 else None,
            )

            suggested_positions.append(allocation)
            current_capital_used += position_size

            # Update diversification tracking
            current_sector_allocation[sector] = (
                current_sector_allocation.get(sector, 0) + position_size
            )
            current_market_allocation[market] = (
                current_market_allocation.get(market, 0) + position_size
            )

            logger.debug(
                f"Allocated {ticker}: {position_size}€ "
                f"(confidence: {confidence}%, score: {final_score}/100)"
            )

        # Calculate diversification score
        diversification_score = self._calculate_diversification_score(
            current_sector_allocation, current_market_allocation, current_capital_used
        )

        # Convert sector/market allocations to percentages
        sector_div = {
            sector: round((amount / current_capital_used) * 100, 2)
            for sector, amount in current_sector_allocation.items()
            if current_capital_used > 0 and sector is not None
        }
        market_div = {
            market: round((amount / current_capital_used) * 100, 2)
            for market, amount in current_market_allocation.items()
            if current_capital_used > 0 and market is not None
        }

        # Calculate instrument type diversification (approximation)
        instrument_div = self._estimate_instrument_diversification(suggested_positions)

        # Create allocation result
        allocation = PortfolioAllocation(
            total_capital=self.total_capital,
            monthly_deposit=self.monthly_deposit,
            available_for_allocation=available_for_allocation,
            suggested_positions=suggested_positions,
            diversification_score=round(diversification_score, 2),
            market_diversification=market_div if market_div else {"unallocated": 100.0},
            sector_diversification=sector_div if sector_div else {"unallocated": 100.0},
            instrument_diversification=instrument_div,
            total_allocated=round(current_capital_used, 2),
            total_allocated_pct=round((current_capital_used / self.total_capital) * 100, 2),
            unallocated=round(self.total_capital - allocated_capital - current_capital_used, 2),
            constraints_applied={
                "max_position_size_pct": self.max_position_size_pct,
                "max_sector_concentration_pct": self.max_sector_concentration_pct,
                "min_diversification_score": self.min_diversification_score,
            },
            generated_at=datetime.now(),
        )

        logger.info(
            f"Allocation complete: {len(suggested_positions)} positions, "
            f"{allocation.total_allocated_pct}% allocated, "
            f"diversification score: {diversification_score:.0f}"
        )

        return allocation

    def _rank_signals(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rank signals by investment quality.

        Args:
            signals: List of signals to rank

        Returns:
            Ranked signals (best first)
        """

        def signal_score(signal: dict[str, Any]) -> tuple[int, float, float]:
            """Calculate signal rank score."""
            # Recommendation strength mapping
            recommendation = signal.get("recommendation", "hold")
            strength_map = {
                "strong_buy": 7,
                "buy": 6,
                "hold_bullish": 5,
                "hold": 4,
                "hold_bearish": 3,
                "sell": 2,
                "strong_sell": 1,
            }
            strength = strength_map.get(recommendation, 0)

            # Use confidence and final score as tiebreakers
            confidence = signal.get("confidence", 0)
            final_score = signal.get("final_score", 50)

            return (strength, confidence, final_score)

        ranked = sorted(signals, key=signal_score, reverse=True)
        return ranked

    def _apply_constraints(
        self,
        position_size: float,
        ticker: str,
        sector: str,
        market: str,
        current_capital_used: float,
        available_capital: float,
        sector_allocation: dict[str, float],
        market_allocation: dict[str, float],
    ) -> float:
        """Apply allocation constraints to position size.

        Args:
            position_size: Proposed position size in EUR
            ticker: Stock ticker
            sector: Sector classification
            market: Market classification
            current_capital_used: Capital already allocated
            available_capital: Total capital available
            sector_allocation: Current sector allocation tracking
            market_allocation: Current market allocation tracking

        Returns:
            Adjusted position size respecting constraints
        """
        adjusted_size = position_size

        # Constraint 1: Max position size
        max_position_eur = self.total_capital * (self.max_position_size_pct / 100)
        adjusted_size = min(adjusted_size, max_position_eur)

        # Constraint 2: Max sector concentration
        max_sector_eur = self.total_capital * (self.max_sector_concentration_pct / 100)
        current_sector_total = sector_allocation.get(sector, 0) + adjusted_size
        if current_sector_total > max_sector_eur:
            adjusted_size = max(0, max_sector_eur - sector_allocation.get(sector, 0))

        # Constraint 3: Don't exceed available capital
        if current_capital_used + adjusted_size > available_capital:
            adjusted_size = max(0, available_capital - current_capital_used)

        # Constraint 4: Minimum position size (at least 50€ if allocated)
        min_position = 50.0
        if 0 < adjusted_size < min_position:
            adjusted_size = 0

        return adjusted_size

    def _calculate_diversification_score(
        self,
        sector_allocation: dict[str, float],
        market_allocation: dict[str, float],
        total_allocated: float,
    ) -> float:
        """Calculate portfolio diversification score.

        Args:
            sector_allocation: Allocation by sector in EUR
            market_allocation: Allocation by market in EUR
            total_allocated: Total capital allocated

        Returns:
            Diversification score 0-100
        """
        if total_allocated == 0:
            return 0

        # Calculate Herfindahl index for concentration (lower is better)
        sector_fractions = [
            (amount / total_allocated) ** 2 for amount in sector_allocation.values()
        ]
        sector_hhi = sum(sector_fractions)

        market_fractions = [
            (amount / total_allocated) ** 2 for amount in market_allocation.values()
        ]
        market_hhi = sum(market_fractions)

        # Convert HHI to diversification score (0-100)
        # HHI ranges from 0 (perfect diversity) to 1 (single concentration)
        sector_score = (1 - sector_hhi) * 100
        market_score = (1 - market_hhi) * 100

        # Combine with weights: 70% sector, 30% market
        diversification_score = (sector_score * 0.7) + (market_score * 0.3)

        return max(0, min(100, diversification_score))

    @staticmethod
    def _estimate_instrument_diversification(
        positions: list[AllocationSuggestion],
    ) -> dict[str, float]:
        """Estimate instrument type diversification.

        Args:
            positions: List of allocation suggestions

        Returns:
            Estimated diversification by type
        """
        # For now, return placeholder (in production, would use metadata)
        total = sum(p.eur for p in positions) if positions else 0

        # Simple heuristic: classify by ticker patterns
        stocks = sum(p.eur for p in positions if len(p.ticker) <= 4)  # Most stocks are short
        etfs = sum(p.eur for p in positions if len(p.ticker) > 4)  # ETFs often longer

        div_dict = {}
        if total > 0:
            div_dict["stocks"] = round((stocks / total) * 100, 2)
            div_dict["etfs"] = round((etfs / total) * 100, 2)
        else:
            div_dict["unallocated"] = 100.0

        return div_dict
