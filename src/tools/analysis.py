"""Analysis tools for computing indicators and metrics."""

from typing import Any

import pandas as pd

from src.tools.base import BaseTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TechnicalIndicatorTool(BaseTool):
    """Tool for calculating technical indicators."""

    def __init__(self):
        """Initialize technical indicator tool."""
        super().__init__(
            name="TechnicalIndicator",
            description=(
                "Calculate technical indicators (SMA, RSI, MACD, ATR). "
                "Input: price data. "
                "Output: Indicator values and trend signals."
            ),
        )

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

            result = {
                "symbol": df.get("ticker", ["Unknown"])[0],
                "periods": len(df),
                "latest_price": df["close_price"].iloc[-1],
            }

            # Simple Moving Averages
            if len(df) >= 200:
                df["sma_20"] = df["close_price"].rolling(20).mean()
                df["sma_50"] = df["close_price"].rolling(50).mean()
                df["sma_200"] = df["close_price"].rolling(200).mean()

                result["sma_20"] = float(df["sma_20"].iloc[-1])
                result["sma_50"] = float(df["sma_50"].iloc[-1])
                result["sma_200"] = float(df["sma_200"].iloc[-1])

                # Golden cross detection
                if df["sma_50"].iloc[-1] > df["sma_200"].iloc[-1]:
                    result["trend"] = "bullish"
                else:
                    result["trend"] = "bearish"

            # RSI (Relative Strength Index)
            if len(df) >= 14:
                result["rsi"] = self._calculate_rsi(df["close_price"])

            # MACD
            if len(df) >= 26:
                macd_result = self._calculate_macd(df["close_price"])
                result["macd"] = macd_result

            # ATR (Average True Range)
            if len(df) >= 14:
                result["atr"] = self._calculate_atr(df)

            # Volume analysis
            avg_volume = df["volume"].tail(20).mean()
            current_volume = df["volume"].iloc[-1]
            result["volume_ratio"] = current_volume / avg_volume if avg_volume > 0 else 0

            return result

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {"error": str(e)}

    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index).

        Args:
            prices: Series of close prices
            period: Period for RSI calculation

        Returns:
            RSI value (0-100)
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

        Args:
            prices: Series of close prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Dictionary with MACD, Signal, and Histogram
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

        Args:
            df: DataFrame with high, low, close prices
            period: Period for ATR calculation

        Returns:
            ATR value
        """
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

            for article in articles:
                sentiment = article.get("sentiment", "neutral")
                score = article.get("sentiment_score", 0)

                if sentiment == "positive":
                    positive += 1
                elif sentiment == "negative":
                    negative += 1
                else:
                    neutral += 1

                total_score += score

            avg_sentiment = total_score / len(articles) if articles else 0

            return {
                "count": len(articles),
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "positive_pct": round(positive / len(articles) * 100, 2),
                "negative_pct": round(negative / len(articles) * 100, 2),
                "neutral_pct": round(neutral / len(articles) * 100, 2),
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
