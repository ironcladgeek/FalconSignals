"""Risk assessment module for evaluating investment risks."""

from typing import Any

from src.analysis.models import RiskAssessment, RiskLevel
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RiskAssessor:
    """Evaluates and scores investment risks."""

    def __init__(
        self,
        volatility_threshold_high: float = 3.0,
        volatility_threshold_very_high: float = 5.0,
        liquidity_threshold_illiquid: float = 50000,
    ):
        """Initialize risk assessor.

        Args:
            volatility_threshold_high: ATR % threshold for high volatility
            volatility_threshold_very_high: ATR % threshold for very high volatility
            liquidity_threshold_illiquid: Daily volume threshold (EUR) for illiquid assets
        """
        self.volatility_threshold_high = volatility_threshold_high
        self.volatility_threshold_very_high = volatility_threshold_very_high
        self.liquidity_threshold_illiquid = liquidity_threshold_illiquid

        logger.debug(
            f"Risk assessor initialized: high_vol={volatility_threshold_high}%, "
            f"very_high_vol={volatility_threshold_very_high}%"
        )

    def assess_signal(
        self,
        signal: dict[str, Any],
        portfolio_context: dict[str, Any] | None = None,
    ) -> RiskAssessment:
        """Assess risks for an investment signal.

        Args:
            signal: Investment signal data
            portfolio_context: Current portfolio state for concentration analysis

        Returns:
            Risk assessment with level and flags
        """
        portfolio_context = portfolio_context or {}

        ticker = signal.get("ticker", "UNKNOWN")
        final_score = signal.get("final_score", 50)
        confidence = signal.get("confidence", 50)

        # Assess volatility
        volatility_pct = signal.get("volatility_pct", 2.0)
        volatility_level = self._assess_volatility(volatility_pct)

        # Assess liquidity
        estimated_volume = signal.get("estimated_daily_volume", 100000)
        liquidity_level = self._assess_liquidity(estimated_volume)

        # Assess sector risk
        sector = signal.get("sector", "Unknown")
        sector_risks = self._assess_sector_risk(sector)

        # Assess concentration risk
        concentration_risk = self._assess_concentration_risk(
            ticker, signal.get("market", "unknown"), portfolio_context
        )

        # Check for warning flags
        flags = self._generate_risk_flags(
            signal, volatility_level, liquidity_level, sector_risks, concentration_risk
        )

        # Determine overall risk level
        overall_risk_level = self._determine_risk_level(
            final_score, confidence, volatility_level, liquidity_level, len(flags)
        )

        assessment = RiskAssessment(
            level=overall_risk_level,
            volatility=volatility_level,
            volatility_pct=volatility_pct,
            liquidity=liquidity_level,
            concentration_risk=concentration_risk,
            sector_risk=sector_risks,
            flags=flags,
        )

        logger.debug(
            f"Risk assessment for {ticker}: {overall_risk_level.value} "
            f"(volatility: {volatility_level}, liquidity: {liquidity_level})"
        )

        return assessment

    def _assess_volatility(self, atr_pct: float) -> str:
        """Assess volatility level based on ATR.

        Args:
            atr_pct: ATR as percentage of price

        Returns:
            Volatility level: low, normal, high, or very_high
        """
        if atr_pct < 1.0:
            return "low"
        elif atr_pct < self.volatility_threshold_high:
            return "normal"
        elif atr_pct < self.volatility_threshold_very_high:
            return "high"
        else:
            return "very_high"

    def _assess_liquidity(self, daily_volume_eur: float) -> str:
        """Assess liquidity based on daily volume.

        Args:
            daily_volume_eur: Estimated daily trading volume in EUR

        Returns:
            Liquidity level: illiquid, normal, or highly_liquid
        """
        if daily_volume_eur < self.liquidity_threshold_illiquid:
            return "illiquid"
        elif daily_volume_eur < self.liquidity_threshold_illiquid * 5:
            return "normal"
        else:
            return "highly_liquid"

    @staticmethod
    def _assess_sector_risk(sector: str) -> str | None:
        """Assess sector-specific risks.

        Args:
            sector: Industry sector classification

        Returns:
            Sector-specific risk assessment or None
        """
        high_risk_sectors = [
            "biotechnology",
            "cryptocurrency",
            "renewable_energy",
            "penny stocks",
            "leveraged",
        ]
        cyclical_sectors = ["consumer_discretionary", "industrial", "materials"]

        sector_lower = sector.lower() if sector else ""

        if any(risk in sector_lower for risk in high_risk_sectors):
            return "High sector risk - cyclical/speculative"
        elif any(cyc in sector_lower for cyc in cyclical_sectors):
            return "Moderate sector risk - cyclical exposure"

        return None

    def _assess_concentration_risk(
        self,
        ticker: str,
        market: str,
        portfolio_context: dict[str, Any],
    ) -> bool:
        """Assess portfolio concentration risk.

        Args:
            ticker: Stock ticker
            market: Market classification
            portfolio_context: Current portfolio state

        Returns:
            True if concentration risk detected
        """
        existing_positions = portfolio_context.get("positions", {})
        portfolio_value = portfolio_context.get("total_value", 1000)  # Default 1000€

        # Check if already have large position
        existing_position = existing_positions.get(ticker, {})
        existing_value = existing_position.get("value", 0)
        position_pct = (existing_value / portfolio_value * 100) if portfolio_value > 0 else 0

        return position_pct > 15  # Flag if >15% of portfolio already

    def _generate_risk_flags(
        self,
        signal: dict[str, Any],
        volatility: str,
        liquidity: str,
        sector_risk: str | None,
        concentration_risk: bool,
    ) -> list[str]:
        """Generate risk warning flags.

        Args:
            signal: Investment signal
            volatility: Volatility assessment
            liquidity: Liquidity assessment
            sector_risk: Sector risk description
            concentration_risk: Concentration risk flag

        Returns:
            List of risk warning messages
        """
        flags = []

        ticker = signal.get("ticker", "UNKNOWN")
        confidence = signal.get("confidence", 50)
        final_score = signal.get("final_score", 50)
        expected_return_max = signal.get("expected_return_max", 10)

        # Low confidence warning
        if confidence < 50:
            flags.append(f"{ticker}: Low confidence signal ({confidence}%)")

        # Mixed signals warning
        scores = signal.get("scores", {})
        tech_score = scores.get("technical", 50)
        fund_score = scores.get("fundamental", 50)
        sent_score = scores.get("sentiment", 50)
        score_variance = max(tech_score, fund_score, sent_score) - min(
            tech_score, fund_score, sent_score
        )
        if score_variance > 40:
            flags.append(f"{ticker}: Conflicting signals across analysis factors")

        # Negative return expectation
        if expected_return_max < 0:
            flags.append(f"{ticker}: Negative expected return ({expected_return_max}%)")

        # High volatility warning
        if volatility in ["high", "very_high"]:
            flags.append(f"{ticker}: High volatility ({volatility})")

        # Illiquid asset warning
        if liquidity == "illiquid":
            flags.append(f"{ticker}: Illiquid asset - difficult to exit position")

        # Sector risk
        if sector_risk:
            flags.append(f"{ticker}: {sector_risk}")

        # Concentration risk
        if concentration_risk:
            flags.append(f"{ticker}: Position would exceed concentration limits")

        # Recent momentum without fundamental support
        if final_score >= 70 and fund_score < 40:
            flags.append(
                f"{ticker}: Strong technical signal but weak fundamentals - potential momentum trap"
            )

        return flags

    @staticmethod
    def _determine_risk_level(
        final_score: float,
        confidence: float,
        volatility: str,
        liquidity: str,
        num_flags: int,
    ) -> RiskLevel:
        """Determine overall risk level.

        Args:
            final_score: Final analysis score 0-100
            confidence: Confidence percentage 0-100
            volatility: Volatility level assessment
            liquidity: Liquidity level assessment
            num_flags: Number of risk flags raised

        Returns:
            Overall risk level
        """
        risk_score = 0

        # Score-based risk
        if final_score < 30:
            risk_score += 30  # Very risky
        elif final_score < 50:
            risk_score += 15  # Risky
        elif final_score > 75:
            risk_score -= 10  # Lower risk with strong signal

        # Confidence-based risk
        if confidence < 40:
            risk_score += 25
        elif confidence < 60:
            risk_score += 10

        # Volatility-based risk
        volatility_scores = {
            "low": -5,
            "normal": 0,
            "high": 15,
            "very_high": 30,
        }
        risk_score += volatility_scores.get(volatility, 0)

        # Liquidity-based risk
        liquidity_scores = {
            "illiquid": 20,
            "normal": 0,
            "highly_liquid": -5,
        }
        risk_score += liquidity_scores.get(liquidity, 0)

        # Flag-based risk
        risk_score += num_flags * 5

        # Determine level
        if risk_score >= 60:
            return RiskLevel.VERY_HIGH
        elif risk_score >= 40:
            return RiskLevel.HIGH
        elif risk_score >= 20:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
