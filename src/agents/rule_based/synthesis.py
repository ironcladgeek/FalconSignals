"""Signal synthesis module for rule-based analysis."""

from typing import Any

from src.agents.base import AgentConfig, BaseAgent
from src.config import get_config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SignalSynthesisModule(BaseAgent):
    """Module for synthesizing multiple signals into final recommendations (rule-based)."""

    def __init__(self, tools: list | None = None):
        """Initialize Signal Synthesis module.

        Args:
            tools: Optional list of tools
        """
        config = AgentConfig(
            role="Signal Synthesizer",
            goal="Combine technical, fundamental, and sentiment signals to generate high-confidence investment recommendations",
            backstory=(
                "You are a master strategist who synthesizes diverse data sources into actionable recommendations. "
                "You understand how technical, fundamental, and sentiment factors interact to drive prices. "
                "Your ability to weight different signals appropriately has generated exceptional returns."
            ),
        )
        super().__init__(config, tools or [])

    def execute(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Synthesize signals into recommendation.

        Args:
            task: Task description
            context: Context with analysis results

        Returns:
            Final recommendation with confidence
        """
        try:
            context = context or {}
            ticker = context.get("ticker")

            if not ticker:
                return {
                    "status": "error",
                    "message": "No ticker provided",
                    "recommendation": "hold",
                    "confidence": 0,
                }

            logger.debug(f"Synthesizing signals for {ticker}")

            # Extract scores from context
            technical_score = context.get("technical_score", 50)
            fundamental_score = context.get("fundamental_score", 50)
            sentiment_score = context.get("sentiment_score", 50)

            # Weight the scores (from configuration)
            config = get_config()
            weights = {
                "technical": config.analysis.weight_technical,
                "fundamental": config.analysis.weight_fundamental,
                "sentiment": config.analysis.weight_sentiment,
            }

            # Calculate final score
            final_score = (
                technical_score * weights["technical"]
                + fundamental_score * weights["fundamental"]
                + sentiment_score * weights["sentiment"]
            )

            # Calculate confidence based on agreement
            scores = [technical_score, fundamental_score, sentiment_score]
            score_variance = max(scores) - min(scores)
            confidence = max(0, 100 - score_variance * 0.5)  # Lower variance = higher confidence

            # Generate recommendation
            recommendation = self._score_to_recommendation(final_score)

            result = {
                "status": "success",
                "ticker": ticker,
                "final_score": round(final_score, 2),
                "confidence": round(confidence, 2),
                "recommendation": recommendation,
                "component_scores": {
                    "technical": technical_score,
                    "fundamental": fundamental_score,
                    "sentiment": sentiment_score,
                },
                "weights": weights,
                "rationale": self._generate_rationale(
                    final_score, technical_score, fundamental_score, sentiment_score
                ),
            }

            logger.debug(
                f"Signal synthesis for {ticker}: {recommendation} "
                f"({final_score:.0f}/100, confidence: {confidence:.0f}%)"
            )
            self.remember(f"{ticker}_signal", result)

            return result

        except Exception as e:
            logger.error(f"Error during signal synthesis: {e}")
            return {
                "status": "error",
                "message": str(e),
                "recommendation": "hold",
                "confidence": 0,
            }

    @staticmethod
    def _score_to_recommendation(score: float) -> str:
        """Convert score to recommendation.

        Args:
            score: Final score (0-100)

        Returns:
            Recommendation string
        """
        if score >= 75:
            return "buy"
        elif score >= 60:
            return "hold_bullish"
        elif score >= 40:
            return "hold"
        elif score >= 25:
            return "hold_bearish"
        else:
            return "sell"

    @staticmethod
    def _generate_rationale(
        final: float, technical: float, fundamental: float, sentiment: float
    ) -> str:
        """Generate explanation for recommendation.

        Args:
            final: Final score
            technical: Technical score
            fundamental: Fundamental score
            sentiment: Sentiment score

        Returns:
            Rationale string
        """
        strong_factors = []

        if technical > 70:
            strong_factors.append("strong technical momentum")
        elif technical < 30:
            strong_factors.append("weak technical setup")

        if fundamental > 70:
            strong_factors.append("solid fundamentals")
        elif fundamental < 30:
            strong_factors.append("concerns about fundamentals")

        if sentiment > 70:
            strong_factors.append("positive market sentiment")
        elif sentiment < 30:
            strong_factors.append("negative market sentiment")

        if strong_factors:
            return f"Based on {', '.join(strong_factors)}."
        else:
            return "Mixed signals from various factors."
