"""Normalize analysis results from both LLM and rule-based modes to unified structure."""

from typing import Any

from src.analysis.models import (
    AnalysisComponentResult,
    AnalystInfo,
    FundamentalMetrics,
    RiskAssessment,
    SentimentInfo,
    TechnicalIndicators,
    UnifiedAnalysisResult,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AnalysisResultNormalizer:
    """Normalizes agent outputs to unified structure.

    Converts both LLM and rule-based analysis outputs to UnifiedAnalysisResult,
    ensuring consistent data structure for signal creation and metadata extraction.
    """

    @staticmethod
    def normalize_llm_result(
        ticker: str,
        technical_result: dict[str, Any],
        fundamental_result: dict[str, Any],
        sentiment_result: dict[str, Any],
        synthesis_result: dict[str, Any],
    ) -> UnifiedAnalysisResult:
        """Convert LLM agent outputs to unified structure.

        Args:
            ticker: Stock ticker symbol
            technical_result: Technical analysis agent output (with detailed indicators)
            fundamental_result: Fundamental analysis agent output (with detailed metrics)
            sentiment_result: Sentiment analysis agent output (with detailed info)
            synthesis_result: Synthesis agent output (scores + recommendation)

        Returns:
            UnifiedAnalysisResult with all detailed metrics preserved
        """
        logger.debug(f"Normalizing LLM results for {ticker}")

        # Extract technical component (detailed indicators from agent output, not synthesis)
        technical = AnalysisResultNormalizer._extract_technical_llm(technical_result)

        # Extract fundamental component
        fundamental = AnalysisResultNormalizer._extract_fundamental_llm(fundamental_result)

        # Extract sentiment component
        sentiment = AnalysisResultNormalizer._extract_sentiment_llm(sentiment_result)

        # Extract synthesis data
        synthesis_data = synthesis_result.get("result", {})
        if hasattr(synthesis_data, "raw"):
            synthesis_data = synthesis_data.raw

        # Convert string to dict
        if isinstance(synthesis_data, str):
            import json

            try:
                synthesis_data = json.loads(synthesis_data)
                # Ensure result is a dict
                if not isinstance(synthesis_data, dict):
                    synthesis_data = {}
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse synthesis result for {ticker}")
                synthesis_data = {}

        # Ensure we have a dict
        if not isinstance(synthesis_data, dict):
            synthesis_data = {}

        # Extract risk assessment from synthesis
        risk_data = synthesis_data.get("risk", {})
        risk_level = (risk_data.get("level") or "medium").lower()
        if risk_level == "moderate":
            risk_level = "medium"

        risk_assessment = RiskAssessment(
            level=risk_level,
            volatility=risk_data.get("volatility") or "normal",
            volatility_pct=risk_data.get("volatility_pct") or 2.0,
            liquidity=risk_data.get("liquidity") or "normal",
            concentration_risk=risk_data.get("concentration_risk") or False,
            sector_risk=risk_data.get("sector_risk"),
            flags=risk_data.get("flags") or risk_data.get("factors") or [],
        )

        return UnifiedAnalysisResult(
            ticker=ticker,
            mode="llm",
            technical=technical,
            fundamental=fundamental,
            sentiment=sentiment,
            final_score=synthesis_data.get("final_score", 50.0),
            recommendation=synthesis_data.get("recommendation", "hold"),
            confidence=synthesis_data.get("confidence", 50.0),
            company_name=synthesis_data.get("name"),
            market=synthesis_data.get("market"),
            sector=synthesis_data.get("sector"),
            risk_assessment=risk_assessment,
            key_reasons=synthesis_data.get("key_reasons", []),
            rationale=synthesis_data.get("rationale"),
            caveats=synthesis_data.get("caveats", []),
            expected_return_min=synthesis_data.get("expected_return_min", 0.0),
            expected_return_max=synthesis_data.get("expected_return_max", 10.0),
            time_horizon=synthesis_data.get("time_horizon", "3M"),
        )

    @staticmethod
    def normalize_rule_based_result(analysis: dict[str, Any]) -> UnifiedAnalysisResult:
        """Convert rule-based analysis to unified structure.

        Args:
            analysis: Rule-based analysis result with nested structure

        Returns:
            UnifiedAnalysisResult with all detailed metrics preserved
        """
        ticker = analysis.get("ticker", "UNKNOWN")
        logger.debug(f"Normalizing rule-based results for {ticker}")

        # Extract component results from nested structure
        analysis_data = analysis.get("analysis", {})

        # Extract technical component
        technical = AnalysisResultNormalizer._extract_technical_rule_based(
            analysis_data.get("technical", {})
        )

        # Extract fundamental component
        fundamental = AnalysisResultNormalizer._extract_fundamental_rule_based(
            analysis_data.get("fundamental", {})
        )

        # Extract sentiment component
        sentiment = AnalysisResultNormalizer._extract_sentiment_rule_based(
            analysis_data.get("sentiment", {})
        )

        # Extract synthesis data
        synthesis_data = analysis_data.get("synthesis", {})
        final_score = analysis.get("final_score", 50)
        confidence = analysis.get("confidence", 50)
        recommendation = analysis.get("final_recommendation", "hold")

        # Extract risk assessment (if present)
        risk_assessment = None
        if "risk_assessment" in analysis:
            risk_data = analysis["risk_assessment"]
            if isinstance(risk_data, RiskAssessment):
                risk_assessment = risk_data
            elif isinstance(risk_data, dict):
                risk_assessment = RiskAssessment(**risk_data)

        return UnifiedAnalysisResult(
            ticker=ticker,
            mode="rule_based",
            technical=technical,
            fundamental=fundamental,
            sentiment=sentiment,
            final_score=final_score,
            recommendation=recommendation,
            confidence=confidence,
            company_name=analysis.get("company_name"),
            market=analysis.get("market"),
            sector=analysis.get("sector"),
            risk_assessment=risk_assessment,
            key_reasons=analysis.get("key_reasons", []),
            rationale=analysis.get("rationale"),
            caveats=analysis.get("caveats", []),
            expected_return_min=analysis.get("expected_return_min", 0.0),
            expected_return_max=analysis.get("expected_return_max", 10.0),
            time_horizon=analysis.get("time_horizon", "3M"),
        )

    @staticmethod
    def _extract_technical_llm(tech_result: dict[str, Any]) -> AnalysisComponentResult:
        """Extract technical analysis component from LLM output."""
        # Handle CrewOutput objects
        if hasattr(tech_result, "raw"):
            tech_result = tech_result.raw

        # Convert string to dict
        if isinstance(tech_result, str):
            import json

            try:
                tech_result = json.loads(tech_result)
                # Ensure result is a dict
                if not isinstance(tech_result, dict):
                    tech_result = {}
            except json.JSONDecodeError:
                tech_result = {}

        # Ensure we have a dict
        if not isinstance(tech_result, dict):
            tech_result = {}

        # LLM technical agent returns detailed indicators in its output
        # Extract and structure them
        indicators_data = tech_result.get("indicators", {})
        components_data = tech_result.get("components", {})

        technical_indicators = TechnicalIndicators(
            rsi=indicators_data.get("rsi"),
            macd=indicators_data.get("macd"),
            macd_signal=indicators_data.get("macd_signal"),
            sma_20=indicators_data.get("sma_20"),
            sma_50=indicators_data.get("sma_50"),
            sma_200=indicators_data.get("sma_200"),
            volume_avg=indicators_data.get("volume_avg")
            or components_data.get("volume", {}).get("avg_volume"),
            atr=indicators_data.get("atr") or components_data.get("volatility", {}).get("atr"),
        )

        return AnalysisComponentResult(
            component="technical",
            score=tech_result.get("technical_score", 50.0),
            raw_data=tech_result,
            technical_indicators=technical_indicators,
            reasoning=tech_result.get("analysis") or tech_result.get("reasoning"),
            confidence=tech_result.get("confidence"),
        )

    @staticmethod
    def _extract_fundamental_llm(fund_result: dict[str, Any]) -> AnalysisComponentResult:
        """Extract fundamental analysis component from LLM output."""
        # Handle CrewOutput objects
        if hasattr(fund_result, "raw"):
            fund_result = fund_result.raw

        # Convert string to dict
        if isinstance(fund_result, str):
            import json

            try:
                fund_result = json.loads(fund_result)
                # Ensure result is a dict
                if not isinstance(fund_result, dict):
                    fund_result = {}
            except json.JSONDecodeError:
                fund_result = {}

        # Ensure we have a dict
        if not isinstance(fund_result, dict):
            fund_result = {}

        metrics_data = fund_result.get("metrics", {})
        analyst_data = fund_result.get("analyst_ratings", {})

        fundamental_metrics = FundamentalMetrics(
            pe_ratio=metrics_data.get("pe_ratio"),
            pb_ratio=metrics_data.get("pb_ratio"),
            ps_ratio=metrics_data.get("ps_ratio"),
            peg_ratio=metrics_data.get("peg_ratio"),
            ev_ebitda=metrics_data.get("ev_ebitda"),
            profit_margin=metrics_data.get("profit_margin"),
            operating_margin=metrics_data.get("operating_margin"),
            roe=metrics_data.get("roe"),
            roa=metrics_data.get("roa"),
            debt_to_equity=metrics_data.get("debt_to_equity"),
            current_ratio=metrics_data.get("current_ratio"),
            revenue_growth=metrics_data.get("revenue_growth"),
            earnings_growth=metrics_data.get("earnings_growth"),
        )

        analyst_info = None
        if analyst_data:
            analyst_info = AnalystInfo(
                num_analysts=analyst_data.get("num_analysts"),
                consensus_rating=analyst_data.get("consensus_rating"),
                strong_buy=analyst_data.get("strong_buy"),
                buy=analyst_data.get("buy"),
                hold=analyst_data.get("hold"),
                sell=analyst_data.get("sell"),
                strong_sell=analyst_data.get("strong_sell"),
                price_target=analyst_data.get("price_target"),
                price_target_high=analyst_data.get("price_target_high"),
                price_target_low=analyst_data.get("price_target_low"),
            )

        return AnalysisComponentResult(
            component="fundamental",
            score=fund_result.get("fundamental_score", 50.0),
            raw_data=fund_result,
            fundamental_metrics=fundamental_metrics,
            analyst_info=analyst_info,
            reasoning=fund_result.get("analysis") or fund_result.get("reasoning"),
            confidence=fund_result.get("confidence"),
        )

    @staticmethod
    def _extract_sentiment_llm(sent_result: dict[str, Any]) -> AnalysisComponentResult:
        """Extract sentiment analysis component from LLM output."""
        # Handle CrewOutput objects
        if hasattr(sent_result, "raw"):
            sent_result = sent_result.raw

        # Convert string to dict
        if isinstance(sent_result, str):
            import json

            try:
                sent_result = json.loads(sent_result)
                # Ensure result is a dict
                if not isinstance(sent_result, dict):
                    sent_result = {}
            except json.JSONDecodeError:
                sent_result = {}

        # Ensure we have a dict
        if not isinstance(sent_result, dict):
            sent_result = {}

        sentiment_info = SentimentInfo(
            news_count=sent_result.get("news_count"),
            sentiment_score=sent_result.get("sentiment_score"),
            positive_news=sent_result.get("positive_news"),
            negative_news=sent_result.get("negative_news"),
            neutral_news=sent_result.get("neutral_news"),
        )

        return AnalysisComponentResult(
            component="sentiment",
            score=sent_result.get("sentiment_score", 50.0),
            raw_data=sent_result,
            sentiment_info=sentiment_info,
            reasoning=sent_result.get("analysis") or sent_result.get("reasoning"),
            confidence=sent_result.get("confidence"),
        )

    @staticmethod
    def _extract_technical_rule_based(tech_data: dict[str, Any]) -> AnalysisComponentResult:
        """Extract technical analysis component from rule-based output."""
        indicators = tech_data.get("indicators", {})
        components = tech_data.get("components", {})

        technical_indicators = TechnicalIndicators(
            rsi=indicators.get("rsi"),
            macd=indicators.get("macd"),
            macd_signal=indicators.get("macd_signal"),
            sma_20=indicators.get("sma_20"),
            sma_50=indicators.get("sma_50"),
            sma_200=indicators.get("sma_200"),
            volume_avg=indicators.get("volume_avg")
            or components.get("volume", {}).get("avg_volume"),
            atr=indicators.get("atr") or components.get("volatility", {}).get("atr"),
        )

        return AnalysisComponentResult(
            component="technical",
            score=tech_data.get("technical_score", 50.0),
            raw_data=tech_data,
            technical_indicators=technical_indicators,
            reasoning=tech_data.get("analysis"),
        )

    @staticmethod
    def _extract_fundamental_rule_based(fund_data: dict[str, Any]) -> AnalysisComponentResult:
        """Extract fundamental analysis component from rule-based output."""
        metrics = fund_data.get("metrics", {})
        analyst_ratings = fund_data.get("analyst_ratings", {})

        fundamental_metrics = FundamentalMetrics(
            pe_ratio=metrics.get("pe_ratio"),
            pb_ratio=metrics.get("pb_ratio"),
            ps_ratio=metrics.get("ps_ratio"),
            peg_ratio=metrics.get("peg_ratio"),
            ev_ebitda=metrics.get("ev_ebitda"),
            profit_margin=metrics.get("profit_margin"),
            operating_margin=metrics.get("operating_margin"),
            roe=metrics.get("roe"),
            roa=metrics.get("roa"),
            debt_to_equity=metrics.get("debt_to_equity"),
            current_ratio=metrics.get("current_ratio"),
            revenue_growth=metrics.get("revenue_growth"),
            earnings_growth=metrics.get("earnings_growth"),
        )

        analyst_info = None
        if analyst_ratings:
            analyst_info = AnalystInfo(
                num_analysts=analyst_ratings.get("num_analysts"),
                consensus_rating=analyst_ratings.get("consensus_rating"),
                strong_buy=analyst_ratings.get("strong_buy"),
                buy=analyst_ratings.get("buy"),
                hold=analyst_ratings.get("hold"),
                sell=analyst_ratings.get("sell"),
                strong_sell=analyst_ratings.get("strong_sell"),
                price_target=analyst_ratings.get("price_target"),
                price_target_high=analyst_ratings.get("price_target_high"),
                price_target_low=analyst_ratings.get("price_target_low"),
            )

        return AnalysisComponentResult(
            component="fundamental",
            score=fund_data.get("fundamental_score", 50.0),
            raw_data=fund_data,
            fundamental_metrics=fundamental_metrics,
            analyst_info=analyst_info,
            reasoning=fund_data.get("analysis"),
        )

    @staticmethod
    def _extract_sentiment_rule_based(sent_data: dict[str, Any]) -> AnalysisComponentResult:
        """Extract sentiment analysis component from rule-based output."""
        sentiment_info = SentimentInfo(
            news_count=sent_data.get("news_count"),
            sentiment_score=sent_data.get("sentiment_score"),
            positive_news=sent_data.get("positive_news"),
            negative_news=sent_data.get("negative_news"),
            neutral_news=sent_data.get("neutral_news"),
        )

        return AnalysisComponentResult(
            component="sentiment",
            score=sent_data.get("sentiment_score", 50.0),
            raw_data=sent_data,
            sentiment_info=sentiment_info,
            reasoning=sent_data.get("analysis"),
        )
