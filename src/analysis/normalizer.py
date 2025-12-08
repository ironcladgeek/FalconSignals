"""Analysis result normalizer for converting agent outputs to unified structure."""

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

        With Pydantic structured output, agent results now contain validated models
        instead of unstructured markdown. This simplifies normalization significantly.

        Args:
            ticker: Stock ticker symbol
            technical_result: Dict with {"status": "success", "result": TechnicalAnalysisOutput}
            fundamental_result: Dict with {"status": "success", "result": FundamentalAnalysisOutput}
            sentiment_result: Dict with {"status": "success", "result": SentimentAnalysisOutput}
            synthesis_result: Dict with {"status": "success", "result": SignalSynthesisOutput}

        Returns:
            UnifiedAnalysisResult with all detailed metrics preserved
        """
        # Import here to avoid circular dependency issues
        from src.agents.output_models import (
            FundamentalAnalysisOutput,
            SentimentAnalysisOutput,
            SignalSynthesisOutput,
            TechnicalAnalysisOutput,
        )

        logger.debug(f"Normalizing LLM results for {ticker}")

        # Extract Pydantic models from result dicts
        # CrewAI returns CrewOutput objects with .pydantic attribute containing the model
        tech_model = AnalysisResultNormalizer._extract_pydantic_model(
            technical_result, TechnicalAnalysisOutput
        )
        fund_model = AnalysisResultNormalizer._extract_pydantic_model(
            fundamental_result, FundamentalAnalysisOutput
        )
        sent_model = AnalysisResultNormalizer._extract_pydantic_model(
            sentiment_result, SentimentAnalysisOutput
        )
        synth_model = AnalysisResultNormalizer._extract_pydantic_model(
            synthesis_result, SignalSynthesisOutput
        )

        # If structured output failed, fall back to markdown parsing
        if tech_model is None:
            logger.warning(
                f"Technical analysis returned non-Pydantic output for {ticker}, falling back"
            )
            tech_model = AnalysisResultNormalizer._parse_technical_markdown(technical_result)
        if fund_model is None:
            logger.warning(
                f"Fundamental analysis returned non-Pydantic output for {ticker}, falling back"
            )
            fund_model = AnalysisResultNormalizer._parse_fundamental_markdown(fundamental_result)
        if sent_model is None:
            logger.warning(
                f"Sentiment analysis returned non-Pydantic output for {ticker}, falling back"
            )
            sent_model = AnalysisResultNormalizer._parse_sentiment_markdown(sentiment_result)
        if synth_model is None:
            logger.warning(
                f"Signal synthesis returned non-Pydantic output for {ticker}, falling back"
            )
            synth_model = AnalysisResultNormalizer._parse_synthesis_markdown(synthesis_result)

        # Convert Pydantic models to component results
        technical = AnalysisResultNormalizer._tech_model_to_component(tech_model, synth_model)
        fundamental = AnalysisResultNormalizer._fund_model_to_component(fund_model, synth_model)
        sentiment = AnalysisResultNormalizer._sent_model_to_component(sent_model, synth_model)

        # Extract risk assessment from synthesis
        risk_assessment = RiskAssessment(
            level=synth_model.risk_level if synth_model else "medium",
            volatility=synth_model.volatility if synth_model else "normal",
            volatility_pct=2.0,
            liquidity="normal",
            concentration_risk=False,
            sector_risk=None,
            flags=synth_model.risk_factors if synth_model else [],
        )

        return UnifiedAnalysisResult(
            ticker=ticker,
            mode="llm",
            technical=technical,
            fundamental=fundamental,
            sentiment=sentiment,
            final_score=synth_model.final_score if synth_model else 50.0,
            recommendation=synth_model.recommendation if synth_model else "hold",
            confidence=synth_model.confidence if synth_model else 50.0,
            company_name=synth_model.company_name if synth_model else None,
            market=synth_model.market if synth_model else None,
            sector=synth_model.sector if synth_model else None,
            risk_assessment=risk_assessment,
            key_reasons=synth_model.key_reasons if synth_model else [],
            rationale=synth_model.rationale if synth_model else None,
            caveats=synth_model.caveats if synth_model else [],
            expected_return_min=synth_model.expected_return_min if synth_model else 0.0,
            expected_return_max=synth_model.expected_return_max if synth_model else 10.0,
            time_horizon=synth_model.time_horizon if synth_model else "3M",
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
    def _parse_llm_markdown_for_indicators(text: str) -> dict[str, Any]:
        """Parse LLM markdown text to extract technical indicators.

        LLM agents return unstructured markdown text. This method uses regex
        to extract key metrics that are mentioned in the text.
        """
        import re

        indicators = {}

        # Extract RSI - be flexible with formatting (value may be after bold markers, colons, etc.)
        # Matches: "RSI: 80.80", "**RSI Value:** 80.80", "RSI at 80.80", "RSI (14): 80.80"
        rsi_match = re.search(
            r"(?:\*\*)?\s*RSI\s*(?:\([\w\s]+\))?\s*(?:Value\s*)?(?:\*\*\s*)?(?:at|:)?\s*(?:\*\*)?\s*(\d+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if rsi_match:
            indicators["rsi"] = float(rsi_match.group(1))

        # Extract MACD - look for various patterns
        # Matches: "MACD Line: 8.36", "MACD: 8.36 / 5.52", "**MACD Line:** 8.36"
        macd_match = re.search(
            r"(?:\*\*)?\s*MACD\s+(?:Line\s*)?(?:\*\*\s*)?(?::)?\s*(?:\*\*)?\s*(\d+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if macd_match:
            indicators["macd"] = float(macd_match.group(1))

        # Also try to extract MACD signal line - handle bold markers before text
        macd_signal_match = re.search(
            r"(?:\*\*)?\s*(?:Signal|Signal\s+Line)\s*(?:\*\*\s*)?(?::)?\s*(?:\*\*)?\s*(\d+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if macd_signal_match:
            indicators["macd_signal"] = float(macd_signal_match.group(1))

        # Extract ATR - be flexible with formatting
        # Matches: "ATR: 6.59", "**ATR:** 6.59", "Average True Range (ATR): 6.59"
        atr_match = re.search(
            r"(?:\*\*)?\s*(?:Average\s+True\s+Range\s*)?\(?ATR\)?\s*(?:\*\*\s*)?(?:of|:)?\s*(?:\*\*)?\s*(\d+\.?\d*)",
            text,
            re.IGNORECASE,
        )
        if atr_match:
            indicators["atr"] = float(atr_match.group(1))

        # Extract volume ratio
        # Matches: "volume ratio of 0.84", "Volume Ratio: 0.84"
        vol_match = re.search(
            r"volume\s+ratio\s*(?:\*\*\s*)?(?:of|:)?\s*(\d+\.?\d*)", text, re.IGNORECASE
        )
        if vol_match:
            indicators["volume_ratio"] = float(vol_match.group(1))

        return indicators

    @staticmethod
    def _parse_llm_markdown_for_fundamentals(text: str) -> dict[str, Any]:
        """Parse LLM markdown text to extract fundamental metrics."""
        import re

        metrics = {}

        # Extract analyst consensus - try multiple formats
        # Format 1: "75% (15 of 20 analysts)" or "15 out of 20 analysts"
        analyst_match = re.search(
            r"(\d+)%.*?\((\d+)\s+(?:of|out of)\s+(\d+)\s+analysts", text, re.IGNORECASE
        )
        if analyst_match:
            metrics["analyst_consensus"] = {
                "bullish_pct": int(analyst_match.group(1)),
                "bullish_count": int(analyst_match.group(2)),
                "total_analysts": int(analyst_match.group(3)),
            }
        else:
            # Format 2: "Strong Buy: 4 analysts", "Buy: 11 analysts", "Total Analysts: 20"
            # Note: Use (?:\*\*)?\s* to handle optional bold markers
            total_match = re.search(
                r"(?:\*\*)?\s*Total(?:\s+Analysts)?(?:\*\*)?\s*:?\s*(\d+)", text, re.IGNORECASE
            )
            strong_buy_match = re.search(r"Strong\s+Buy(?:\*\*)?\s*:?\s*(\d+)", text, re.IGNORECASE)
            # For Buy, match "Buy:" but not "Strong Buy:"
            buy_match = re.search(
                r"\b(?:- )?Buy(?:\*\*)?\s*:?\s*(\d+)(?! analysts)", text, re.IGNORECASE
            )
            if buy_match:
                # Verify it's not part of "Strong Buy"
                match_start = buy_match.start()
                if match_start >= 7:
                    preceding = text[match_start - 7 : match_start]
                    if "Strong" in preceding:
                        buy_match = None

            hold_match = re.search(r"\b(?:- )?Hold(?:\*\*)?\s*:?\s*(\d+)", text, re.IGNORECASE)
            sell_match = re.search(
                r"\b(?:- )?Sell(?:\*\*)?\s*:?\s*(\d+)(?! analysts)", text, re.IGNORECASE
            )
            if sell_match:
                # Verify it's not part of "Strong Sell"
                match_start = sell_match.start()
                if match_start >= 7:
                    preceding = text[match_start - 7 : match_start]
                    if "Strong" in preceding:
                        sell_match = None

            if total_match:
                total = int(total_match.group(1))
                strong_buy = int(strong_buy_match.group(1)) if strong_buy_match else 0
                buy = int(buy_match.group(1)) if buy_match else 0
                hold = int(hold_match.group(1)) if hold_match else 0
                sell = int(sell_match.group(1)) if sell_match else 0
                bullish_count = strong_buy + buy

                metrics["analyst_consensus"] = {
                    "bullish_pct": int((bullish_count / total) * 100) if total > 0 else 0,
                    "bullish_count": bullish_count,
                    "total_analysts": total,
                }
                # Also store individual counts for metadata
                metrics["analyst_ratings"] = {
                    "strong_buy": strong_buy,
                    "buy": buy,
                    "hold": hold,
                    "sell": sell,
                }

        # Extract price (e.g., "$210.49" or "Price: $210.49")
        price_match = re.search(r"\$([0-9]+\.?[0-9]*)", text)
        if price_match:
            metrics["current_price"] = float(price_match.group(1))

        return metrics

    @staticmethod
    def _parse_llm_markdown_for_sentiment(text: str) -> dict[str, Any]:
        """Parse LLM markdown text to extract sentiment metrics."""
        import re

        metrics = {}

        # Extract sentiment distribution - multiple formats
        # Format 1: "Positive Articles: 11** (55%)"
        pos_match = re.search(
            r"Positive\s+Articles?(?:\*\*)?\s*:?\s*(\d+)(?:\*\*)?\s*\((\d+)%\)", text, re.IGNORECASE
        )
        if pos_match:
            metrics["positive_count"] = int(pos_match.group(1))
            metrics["positive_pct"] = int(pos_match.group(2))
        else:
            # Format 2: "Positive: 70% (7 out of 10)"
            pos_match2 = re.search(
                r"Positive.*?(\d+)%.*?\((\d+)\s+(?:out of|of)\s+(\d+)", text, re.IGNORECASE
            )
            if pos_match2:
                metrics["positive_pct"] = int(pos_match2.group(1))
                metrics["positive_count"] = int(pos_match2.group(2))
                total = int(pos_match2.group(3))
            else:
                # Format 3: "X positive news", "Y total articles"
                pos_count_match = re.search(
                    r"(\d+)\s+positive(?:\s+news|\s+articles)?", text, re.IGNORECASE
                )
                if pos_count_match:
                    metrics["positive_count"] = int(pos_count_match.group(1))

        # Extract negative count and percentage
        neg_match = re.search(
            r"Negative\s+Articles?(?:\*\*)?\s*:?\s*(\d+)(?:\*\*)?\s*\((\d+)%\)", text, re.IGNORECASE
        )
        if neg_match:
            metrics["negative_count"] = int(neg_match.group(1))
            metrics["negative_pct"] = int(neg_match.group(2))
        else:
            neg_match2 = re.search(r"Negative.*?(\d+)%", text, re.IGNORECASE)
            if neg_match2:
                metrics["negative_pct"] = int(neg_match2.group(1))

        # Extract neutral count
        neu_match = re.search(
            r"Neutral\s+Articles?(?:\*\*)?\s*:?\s*(\d+)(?:\*\*)?\s*\((\d+)%\)", text, re.IGNORECASE
        )
        if neu_match:
            metrics["neutral_count"] = int(neu_match.group(1))
            metrics["neutral_pct"] = int(neu_match.group(2))

        # Calculate total if we have counts
        if "positive_count" in metrics or "negative_count" in metrics or "neutral_count" in metrics:
            total = (
                metrics.get("positive_count", 0)
                + metrics.get("negative_count", 0)
                + metrics.get("neutral_count", 0)
            )
            if total > 0:
                metrics["total_articles"] = total

        # Calculate counts if we have total
        if "positive_count" in metrics and pos_match:
            total_articles = int(pos_match.group(3))
            metrics["total_articles"] = total_articles
            if "positive_pct" in metrics and "negative_pct" in metrics:
                metrics["neutral_pct"] = 100 - metrics["positive_pct"] - metrics["negative_pct"]
                metrics["negative_count"] = int(total_articles * metrics["negative_pct"] / 100)
                metrics["neutral_count"] = (
                    total_articles - metrics["positive_count"] - metrics["negative_count"]
                )

        return metrics

    @staticmethod
    def _extract_technical_llm(tech_result: dict[str, Any]) -> AnalysisComponentResult:
        """Extract technical analysis component from LLM output.

        Handles both Pydantic structured output and legacy markdown parsing.

        Args:
            tech_result: Technical analysis result (Pydantic model or dict)
        """
        from src.agents.output_models import TechnicalAnalysisOutput

        # Check if we have a Pydantic model
        result_data = tech_result.get("result", {})

        if isinstance(result_data, TechnicalAnalysisOutput):
            return AnalysisResultNormalizer._extract_from_technical_pydantic(result_data)
        elif hasattr(result_data, "pydantic") and result_data.pydantic:
            return AnalysisResultNormalizer._extract_from_technical_pydantic(result_data.pydantic)
        elif (
            isinstance(result_data, dict) and "pydantic" in result_data and result_data["pydantic"]
        ):
            return AnalysisResultNormalizer._extract_from_technical_pydantic(
                result_data["pydantic"]
            )

        # Fallback to markdown parsing
        # Handle CrewOutput objects and dict with 'raw' key
        original_text = ""
        if hasattr(tech_result, "raw"):
            tech_result = tech_result.raw
            original_text = tech_result if isinstance(tech_result, str) else ""
        elif isinstance(tech_result, dict) and "raw" in tech_result:
            # LLM agents return {"raw": "markdown", "pydantic": null, "json_dict": null}
            original_text = tech_result.get("raw", "")
            tech_result = {}  # Will parse from original_text instead
        else:
            original_text = tech_result if isinstance(tech_result, str) else ""

        # Convert string to dict
        if isinstance(tech_result, str):
            import json

            try:
                tech_result = json.loads(tech_result)
                # Ensure result is a dict
                if not isinstance(tech_result, dict):
                    tech_result = {}
            except json.JSONDecodeError:
                # Not JSON - will parse as markdown
                tech_result = {}

        # Ensure we have a dict
        if not isinstance(tech_result, dict):
            tech_result = {}

        # LLM technical agent returns detailed indicators in its output
        # Extract and structure them
        indicators_data = tech_result.get("indicators", {})
        components_data = tech_result.get("components", {})

        # If no structured data, parse from markdown (original text or fallback)
        if not indicators_data:
            text_to_parse = original_text or fallback_text
            if text_to_parse:
                logger.debug(
                    f"Parsing technical indicators from markdown (length: {len(text_to_parse)} chars)"
                )
                parsed_indicators = AnalysisResultNormalizer._parse_llm_markdown_for_indicators(
                    text_to_parse
                )
                logger.debug(f"Parsed indicators: {parsed_indicators}")
                indicators_data.update(parsed_indicators)
            else:
                logger.warning("No text available to parse technical indicators from")

        # Extract MACD values (handle both dict and float formats)
        macd_data = indicators_data.get("macd")
        if isinstance(macd_data, dict):
            macd_value = macd_data.get("line")
            macd_signal_value = macd_data.get("signal")
        else:
            macd_value = macd_data
            macd_signal_value = indicators_data.get("macd_signal")

        technical_indicators = TechnicalIndicators(
            rsi=indicators_data.get("rsi"),
            macd=macd_value,
            macd_signal=macd_signal_value,
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
        """Extract fundamental analysis component from LLM output.

        Handles both Pydantic structured output and legacy markdown parsing.
        """
        from src.agents.output_models import FundamentalAnalysisOutput

        # Check if we have a Pydantic model
        result_data = fund_result.get("result", {})

        if isinstance(result_data, FundamentalAnalysisOutput):
            return AnalysisResultNormalizer._extract_from_fundamental_pydantic(result_data)
        elif hasattr(result_data, "pydantic") and result_data.pydantic:
            return AnalysisResultNormalizer._extract_from_fundamental_pydantic(result_data.pydantic)
        elif (
            isinstance(result_data, dict) and "pydantic" in result_data and result_data["pydantic"]
        ):
            return AnalysisResultNormalizer._extract_from_fundamental_pydantic(
                result_data["pydantic"]
            )

        # Fallback to markdown parsing
        # Handle CrewOutput objects
        if hasattr(fund_result, "raw"):
            fund_result = fund_result.raw

        # Store original text for markdown parsing
        # Extract from dict if it has 'raw' key (LLM agent output format)
        original_text = ""
        if isinstance(fund_result, dict) and "raw" in fund_result:
            original_text = fund_result.get("raw", "")
            # Set fund_result to empty dict so we parse from markdown
            fund_result = {}
        elif isinstance(fund_result, str):
            original_text = fund_result
            fund_result = {}

        # Convert string to dict
        if isinstance(fund_result, str):
            import json

            try:
                fund_result = json.loads(fund_result)
                # Ensure result is a dict
                if not isinstance(fund_result, dict):
                    fund_result = {}
            except json.JSONDecodeError:
                # Not JSON - will parse as markdown
                fund_result = {}

        # Ensure we have a dict
        if not isinstance(fund_result, dict):
            fund_result = {}

        metrics_data = fund_result.get("metrics", {})
        analyst_data = fund_result.get("analyst_ratings", {})

        # If no structured data, parse from markdown
        parsed_fundamentals = {}
        if original_text and not metrics_data:
            logger.debug(
                f"Parsing fundamental metrics from markdown (length: {len(original_text)} chars)"
            )
            parsed_fundamentals = AnalysisResultNormalizer._parse_llm_markdown_for_fundamentals(
                original_text
            )
            logger.debug(f"Parsed fundamentals: {parsed_fundamentals}")
            if "analyst_consensus" in parsed_fundamentals:
                consensus = parsed_fundamentals["analyst_consensus"]
                analyst_data = {
                    "num_analysts": consensus.get("total_analysts"),
                    "consensus_rating": "buy" if consensus.get("bullish_pct", 0) >= 60 else "hold",
                }
                # Also get individual analyst ratings if available
                if "analyst_ratings" in parsed_fundamentals:
                    analyst_data.update(parsed_fundamentals["analyst_ratings"])
        elif not original_text:
            logger.warning("No text available to parse fundamental metrics from")

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
        """Extract sentiment analysis component from LLM output.

        Handles both Pydantic structured output and legacy markdown parsing.
        """
        from src.agents.output_models import SentimentAnalysisOutput

        # Check if we have a Pydantic model
        result_data = sent_result.get("result", {})

        if isinstance(result_data, SentimentAnalysisOutput):
            return AnalysisResultNormalizer._extract_from_sentiment_pydantic(result_data)
        elif hasattr(result_data, "pydantic") and result_data.pydantic:
            return AnalysisResultNormalizer._extract_from_sentiment_pydantic(result_data.pydantic)
        elif (
            isinstance(result_data, dict) and "pydantic" in result_data and result_data["pydantic"]
        ):
            return AnalysisResultNormalizer._extract_from_sentiment_pydantic(
                result_data["pydantic"]
            )

        # Fallback to markdown parsing
        # Handle CrewOutput objects
        if hasattr(sent_result, "raw"):
            sent_result = sent_result.raw

        # Store original text for markdown parsing
        # Extract from dict if it has 'raw' key (LLM agent output format)
        original_text = ""
        if isinstance(sent_result, dict) and "raw" in sent_result:
            original_text = sent_result.get("raw", "")
            # Set sent_result to empty dict so we parse from markdown
            sent_result = {}
        elif isinstance(sent_result, str):
            original_text = sent_result
            sent_result = {}

        # Convert string to dict
        if isinstance(sent_result, str):
            import json

            try:
                sent_result = json.loads(sent_result)
                # Ensure result is a dict
                if not isinstance(sent_result, dict):
                    sent_result = {}
            except json.JSONDecodeError:
                # Not JSON - will parse as markdown
                sent_result = {}

        # Ensure we have a dict
        if not isinstance(sent_result, dict):
            sent_result = {}

        # Parse markdown if no structured data
        parsed_sentiment = {}
        if original_text and not sent_result.get("news_count"):
            logger.debug(f"Parsing sentiment from markdown (length: {len(original_text)} chars)")
            parsed_sentiment = AnalysisResultNormalizer._parse_llm_markdown_for_sentiment(
                original_text
            )
            logger.debug(f"Parsed sentiment: {parsed_sentiment}")
        elif not original_text:
            logger.warning("No text available to parse sentiment from")

        # Calculate sentiment_score from distribution if not provided
        sentiment_score = sent_result.get("sentiment_score")
        if sentiment_score is None and parsed_sentiment:
            # Calculate from positive/negative percentages: (pos% - neg%) / 100
            pos_pct = parsed_sentiment.get("positive_pct", 0)
            neg_pct = parsed_sentiment.get("negative_pct", 0)
            sentiment_score = (pos_pct - neg_pct) / 100.0  # Range: -1 to 1

        sentiment_info = SentimentInfo(
            news_count=sent_result.get("news_count") or parsed_sentiment.get("total_articles"),
            sentiment_score=sentiment_score,
            positive_news=sent_result.get("positive_news")
            or parsed_sentiment.get("positive_count"),
            negative_news=sent_result.get("negative_news")
            or parsed_sentiment.get("negative_count"),
            neutral_news=sent_result.get("neutral_news") or parsed_sentiment.get("neutral_count"),
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

        # Extract MACD values (handle both dict and float formats)
        macd_data = indicators.get("macd")
        if isinstance(macd_data, dict):
            macd_value = macd_data.get("line")
            macd_signal_value = macd_data.get("signal")
        else:
            macd_value = macd_data
            macd_signal_value = indicators.get("macd_signal")

        technical_indicators = TechnicalIndicators(
            rsi=indicators.get("rsi"),
            macd=macd_value,
            macd_signal=macd_signal_value,
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
        # Extract raw sentiment score (-1 to 1) from sentiment_metrics
        sentiment_metrics = sent_data.get("sentiment_metrics", {})
        raw_sentiment_score = sentiment_metrics.get("avg_sentiment")  # -1 to 1

        sentiment_info = SentimentInfo(
            news_count=sent_data.get("news_count"),
            sentiment_score=raw_sentiment_score,  # -1 to 1 from sentiment_metrics
            positive_news=sent_data.get("positive_news"),
            negative_news=sent_data.get("negative_news"),
            neutral_news=sent_data.get("neutral_news"),
        )

        return AnalysisComponentResult(
            component="sentiment",
            score=sent_data.get("sentiment_score", 50.0),  # Component score 0-100
            raw_data=sent_data,
            sentiment_info=sentiment_info,
            reasoning=sent_data.get("analysis"),
        )

    # ==================== Pydantic Model Extraction Helpers ====================

    @staticmethod
    def _extract_pydantic_model(result: dict[str, Any], model_class: type):
        """Extract Pydantic model from agent result dict.

        Args:
            result: CrewOutput object OR dict with {"raw": str, "pydantic": dict, "json_dict": dict}
                    OR {"result": <PydanticModel>} (legacy structure)
            model_class: Expected Pydantic model class

        Returns:
            Pydantic model instance or None if not found
        """
        # Import here to avoid circular dependency

        if not result:
            return None

        # Direct Pydantic instance
        if isinstance(result, model_class):
            return result

        # CrewOutput object with .pydantic attribute (CrewAI returns this)
        if hasattr(result, "pydantic") and not isinstance(result, dict):
            pyd = result.pydantic
            if isinstance(pyd, model_class):
                return pyd
            # If it's a dict, instantiate the model
            if isinstance(pyd, dict):
                try:
                    return model_class(**pyd)
                except Exception as e:
                    logger.warning(
                        f"Failed to instantiate {model_class.__name__} from CrewOutput.pydantic dict: {e}"
                    )
                    return None

        # Dict with "pydantic" key at top level
        if isinstance(result, dict) and "pydantic" in result:
            pyd = result["pydantic"]
            if pyd is not None:
                # If it's already a Pydantic instance, return it
                if isinstance(pyd, model_class):
                    return pyd
                # If it's a dict, instantiate the model from the dict
                if isinstance(pyd, dict):
                    try:
                        return model_class(**pyd)
                    except Exception as e:
                        logger.warning(
                            f"Failed to instantiate {model_class.__name__} from dict: {e}"
                        )
                        return None

        # Legacy structure: {"result": <data>}
        if isinstance(result, dict) and "result" in result:
            result_data = result["result"]

            # Direct Pydantic instance
            if isinstance(result_data, model_class):
                return result_data

            # CrewAI structure with pydantic field
            if hasattr(result_data, "pydantic"):
                pyd = result_data.pydantic
                if isinstance(pyd, model_class):
                    return pyd
                if isinstance(pyd, dict):
                    try:
                        return model_class(**pyd)
                    except Exception as e:
                        logger.warning(
                            f"Failed to instantiate {model_class.__name__} from nested dict: {e}"
                        )
                        return None

        return None

    @staticmethod
    def _tech_model_to_component(
        tech: "TechnicalAnalysisOutput", synth: "SignalSynthesisOutput"
    ) -> AnalysisComponentResult:
        """Convert TechnicalAnalysisOutput Pydantic model to component result."""
        # Import here to avoid circular dependency

        if tech is None:
            return AnalysisComponentResult(
                component="technical",
                score=50.0,
                technical_indicators=None,
            )

        return AnalysisComponentResult(
            component="technical",
            score=synth.technical_score if synth else tech.technical_score,
            technical_indicators=TechnicalIndicators(
                rsi=tech.rsi,
                macd=tech.macd,
                macd_signal=tech.macd_signal,
                atr=tech.atr,
            ),
            reasoning=tech.reasoning,
            confidence=tech.technical_score,
        )

    @staticmethod
    def _fund_model_to_component(
        fund: "FundamentalAnalysisOutput", synth: "SignalSynthesisOutput"
    ) -> AnalysisComponentResult:
        """Convert FundamentalAnalysisOutput Pydantic model to component result."""
        # Import here to avoid circular dependency

        if fund is None:
            return AnalysisComponentResult(
                component="fundamental",
                score=50.0,
                fundamental_metrics=None,
                analyst_info=None,
            )

        # Create AnalystInfo if we have analyst data
        analyst_info = None
        if fund.total_analysts:
            # Calculate consensus rating
            consensus = "hold"
            if fund.consensus_rating:
                consensus = fund.consensus_rating.lower().replace(" ", "_")

            analyst_info = AnalystInfo(
                num_analysts=fund.total_analysts,
                consensus_rating=consensus,
                strong_buy=fund.strong_buy_count,
                buy=fund.buy_count,
                hold=fund.hold_count,
                sell=fund.sell_count,
                strong_sell=fund.strong_sell_count,
            )

        # Extract financial metrics from Pydantic model
        fundamental_metrics = None
        has_any_metric = any(
            [
                fund.pe_ratio,
                fund.pb_ratio,
                fund.ps_ratio,
                fund.peg_ratio,
                fund.ev_ebitda,
                fund.profit_margin,
                fund.operating_margin,
                fund.roe,
                fund.roa,
                fund.debt_to_equity,
                fund.current_ratio,
                fund.revenue_growth,
                fund.earnings_growth,
            ]
        )
        if has_any_metric:
            fundamental_metrics = FundamentalMetrics(
                pe_ratio=fund.pe_ratio,
                pb_ratio=fund.pb_ratio,
                ps_ratio=fund.ps_ratio,
                peg_ratio=fund.peg_ratio,
                ev_ebitda=fund.ev_ebitda,
                profit_margin=fund.profit_margin,
                operating_margin=fund.operating_margin,
                roe=fund.roe,
                roa=fund.roa,
                debt_to_equity=fund.debt_to_equity,
                current_ratio=fund.current_ratio,
                revenue_growth=fund.revenue_growth,
                earnings_growth=fund.earnings_growth,
            )

        return AnalysisComponentResult(
            component="fundamental",
            score=synth.fundamental_score if synth else fund.fundamental_score,
            fundamental_metrics=fundamental_metrics,
            analyst_info=analyst_info,
            reasoning=fund.reasoning,
            confidence=fund.fundamental_score,
        )

    @staticmethod
    def _sent_model_to_component(
        sent: "SentimentAnalysisOutput", synth: "SignalSynthesisOutput"
    ) -> AnalysisComponentResult:
        """Convert SentimentAnalysisOutput Pydantic model to component result."""
        # Import here to avoid circular dependency

        if sent is None:
            return AnalysisComponentResult(
                component="sentiment",
                score=50.0,
                sentiment_info=None,
            )

        sentiment_info = SentimentInfo(
            news_count=sent.total_articles,
            sentiment_score=sent.sentiment_score,
            positive_news=sent.positive_count,
            negative_news=sent.negative_count,
            neutral_news=sent.neutral_count,
        )

        return AnalysisComponentResult(
            component="sentiment",
            score=synth.sentiment_score if synth else sent.sentiment_strength_score,
            sentiment_info=sentiment_info,
            reasoning=sent.reasoning,
            confidence=sent.sentiment_strength_score,
        )

    # ==================== Markdown Parsing Fallbacks ====================

    @staticmethod
    def _parse_technical_markdown(result: dict[str, Any]) -> "TechnicalAnalysisOutput":
        """Parse technical analysis from markdown (fallback for non-Pydantic output)."""
        from src.agents.output_models import TechnicalAnalysisOutput

        # Extract raw text
        text = ""
        if isinstance(result, dict) and "result" in result:
            res = result["result"]
            if isinstance(res, dict) and "raw" in res:
                text = res["raw"]
            elif hasattr(res, "raw"):
                text = res.raw

        # Parse indicators from markdown
        indicators = AnalysisResultNormalizer._parse_llm_markdown_for_indicators(text)

        # Return minimal model with parsed data
        return TechnicalAnalysisOutput(
            rsi=indicators.get("rsi"),
            macd=indicators.get("macd"),
            macd_signal=indicators.get("macd_signal"),
            atr=indicators.get("atr"),
            trend_direction="neutral",
            trend_strength="moderate",
            momentum_status="neutral",
            technical_score=50,
            key_findings=["Parsed from markdown"],
            reasoning="Fallback parsing from unstructured output",
        )

    @staticmethod
    def _parse_fundamental_markdown(result: dict[str, Any]) -> "FundamentalAnalysisOutput":
        """Parse fundamental analysis from markdown (fallback for non-Pydantic output)."""
        from src.agents.output_models import FundamentalAnalysisOutput

        # Extract raw text
        text = ""
        if isinstance(result, dict) and "result" in result:
            res = result["result"]
            if isinstance(res, dict) and "raw" in res:
                text = res["raw"]
            elif hasattr(res, "raw"):
                text = res.raw

        # Parse fundamentals from markdown
        metrics = AnalysisResultNormalizer._parse_llm_markdown_for_fundamentals(text)
        analyst_data = metrics.get("analyst_ratings", {})

        return FundamentalAnalysisOutput(
            total_analysts=metrics.get("analyst_consensus", {}).get("total_analysts"),
            strong_buy_count=analyst_data.get("strong_buy"),
            buy_count=analyst_data.get("buy"),
            hold_count=analyst_data.get("hold"),
            sell_count=analyst_data.get("sell"),
            strong_sell_count=analyst_data.get("strong_sell"),
            consensus_rating="Hold",
            competitive_position="moderate",
            growth_outlook="moderate",
            valuation_assessment="fairly valued",
            fundamental_score=50,
            key_findings=["Parsed from markdown"],
            reasoning="Fallback parsing from unstructured output",
        )

    @staticmethod
    def _parse_sentiment_markdown(result: dict[str, Any]) -> "SentimentAnalysisOutput":
        """Parse sentiment analysis from markdown (fallback for non-Pydantic output)."""
        from src.agents.output_models import SentimentAnalysisOutput

        # Extract raw text
        text = ""
        if isinstance(result, dict) and "result" in result:
            res = result["result"]
            if isinstance(res, dict) and "raw" in res:
                text = res["raw"]
            elif hasattr(res, "raw"):
                text = res.raw

        # Parse sentiment from markdown
        metrics = AnalysisResultNormalizer._parse_llm_markdown_for_sentiment(text)

        return SentimentAnalysisOutput(
            total_articles=metrics.get("total_articles"),
            positive_count=metrics.get("positive_count"),
            negative_count=metrics.get("negative_count"),
            neutral_count=metrics.get("neutral_count"),
            overall_sentiment="neutral",
            sentiment_score=0.0,
            major_themes=["Parsed from markdown"],
            sentiment_strength_score=50,
            key_findings=["Parsed from markdown"],
            reasoning="Fallback parsing from unstructured output",
        )

    @staticmethod
    def _parse_synthesis_markdown(result: dict[str, Any]) -> "SignalSynthesisOutput":
        """Parse signal synthesis from markdown (fallback for non-Pydantic output)."""
        # Extract and parse JSON from markdown
        import json
        import re

        from src.agents.output_models import SignalSynthesisOutput

        synthesis_data = result.get("result", {})

        if isinstance(synthesis_data, dict) and "raw" in synthesis_data:
            text = synthesis_data["raw"]
            try:
                # Try to extract JSON from markdown code blocks
                text = text.strip()
                if text.startswith("```"):
                    text = re.sub(r"^```(?:json)?\n?", "", text)
                    text = re.sub(r"\n?```$", "", text)
                    text = text.strip()
                synthesis_data = json.loads(text)
            except json.JSONDecodeError:
                synthesis_data = {}

        if not isinstance(synthesis_data, dict):
            synthesis_data = {}

        # Extract scores
        scores = synthesis_data.get("scores", {})

        return SignalSynthesisOutput(
            technical_score=scores.get("technical", 50),
            fundamental_score=scores.get("fundamental", 50),
            sentiment_score=scores.get("sentiment", 50),
            final_score=synthesis_data.get("final_score", 50),
            recommendation=synthesis_data.get("recommendation", "hold"),
            confidence=synthesis_data.get("confidence", 50),
            key_reasons=synthesis_data.get("key_reasons", ["Parsed from markdown"]),
            rationale=synthesis_data.get("rationale", "Fallback parsing"),
            caveats=synthesis_data.get("caveats", []),
            risk_level="medium",
            volatility="normal",
            risk_factors=["Unknown - parsed from markdown"],
            expected_return_min=synthesis_data.get("expected_return_min", 0.0),
            expected_return_max=synthesis_data.get("expected_return_max", 10.0),
            time_horizon=synthesis_data.get("time_horizon", "3M"),
            company_name=synthesis_data.get("name"),
            sector=synthesis_data.get("sector"),
            market=synthesis_data.get("market"),
        )
