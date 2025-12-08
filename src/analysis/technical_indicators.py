"""Configurable technical indicator calculation using pandas-ta.

This module provides a flexible, configuration-driven approach to calculating
technical indicators using the pandas-ta library.
"""

from typing import Any, Optional

import pandas as pd

from src.config.schemas import IndicatorConfig, TechnicalIndicatorsConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import pandas_ta, fallback to manual calculations if not available
try:
    import pandas_ta as ta

    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logger.warning("pandas-ta not installed, using fallback calculations")


class ConfigurableTechnicalAnalyzer:
    """Technical indicator calculator using pandas-ta with configuration.

    Uses pandas-ta library for accurate, battle-tested indicator calculations.
    Falls back to manual calculations if pandas-ta is not available.
    """

    def __init__(self, config: Optional[TechnicalIndicatorsConfig] = None):
        """Initialize the technical analyzer.

        Args:
            config: Technical indicators configuration. Uses defaults if not provided.
        """
        self.config = config or TechnicalIndicatorsConfig()
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that configured indicators are supported by pandas-ta."""
        if not PANDAS_TA_AVAILABLE or not self.config.use_pandas_ta:
            return

        supported_indicators = self._get_supported_indicators()
        for ind_config in self.config.indicators:
            if ind_config.enabled and ind_config.name not in supported_indicators:
                logger.warning(
                    f"Indicator '{ind_config.name}' not found in pandas-ta. "
                    f"Available indicators: {list(supported_indicators)[:20]}..."
                )

    def _get_supported_indicators(self) -> set[str]:
        """Get set of indicator names supported by pandas-ta."""
        if not PANDAS_TA_AVAILABLE:
            return set()

        # Get all indicator functions from pandas-ta
        supported = set()
        for attr in dir(ta):
            if not attr.startswith("_") and callable(getattr(ta, attr, None)):
                supported.add(attr)
        return supported

    def calculate_indicators(
        self,
        df: pd.DataFrame,
        close_col: str = "close",
        high_col: str = "high",
        low_col: str = "low",
        volume_col: str = "volume",
    ) -> dict[str, Any]:
        """Calculate all enabled indicators from configuration.

        Args:
            df: DataFrame with price data
            close_col: Name of close price column
            high_col: Name of high price column
            low_col: Name of low price column
            volume_col: Name of volume column

        Returns:
            Dictionary with indicator results
        """
        if df.empty:
            return {"error": "No price data provided"}

        if len(df) < self.config.min_periods_required:
            return {
                "error": f"Insufficient data: {len(df)} periods, "
                f"need {self.config.min_periods_required}"
            }

        # Normalize column names
        df = self._normalize_columns(df, close_col, high_col, low_col, volume_col)

        results = {
            "periods": len(df),
            "latest_price": float(df["close"].iloc[-1]),
            "indicators": {},
        }

        # Calculate each enabled indicator
        for ind_config in self.config.indicators:
            if not ind_config.enabled:
                continue

            try:
                indicator_result = self._calculate_single_indicator(df, ind_config)
                if indicator_result is not None:
                    # Create unique key for indicators with same name but different params
                    key = self._make_indicator_key(ind_config)
                    results["indicators"][key] = indicator_result
            except Exception as e:
                logger.warning(f"Error calculating {ind_config.name}: {e}")
                results["indicators"][ind_config.name] = {"error": str(e)}

        # Add trend analysis
        results["trend"] = self._analyze_trend(df, results["indicators"])

        # Add volume analysis
        results["volume_analysis"] = self._analyze_volume(df)

        return results

    def _normalize_columns(
        self,
        df: pd.DataFrame,
        close_col: str,
        high_col: str,
        low_col: str,
        volume_col: str,
    ) -> pd.DataFrame:
        """Normalize DataFrame column names."""
        df = df.copy()

        # Map common column name variations
        column_mapping = {
            close_col: "close",
            high_col: "high",
            low_col: "low",
            volume_col: "volume",
            "close_price": "close",
            "high_price": "high",
            "low_price": "low",
            "open_price": "open",
        }

        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df[new_name] = df[old_name]

        return df

    def _make_indicator_key(self, ind_config: IndicatorConfig) -> str:
        """Create unique key for an indicator based on name and params."""
        if "length" in ind_config.params:
            return f"{ind_config.name}_{ind_config.params['length']}"
        return ind_config.name

    def _calculate_single_indicator(
        self,
        df: pd.DataFrame,
        ind_config: IndicatorConfig,
    ) -> Optional[dict[str, Any]]:
        """Calculate a single indicator using pandas-ta or fallback.

        Args:
            df: DataFrame with normalized price data
            ind_config: Indicator configuration

        Returns:
            Dictionary with indicator values or None if calculation failed
        """
        if self.config.use_pandas_ta and PANDAS_TA_AVAILABLE:
            return self._calculate_with_pandas_ta(df, ind_config)
        else:
            return self._calculate_fallback(df, ind_config)

    def _calculate_with_pandas_ta(
        self,
        df: pd.DataFrame,
        ind_config: IndicatorConfig,
    ) -> Optional[dict[str, Any]]:
        """Calculate indicator using pandas-ta library."""
        name = ind_config.name.lower()
        params = ind_config.params

        try:
            if name == "rsi":
                result = ta.rsi(df["close"], length=params.get("length", 14))
                if result is not None and not result.empty:
                    return {"value": float(result.iloc[-1])}

            elif name == "macd":
                result = ta.macd(
                    df["close"],
                    fast=params.get("fast", 12),
                    slow=params.get("slow", 26),
                    signal=params.get("signal", 9),
                )
                if result is not None and not result.empty:
                    # MACD returns a DataFrame with multiple columns
                    macd_col = [c for c in result.columns if "MACD_" in c and "h" not in c.lower()][
                        0
                    ]
                    signal_col = [c for c in result.columns if "MACDs_" in c][0]
                    hist_col = [c for c in result.columns if "MACDh_" in c][0]
                    return {
                        "line": float(result[macd_col].iloc[-1]),
                        "signal": float(result[signal_col].iloc[-1]),
                        "histogram": float(result[hist_col].iloc[-1]),
                    }

            elif name == "bbands":
                result = ta.bbands(
                    df["close"],
                    length=params.get("length", 20),
                    std=params.get("std", 2.0),
                )
                if result is not None and not result.empty:
                    lower_col = [c for c in result.columns if "BBL_" in c][0]
                    mid_col = [c for c in result.columns if "BBM_" in c][0]
                    upper_col = [c for c in result.columns if "BBU_" in c][0]
                    band_width_col = [c for c in result.columns if "BBB_" in c]
                    band_pct_col = [c for c in result.columns if "BBP_" in c]

                    res = {
                        "lower": float(result[lower_col].iloc[-1]),
                        "middle": float(result[mid_col].iloc[-1]),
                        "upper": float(result[upper_col].iloc[-1]),
                    }
                    if band_width_col:
                        res["bandwidth"] = float(result[band_width_col[0]].iloc[-1])
                    if band_pct_col:
                        res["percent_b"] = float(result[band_pct_col[0]].iloc[-1])
                    return res

            elif name == "atr":
                result = ta.atr(
                    df["high"],
                    df["low"],
                    df["close"],
                    length=params.get("length", 14),
                )
                if result is not None and not result.empty:
                    return {"value": float(result.iloc[-1])}

            elif name == "sma":
                result = ta.sma(df["close"], length=params.get("length", 20))
                if result is not None and not result.empty:
                    return {"value": float(result.iloc[-1])}

            elif name == "ema":
                result = ta.ema(df["close"], length=params.get("length", 20))
                if result is not None and not result.empty:
                    return {"value": float(result.iloc[-1])}

            elif name == "adx":
                result = ta.adx(
                    df["high"],
                    df["low"],
                    df["close"],
                    length=params.get("length", 14),
                )
                if result is not None and not result.empty:
                    adx_col = [c for c in result.columns if "ADX_" in c][0]
                    dmp_col = [c for c in result.columns if "DMP_" in c][0]
                    dmn_col = [c for c in result.columns if "DMN_" in c][0]
                    return {
                        "adx": float(result[adx_col].iloc[-1]),
                        "dmp": float(result[dmp_col].iloc[-1]),
                        "dmn": float(result[dmn_col].iloc[-1]),
                    }

            elif name == "stoch":
                result = ta.stoch(
                    df["high"],
                    df["low"],
                    df["close"],
                    k=params.get("k", 14),
                    d=params.get("d", 3),
                )
                if result is not None and not result.empty:
                    k_col = [c for c in result.columns if "STOCHk_" in c][0]
                    d_col = [c for c in result.columns if "STOCHd_" in c][0]
                    return {
                        "k": float(result[k_col].iloc[-1]),
                        "d": float(result[d_col].iloc[-1]),
                    }

            elif name == "ichimoku":
                result = ta.ichimoku(
                    df["high"],
                    df["low"],
                    df["close"],
                    tenkan=params.get("tenkan", 9),
                    kijun=params.get("kijun", 26),
                    senkou=params.get("senkou", 52),
                )
                if result is not None and isinstance(result, tuple) and len(result) == 2:
                    # Ichimoku returns (df, span_b_periods)
                    ichimoku_df = result[0]
                    if ichimoku_df is not None and not ichimoku_df.empty:
                        # Extract all Ichimoku components
                        # Column names: ISA_9 (tenkan), ISB_26 (kijun), ITS_9 (chikou),
                        # IKS_26 (senkou_a), ICS_26 (senkou_b)
                        components = {}
                        last_row = ichimoku_df.iloc[-1]

                        for col in ichimoku_df.columns:
                            value = last_row[col]
                            # Skip NaN values (insufficient data)
                            if pd.isna(value):
                                continue

                            col_lower = col.lower()
                            if (
                                col.startswith("ISA_") or "isa_" in col_lower
                            ):  # Tenkan-sen (conversion line)
                                components["tenkan"] = float(value)
                            elif (
                                col.startswith("ISB_") or "isb_" in col_lower
                            ):  # Kijun-sen (base line)
                                components["kijun"] = float(value)
                            elif (
                                col.startswith("ITS_") or "its_" in col_lower
                            ):  # Chikou Span (lagging span)
                                components["chikou"] = float(value)
                            elif (
                                col.startswith("IKS_") or "iks_" in col_lower
                            ):  # Senkou Span A (leading span A)
                                components["senkou_a"] = float(value)
                            elif (
                                col.startswith("ICS_") or "ics_" in col_lower
                            ):  # Senkou Span B (leading span B)
                                components["senkou_b"] = float(value)

                        return components if components else None

            else:
                # Try to call indicator dynamically
                func = getattr(ta, name, None)
                if func is not None:
                    result = func(df["close"], **params)
                    if result is not None:
                        if isinstance(result, pd.DataFrame):
                            return {col: float(result[col].iloc[-1]) for col in result.columns}
                        elif isinstance(result, pd.Series):
                            return {"value": float(result.iloc[-1])}

        except Exception as e:
            logger.debug(f"pandas-ta error for {name}: {e}")
            return None

        return None

    def _calculate_fallback(
        self,
        df: pd.DataFrame,
        ind_config: IndicatorConfig,
    ) -> Optional[dict[str, Any]]:
        """Calculate indicator using manual implementations (fallback)."""
        name = ind_config.name.lower()
        params = ind_config.params

        try:
            if name == "rsi":
                return {"value": self._manual_rsi(df["close"], params.get("length", 14))}

            elif name == "macd":
                return self._manual_macd(
                    df["close"],
                    params.get("fast", 12),
                    params.get("slow", 26),
                    params.get("signal", 9),
                )

            elif name == "sma":
                length = params.get("length", 20)
                sma = df["close"].rolling(length).mean()
                if not sma.empty and not pd.isna(sma.iloc[-1]):
                    return {"value": float(sma.iloc[-1])}

            elif name == "ema":
                length = params.get("length", 20)
                ema = df["close"].ewm(span=length).mean()
                if not ema.empty:
                    return {"value": float(ema.iloc[-1])}

            elif name == "atr":
                return {"value": self._manual_atr(df, params.get("length", 14))}

        except Exception as e:
            logger.debug(f"Fallback calculation error for {name}: {e}")
            return None

        return None

    def _manual_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI manually."""
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)

        avg_gain = gains.rolling(period).mean()
        avg_loss = losses.rolling(period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1])

    def _manual_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> dict[str, float]:
        """Calculate MACD manually."""
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

    def _manual_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate ATR manually."""
        tr1 = df["high"] - df["low"]
        tr2 = abs(df["high"] - df["close"].shift(1))
        tr3 = abs(df["low"] - df["close"].shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()

        return float(atr.iloc[-1])

    def _analyze_trend(self, df: pd.DataFrame, indicators: dict) -> dict[str, Any]:
        """Analyze overall trend based on calculated indicators."""
        trend = {"direction": "neutral", "strength": "moderate", "signals": []}

        # Check SMA crossovers
        sma_50 = indicators.get("sma_50", {}).get("value")
        sma_200 = indicators.get("sma_200", {}).get("value")
        if sma_50 and sma_200:
            if sma_50 > sma_200:
                trend["direction"] = "bullish"
                trend["signals"].append("Golden Cross (SMA50 > SMA200)")
            else:
                trend["direction"] = "bearish"
                trend["signals"].append("Death Cross (SMA50 < SMA200)")

        # Check RSI levels
        rsi = indicators.get("rsi", {}).get("value")
        if rsi:
            if rsi > 70:
                trend["signals"].append(f"RSI overbought ({rsi:.1f})")
            elif rsi < 30:
                trend["signals"].append(f"RSI oversold ({rsi:.1f})")

        # Check MACD
        macd = indicators.get("macd", {})
        if macd.get("histogram"):
            if macd["histogram"] > 0:
                trend["signals"].append("MACD bullish")
            else:
                trend["signals"].append("MACD bearish")

        # Determine strength
        bullish_signals = sum(
            1 for s in trend["signals"] if "bullish" in s.lower() or "golden" in s.lower()
        )
        bearish_signals = sum(
            1 for s in trend["signals"] if "bearish" in s.lower() or "death" in s.lower()
        )

        if bullish_signals >= 2 or bearish_signals >= 2:
            trend["strength"] = "strong"
        elif bullish_signals == 0 and bearish_signals == 0:
            trend["strength"] = "weak"

        return trend

    def _analyze_volume(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze volume patterns."""
        if "volume" not in df.columns:
            return {"error": "Volume data not available"}

        avg_volume_20 = df["volume"].tail(20).mean()
        current_volume = df["volume"].iloc[-1]

        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 0

        return {
            "current": int(current_volume),
            "avg_20": int(avg_volume_20),
            "ratio": round(volume_ratio, 2),
            "status": ("high" if volume_ratio > 1.5 else "low" if volume_ratio < 0.5 else "normal"),
        }

    def get_indicator_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        """Create a simplified summary of technical indicators.

        Args:
            results: Full indicator results from calculate_indicators

        Returns:
            Simplified summary suitable for reports
        """
        if "error" in results:
            return results

        indicators = results.get("indicators", {})
        summary = {
            "latest_price": results.get("latest_price"),
            "trend": results.get("trend", {}).get("direction", "neutral"),
            "trend_strength": results.get("trend", {}).get("strength", "moderate"),
        }

        # Extract key values
        if "rsi" in indicators:
            summary["rsi"] = indicators["rsi"].get("value")

        if "macd" in indicators:
            summary["macd_histogram"] = indicators["macd"].get("histogram")

        if "atr" in indicators or "atr_14" in indicators:
            atr_data = indicators.get("atr") or indicators.get("atr_14")
            summary["atr"] = atr_data.get("value")

        # Get moving averages
        for key in ["sma_20", "sma_50", "sma_200"]:
            if key in indicators:
                summary[key] = indicators[key].get("value")

        # Volume ratio
        vol = results.get("volume_analysis", {})
        if "ratio" in vol:
            summary["volume_ratio"] = vol["ratio"]

        return summary
