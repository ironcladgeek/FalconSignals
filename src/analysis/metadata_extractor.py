"""Extract metadata from analysis results for enhanced recommendations.

This module provides functions to extract technical indicators, fundamental metrics,
analyst information, and sentiment data from analysis results and convert them into
structured metadata models for storage and display.
"""

from typing import Any

from src.analysis.models import (
    AnalysisMetadata,
    AnalystInfo,
    FundamentalMetrics,
    SentimentInfo,
    TechnicalIndicators,
    UnifiedAnalysisResult,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


def extract_technical_indicators(analysis_data: dict[str, Any]) -> TechnicalIndicators | None:
    """Extract technical indicators from analysis data.

    Args:
        analysis_data: Technical analysis section from analysis results

    Returns:
        TechnicalIndicators model or None if no data available
    """
    try:
        tech_data = analysis_data.get("technical", {})
        if not tech_data:
            return None

        # Extract indicators from nested structure
        indicators = tech_data.get("indicators", {})
        components = tech_data.get("components", {})

        return TechnicalIndicators(
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
    except Exception as e:
        logger.warning(f"Failed to extract technical indicators: {e}")
        return None


def extract_fundamental_metrics(analysis_data: dict[str, Any]) -> FundamentalMetrics | None:
    """Extract fundamental metrics from analysis data.

    Args:
        analysis_data: Fundamental analysis section from analysis results

    Returns:
        FundamentalMetrics model or None if no data available
    """
    try:
        fund_data = analysis_data.get("fundamental", {})
        if not fund_data:
            return None

        # Extract metrics from nested structure
        metrics = fund_data.get("metrics", {})
        valuation = metrics.get("valuation", {})
        profitability = metrics.get("profitability", {})
        financial_health = metrics.get("financial_health", {})
        growth = metrics.get("growth", {})

        return FundamentalMetrics(
            pe_ratio=valuation.get("trailing_pe") or valuation.get("pe_ratio"),
            pb_ratio=valuation.get("price_to_book") or valuation.get("pb_ratio"),
            ps_ratio=valuation.get("price_to_sales") or valuation.get("ps_ratio"),
            peg_ratio=valuation.get("peg_ratio"),
            ev_ebitda=valuation.get("enterprise_to_ebitda") or valuation.get("ev_ebitda"),
            profit_margin=profitability.get("profit_margin"),
            operating_margin=profitability.get("operating_margin"),
            roe=profitability.get("return_on_equity") or profitability.get("roe"),
            roa=profitability.get("return_on_assets") or profitability.get("roa"),
            debt_to_equity=financial_health.get("debt_to_equity"),
            current_ratio=financial_health.get("current_ratio"),
            revenue_growth=growth.get("revenue_growth"),
            earnings_growth=growth.get("earnings_growth"),
        )
    except Exception as e:
        logger.warning(f"Failed to extract fundamental metrics: {e}")
        return None


def extract_analyst_info(analysis_data: dict[str, Any]) -> AnalystInfo | None:
    """Extract analyst information from analysis data.

    Args:
        analysis_data: Analysis data containing analyst information

    Returns:
        AnalystInfo model or None if no data available
    """
    try:
        # Check both fundamental and sentiment sections for analyst data
        fund_data = analysis_data.get("fundamental", {})
        sent_data = analysis_data.get("sentiment", {})

        analyst_data = (
            fund_data.get("analyst_data", {})
            or sent_data.get("analyst_data", {})
            or analysis_data.get("analyst_data", {})
        )

        if not analyst_data:
            return None

        # Calculate consensus rating
        consensus = None
        total = analyst_data.get("total_analysts", 0)
        if total > 0:
            strong_buy = analyst_data.get("strong_buy", 0)
            buy = analyst_data.get("buy", 0)
            hold = analyst_data.get("hold", 0)
            sell = analyst_data.get("sell", 0)

            # Determine consensus based on majority
            max_count = max(strong_buy, buy, hold, sell)
            if max_count == strong_buy:
                consensus = "strong_buy"
            elif max_count == buy:
                consensus = "buy"
            elif max_count == hold:
                consensus = "hold"
            elif max_count == sell:
                consensus = "sell"

        return AnalystInfo(
            num_analysts=analyst_data.get("total_analysts"),
            consensus_rating=consensus or analyst_data.get("consensus"),
            strong_buy=analyst_data.get("strong_buy"),
            buy=analyst_data.get("buy"),
            hold=analyst_data.get("hold"),
            sell=analyst_data.get("sell"),
            strong_sell=analyst_data.get("strong_sell"),
            price_target=analyst_data.get("price_target"),
            price_target_high=analyst_data.get("price_target_high"),
            price_target_low=analyst_data.get("price_target_low"),
        )
    except Exception as e:
        logger.warning(f"Failed to extract analyst info: {e}")
        return None


def extract_sentiment_info(analysis_data: dict[str, Any]) -> SentimentInfo | None:
    """Extract sentiment information from analysis data.

    Args:
        analysis_data: Sentiment analysis section from analysis results

    Returns:
        SentimentInfo model or None if no data available
    """
    try:
        sent_data = analysis_data.get("sentiment", {})
        if not sent_data:
            return None

        news_data = sent_data.get("news", {})

        return SentimentInfo(
            news_count=sent_data.get("news_count") or news_data.get("count"),
            sentiment_score=sent_data.get("sentiment_score"),
            positive_news=sent_data.get("positive_news") or news_data.get("positive"),
            negative_news=sent_data.get("negative_news") or news_data.get("negative"),
            neutral_news=sent_data.get("neutral_news") or news_data.get("neutral"),
        )
    except Exception as e:
        logger.warning(f"Failed to extract sentiment info: {e}")
        return None


def extract_metadata_from_unified_result(
    result: UnifiedAnalysisResult,
) -> AnalysisMetadata | None:
    """Extract metadata from UnifiedAnalysisResult (NEW unified approach).

    This is the new, simplified metadata extraction that works with the
    unified analysis result structure used by both LLM and rule-based modes.

    Args:
        result: UnifiedAnalysisResult with structured component data

    Returns:
        AnalysisMetadata model or None if no data available
    """
    try:
        logger.debug(
            f"Extracting metadata from unified result for {result.ticker} ({result.mode} mode)"
        )

        # Extract from structured components (already normalized)
        technical_indicators = result.technical.technical_indicators
        fundamental_metrics = result.fundamental.fundamental_metrics
        analyst_info = result.fundamental.analyst_info
        sentiment_info = result.sentiment.sentiment_info

        logger.debug(
            f"Metadata extraction: tech={technical_indicators is not None}, "
            f"fund={fundamental_metrics is not None}, "
            f"analyst={analyst_info is not None}, "
            f"sentiment={sentiment_info is not None}"
        )

        # Only create metadata if at least one component has data
        if not any([technical_indicators, fundamental_metrics, analyst_info, sentiment_info]):
            logger.debug("No metadata components available")
            return None

        return AnalysisMetadata(
            technical_indicators=technical_indicators,
            fundamental_metrics=fundamental_metrics,
            analyst_info=analyst_info,
            sentiment_info=sentiment_info,
        )
    except Exception as e:
        logger.warning(f"Failed to extract metadata from unified result: {e}")
        return None


def extract_analysis_metadata(analysis: dict[str, Any]) -> AnalysisMetadata | None:
    """Extract complete analysis metadata from analysis results (LEGACY).

    This function is kept for backward compatibility during migration.
    New code should use extract_metadata_from_unified_result() instead.

    Args:
        analysis: Complete analysis result dictionary

    Returns:
        AnalysisMetadata model or None if no data available
    """
    try:
        analysis_data = analysis.get("analysis", {})
        if not analysis_data:
            logger.info("⚠️  No 'analysis' key found in results")
            logger.info(f"Available keys: {list(analysis.keys())}")
            return None

        logger.info(f"✓ Analysis data keys: {list(analysis_data.keys())}")

        # Extract all components
        technical_indicators = extract_technical_indicators(analysis_data)
        fundamental_metrics = extract_fundamental_metrics(analysis_data)
        analyst_info = extract_analyst_info(analysis_data)
        sentiment_info = extract_sentiment_info(analysis_data)

        logger.info(
            f"Metadata extraction: tech={technical_indicators is not None}, "
            f"fund={fundamental_metrics is not None}, "
            f"analyst={analyst_info is not None}, "
            f"sentiment={sentiment_info is not None}"
        )

        # Only create metadata if at least one component has data
        if not any([technical_indicators, fundamental_metrics, analyst_info, sentiment_info]):
            logger.debug("No metadata components extracted")
            return None

        return AnalysisMetadata(
            technical_indicators=technical_indicators,
            fundamental_metrics=fundamental_metrics,
            analyst_info=analyst_info,
            sentiment_info=sentiment_info,
        )
    except Exception as e:
        logger.warning(f"Failed to extract analysis metadata: {e}")
        return None
