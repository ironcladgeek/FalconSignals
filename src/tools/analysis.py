"""Analysis tools for computing indicators and metrics."""

from typing import Any, Optional

import pandas as pd

from src.analysis.technical_indicators import ConfigurableTechnicalAnalyzer
from src.config.schemas import TechnicalIndicatorsConfig
from src.tools.base import BaseTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TechnicalIndicatorTool(BaseTool):
    """Tool for calculating technical indicators using pandas-ta.

    Uses the ConfigurableTechnicalAnalyzer for battle-tested indicator calculations
    with configuration-driven indicator selection.
    """

    def __init__(self, config: Optional[TechnicalIndicatorsConfig] = None):
        """Initialize technical indicator tool.

        Args:
            config: Technical indicators configuration. If None, uses defaults from
                    the global config or built-in defaults.
        """
        super().__init__(
            name="TechnicalIndicator",
            description=(
                "Calculate technical indicators using pandas-ta library. "
                "Input: price data. "
                "Output: Indicator values and trend signals."
            ),
        )

        # Try to get config from global config if not provided
        if config is None:
            try:
                from src.config import get_config

                global_config = get_config()
                config = global_config.analysis.technical_indicators
            except Exception:
                config = TechnicalIndicatorsConfig()

        self._analyzer = ConfigurableTechnicalAnalyzer(config)

    def run(self, prices: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate technical indicators from price data.

        Args:
            prices: List of price dictionaries with OHLCV data

        Returns:
            Dictionary with calculated indicators
        """
        try:
            if not prices:
                return {"error": "No price data provided"}

            # Convert to DataFrame
            df = pd.DataFrame(prices)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            # Get ticker symbol if available
            ticker = "Unknown"
            if "ticker" in df.columns:
                ticker = df["ticker"].iloc[0]

            # Use configurable analyzer
            results = self._analyzer.calculate_indicators(df)

            if "error" in results:
                return results

            # Format output for backward compatibility
            output = {
                "symbol": ticker,
                "periods": results.get("periods"),
                "latest_price": results.get("latest_price"),
            }

            # Extract key indicators for backward compatibility
            indicators = results.get("indicators", {})

            # SMAs
            for sma_key in ["sma_20", "sma_50", "sma_200"]:
                if sma_key in indicators:
                    output[sma_key] = indicators[sma_key].get("value")

            # RSI (check both 'rsi' and 'rsi_14')
            rsi_data = indicators.get("rsi") or indicators.get("rsi_14")
            if rsi_data:
                output["rsi"] = rsi_data.get("value")

            # MACD
            if "macd" in indicators:
                output["macd"] = indicators["macd"]

            # ATR
            atr_data = indicators.get("atr") or indicators.get("atr_14")
            if atr_data:
                output["atr"] = atr_data.get("value")

            # Bollinger Bands (check both 'bbands' and 'bbands_20')
            bbands_data = indicators.get("bbands") or indicators.get("bbands_20")
            if bbands_data:
                output["bbands"] = bbands_data

            # Trend
            trend = results.get("trend", {})
            output["trend"] = trend.get("direction", "neutral")
            output["trend_signals"] = trend.get("signals", [])

            # Volume ratio
            vol = results.get("volume_analysis", {})
            if "ratio" in vol:
                output["volume_ratio"] = vol["ratio"]

            # Include full results for advanced usage
            output["full_analysis"] = results

            return output

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {"error": str(e)}

    def get_summary(self, prices: list[dict[str, Any]]) -> dict[str, Any]:
        """Get simplified indicator summary suitable for reports.

        Args:
            prices: List of price dictionaries with OHLCV data

        Returns:
            Simplified summary dictionary
        """
        full_results = self.run(prices)
        if "error" in full_results:
            return full_results

        if "full_analysis" in full_results:
            return self._analyzer.get_indicator_summary(full_results["full_analysis"])

        return full_results

    # Legacy methods preserved for backward compatibility
    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index).

        DEPRECATED: Use ConfigurableTechnicalAnalyzer instead.
        Kept for backward compatibility.
        """
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)

        avg_gain = gains.rolling(period).mean()
        avg_loss = losses.rolling(period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1])

    @staticmethod
    def _calculate_macd(
        prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence).

        DEPRECATED: Use ConfigurableTechnicalAnalyzer instead.
        Kept for backward compatibility.
        """
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        return {
            "line": float(macd_line.iloc[-1]),
            "signal": float(signal_line.iloc[-1]),
            "histogram": float(histogram.iloc[-1]),
        }

    @staticmethod
    def _calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
        """Calculate ATR (Average True Range).

        DEPRECATED: Use ConfigurableTechnicalAnalyzer instead.
        Kept for backward compatibility.
        """
        df = df.copy()
        df["tr1"] = df["high_price"] - df["low_price"]
        df["tr2"] = abs(df["high_price"] - df["close_price"].shift(1))
        df["tr3"] = abs(df["low_price"] - df["close_price"].shift(1))

        df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)
        atr = df["tr"].rolling(period).mean()

        return float(atr.iloc[-1])


class SentimentAnalyzerTool(BaseTool):
    """Tool for analyzing sentiment from news."""

    def __init__(self):
        """Initialize sentiment analyzer."""
        super().__init__(
            name="SentimentAnalyzer",
            description=(
                "Score news sentiment and importance. "
                "Input: news articles. "
                "Output: Sentiment scores and aggregated metrics."
            ),
        )

    def run(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze sentiment from articles.

        Args:
            articles: List of news article dictionaries

        Returns:
            Dictionary with sentiment metrics
        """
        try:
            if not articles:
                return {
                    "count": 0,
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "avg_sentiment": 0,
                }

            positive = 0
            negative = 0
            neutral = 0
            total_score = 0
            scored_count = 0

            for article in articles:
                sentiment = article.get("sentiment")
                score = article.get("sentiment_score")

                # Only count articles that have sentiment data
                if sentiment:
                    if sentiment == "positive":
                        positive += 1
                    elif sentiment == "negative":
                        negative += 1
                    else:
                        neutral += 1

                if score is not None:
                    total_score += score
                    scored_count += 1

            # If no sentiment data is available, return neutral
            if positive + negative + neutral == 0:
                return {
                    "count": len(articles),
                    "positive": 0,
                    "negative": 0,
                    "neutral": len(articles),
                    "positive_pct": 0.0,
                    "negative_pct": 0.0,
                    "neutral_pct": 100.0,
                    "avg_sentiment": 0.0,
                    "sentiment_direction": "neutral",
                    "note": "No sentiment data available from provider. LLM analysis needed.",
                }

            total_categorized = positive + negative + neutral
            avg_sentiment = total_score / scored_count if scored_count > 0 else 0

            return {
                "count": len(articles),
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "positive_pct": round(positive / total_categorized * 100, 2),
                "negative_pct": round(negative / total_categorized * 100, 2),
                "neutral_pct": round(neutral / total_categorized * 100, 2),
                "avg_sentiment": round(avg_sentiment, 3),
                "sentiment_direction": (
                    "positive"
                    if avg_sentiment > 0.1
                    else ("negative" if avg_sentiment < -0.1 else "neutral")
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"error": str(e)}
