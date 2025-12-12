"""Filtering strategies for ticker selection before analysis.

This module provides different strategies for filtering tickers based on
market data patterns. Strategies are used to reduce the number of tickers
that undergo expensive analysis (especially LLM-based).
"""

from abc import ABC, abstractmethod
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class FilterStrategy(ABC):
    """Abstract base class for ticker filtering strategies."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize strategy with optional configuration.

        Args:
            config: Strategy-specific configuration parameters
        """
        self.config = config or {}

    @abstractmethod
    def filter(self, ticker: str, prices: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Filter a ticker based on price data.

        Args:
            ticker: Stock ticker symbol
            prices: List of price data points (sorted oldest to newest)

        Returns:
            Tuple of (should_include, reasons)
            - should_include: True if ticker passes filter
            - reasons: List of reasons for inclusion/exclusion
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for identification."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Strategy description for CLI help."""
        pass


class AnomalyStrategy(FilterStrategy):
    """Filter tickers based on price and volume anomalies.

    Detects:
    - Large daily/weekly price movements
    - Volume spikes
    - Price at new highs/lows
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize anomaly detection strategy.

        Config options:
            daily_change_threshold: Daily price change % to trigger (default: 5.0)
            weekly_change_threshold: Weekly price change % to trigger (default: 15.0)
            volume_spike_multiplier: Volume spike multiplier (default: 1.5)
            lookback_days_high_low: Days to check for highs/lows (default: 30)
        """
        super().__init__(config)
        self.daily_threshold = self.config.get("daily_change_threshold", 5.0)
        self.weekly_threshold = self.config.get("weekly_change_threshold", 15.0)
        self.volume_multiplier = self.config.get("volume_spike_multiplier", 1.5)
        self.lookback_days = self.config.get("lookback_days_high_low", 30)

    @property
    def name(self) -> str:
        return "anomaly"

    @property
    def description(self) -> str:
        return "Filter tickers with price/volume anomalies (large moves, spikes, extremes)"

    def filter(self, ticker: str, prices: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Detect anomalies in price data.

        Args:
            ticker: Stock ticker
            prices: List of price data points

        Returns:
            Tuple of (has_anomalies, anomaly_list)
        """
        if len(prices) < 5:
            return False, ["Insufficient price data"]

        anomalies = []

        # Get recent data points
        latest = prices[-1]
        prev_day = prices[-2]
        week_ago = prices[-5] if len(prices) >= 5 else prices[0]

        # Price change detection
        daily_change = (
            (latest["close_price"] - prev_day["close_price"]) / prev_day["close_price"] * 100
        )
        weekly_change = (
            (latest["close_price"] - week_ago["close_price"]) / week_ago["close_price"] * 100
        )

        if abs(daily_change) > self.daily_threshold:
            anomalies.append(f"Large daily move: {daily_change:+.2f}%")

        if abs(weekly_change) > self.weekly_threshold:
            anomalies.append(f"Large weekly move: {weekly_change:+.2f}%")

        # Volume anomaly
        avg_volume = sum(p["volume"] for p in prices[-5:]) / 5
        current_volume = latest["volume"]

        if current_volume > avg_volume * self.volume_multiplier:
            volume_ratio = current_volume / avg_volume
            anomalies.append(f"Volume spike: {volume_ratio:.1f}x average")

        # Price at new highs/lows
        lookback_window = min(self.lookback_days, len(prices))
        high_window = max(p["high_price"] for p in prices[-lookback_window:])
        low_window = min(p["low_price"] for p in prices[-lookback_window:])

        if latest["high_price"] >= high_window:
            anomalies.append(f"Trading at {lookback_window}-day high")

        if latest["low_price"] <= low_window:
            anomalies.append(f"Trading at {lookback_window}-day low")

        has_anomalies = len(anomalies) > 0
        return has_anomalies, anomalies


class VolumeStrategy(FilterStrategy):
    """Filter tickers based on volume patterns.

    Focuses on:
    - High volume activity
    - Volume trends (increasing/decreasing)
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize volume-based strategy.

        Config options:
            min_volume_ratio: Minimum volume ratio vs average (default: 1.2)
            volume_trend_days: Days to calculate volume trend (default: 10)
            min_trend_slope: Minimum trend slope % to trigger (default: 10.0)
        """
        super().__init__(config)
        self.min_volume_ratio = self.config.get("min_volume_ratio", 1.2)
        self.trend_days = self.config.get("volume_trend_days", 10)
        self.min_trend_slope = self.config.get("min_trend_slope", 10.0)

    @property
    def name(self) -> str:
        return "volume"

    @property
    def description(self) -> str:
        return "Filter tickers with significant volume activity and trends"

    def filter(self, ticker: str, prices: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Detect volume patterns.

        Args:
            ticker: Stock ticker
            prices: List of price data points

        Returns:
            Tuple of (has_volume_signal, reasons)
        """
        if len(prices) < 10:
            return False, ["Insufficient data for volume analysis"]

        reasons = []

        # Current volume vs average
        latest = prices[-1]
        avg_volume = sum(p["volume"] for p in prices[-20:]) / 20
        current_volume = latest["volume"]

        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        if volume_ratio >= self.min_volume_ratio:
            reasons.append(f"High volume: {volume_ratio:.1f}x average")

        # Volume trend (simple linear approximation)
        if len(prices) >= self.trend_days:
            recent_volumes = [p["volume"] for p in prices[-self.trend_days :]]
            avg_early = sum(recent_volumes[: self.trend_days // 2]) / (self.trend_days // 2)
            avg_late = sum(recent_volumes[self.trend_days // 2 :]) / (
                self.trend_days - self.trend_days // 2
            )

            if avg_early > 0:
                trend_change = (avg_late - avg_early) / avg_early * 100
                if abs(trend_change) >= self.min_trend_slope:
                    direction = "increasing" if trend_change > 0 else "decreasing"
                    reasons.append(f"Volume {direction}: {abs(trend_change):.1f}%")

        has_signal = len(reasons) > 0
        return has_signal, reasons


class MomentumStrategy(FilterStrategy):
    """Filter tickers based on price momentum.

    Detects:
    - Sustained upward/downward trends
    - Acceleration in price movement
    - Momentum strength
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize momentum-based strategy.

        Config options:
            min_consecutive_days: Minimum days of same direction (default: 3)
            min_total_change: Minimum total % change over period (default: 8.0)
            lookback_days: Days to analyze for momentum (default: 10)
        """
        super().__init__(config)
        self.min_consecutive_days = self.config.get("min_consecutive_days", 3)
        self.min_total_change = self.config.get("min_total_change", 8.0)
        self.lookback_days = self.config.get("lookback_days", 10)

    @property
    def name(self) -> str:
        return "momentum"

    @property
    def description(self) -> str:
        return "Filter tickers with strong price momentum (sustained trends)"

    def filter(self, ticker: str, prices: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Detect momentum patterns.

        Args:
            ticker: Stock ticker
            prices: List of price data points

        Returns:
            Tuple of (has_momentum, reasons)
        """
        if len(prices) < self.lookback_days:
            return False, ["Insufficient data for momentum analysis"]

        reasons = []
        recent_prices = prices[-self.lookback_days :]

        # Calculate consecutive days in same direction
        up_days = 0
        down_days = 0
        max_up_streak = 0
        max_down_streak = 0

        for i in range(1, len(recent_prices)):
            if recent_prices[i]["close_price"] > recent_prices[i - 1]["close_price"]:
                up_days += 1
                down_days = 0
                max_up_streak = max(max_up_streak, up_days)
            elif recent_prices[i]["close_price"] < recent_prices[i - 1]["close_price"]:
                down_days += 1
                up_days = 0
                max_down_streak = max(max_down_streak, down_days)

        # Total price change over period
        start_price = recent_prices[0]["close_price"]
        end_price = recent_prices[-1]["close_price"]
        total_change = (end_price - start_price) / start_price * 100

        if max_up_streak >= self.min_consecutive_days and total_change >= self.min_total_change:
            reasons.append(
                f"Strong upward momentum: {max_up_streak} consecutive up days, "
                f"{total_change:+.2f}% total"
            )

        if (
            max_down_streak >= self.min_consecutive_days
            and abs(total_change) >= self.min_total_change
        ):
            reasons.append(
                f"Strong downward momentum: {max_down_streak} consecutive down days, "
                f"{total_change:+.2f}% total"
            )

        has_momentum = len(reasons) > 0
        return has_momentum, reasons


class VolatilityStrategy(FilterStrategy):
    """Filter tickers based on volatility patterns.

    Detects:
    - High volatility (large intraday swings)
    - Increasing/decreasing volatility trends
    - Volatility breakouts
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize volatility-based strategy.

        Config options:
            min_avg_daily_range: Minimum average daily range % (default: 3.0)
            volatility_multiplier: Multiplier for volatility spike (default: 1.5)
            lookback_days: Days to analyze volatility (default: 20)
        """
        super().__init__(config)
        self.min_avg_daily_range = self.config.get("min_avg_daily_range", 3.0)
        self.volatility_multiplier = self.config.get("volatility_multiplier", 1.5)
        self.lookback_days = self.config.get("lookback_days", 20)

    @property
    def name(self) -> str:
        return "volatility"

    @property
    def description(self) -> str:
        return "Filter tickers with high volatility or volatility breakouts"

    def filter(self, ticker: str, prices: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Detect volatility patterns.

        Args:
            ticker: Stock ticker
            prices: List of price data points

        Returns:
            Tuple of (has_volatility_signal, reasons)
        """
        if len(prices) < self.lookback_days:
            return False, ["Insufficient data for volatility analysis"]

        reasons = []
        recent_prices = prices[-self.lookback_days :]

        # Calculate daily ranges (high - low) as % of close
        daily_ranges = [
            (p["high_price"] - p["low_price"]) / p["close_price"] * 100 for p in recent_prices
        ]

        avg_daily_range = sum(daily_ranges) / len(daily_ranges)
        latest_range = daily_ranges[-1]

        # High average volatility
        if avg_daily_range >= self.min_avg_daily_range:
            reasons.append(f"High average volatility: {avg_daily_range:.2f}% daily range")

        # Volatility spike
        if latest_range > avg_daily_range * self.volatility_multiplier:
            reasons.append(
                f"Volatility spike: {latest_range:.2f}% range "
                f"({latest_range / avg_daily_range:.1f}x average)"
            )

        # Increasing volatility trend
        if len(daily_ranges) >= 10:
            early_avg = sum(daily_ranges[:10]) / 10
            late_avg = sum(daily_ranges[-10:]) / 10
            if late_avg > early_avg * 1.3:  # 30% increase
                reasons.append(
                    f"Increasing volatility: {late_avg / early_avg:.1f}x vs earlier period"
                )

        has_signal = len(reasons) > 0
        return has_signal, reasons


class BreakoutStrategy(FilterStrategy):
    """Filter tickers showing breakout patterns.

    Detects:
    - Price breaking above resistance levels
    - Price breaking below support levels
    - Volume confirmation of breakouts
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize breakout detection strategy.

        Config options:
            lookback_days: Days to identify support/resistance (default: 30)
            breakout_threshold: % above/below level for breakout (default: 2.0)
            min_volume_ratio: Min volume ratio for confirmation (default: 1.3)
        """
        super().__init__(config)
        self.lookback_days = self.config.get("lookback_days", 30)
        self.breakout_threshold = self.config.get("breakout_threshold", 2.0)
        self.min_volume_ratio = self.config.get("min_volume_ratio", 1.3)

    @property
    def name(self) -> str:
        return "breakout"

    @property
    def description(self) -> str:
        return "Filter tickers breaking out of support/resistance levels"

    def filter(self, ticker: str, prices: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Detect breakout patterns.

        Args:
            ticker: Stock ticker
            prices: List of price data points

        Returns:
            Tuple of (has_breakout, reasons)
        """
        if len(prices) < self.lookback_days:
            return False, ["Insufficient data for breakout analysis"]

        reasons = []
        lookback_window = prices[-self.lookback_days : -1]  # Exclude latest
        latest = prices[-1]

        # Calculate resistance (max high) and support (min low)
        resistance = max(p["high_price"] for p in lookback_window)
        support = min(p["low_price"] for p in lookback_window)

        # Average volume for confirmation
        avg_volume = sum(p["volume"] for p in prices[-20:]) / 20
        current_volume = latest["volume"]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        # Breakout above resistance
        breakout_price = resistance * (1 + self.breakout_threshold / 100)
        if latest["close_price"] >= breakout_price:
            volume_confirmed = volume_ratio >= self.min_volume_ratio
            confirmation = " (volume confirmed)" if volume_confirmed else " (low volume)"
            reasons.append(
                f"Resistance breakout: ${latest['close_price']:.2f} > "
                f"${resistance:.2f}{confirmation}"
            )

        # Breakdown below support
        breakdown_price = support * (1 - self.breakout_threshold / 100)
        if latest["close_price"] <= breakdown_price:
            volume_confirmed = volume_ratio >= self.min_volume_ratio
            confirmation = " (volume confirmed)" if volume_confirmed else " (low volume)"
            reasons.append(
                f"Support breakdown: ${latest['close_price']:.2f} < ${support:.2f}{confirmation}"
            )

        has_breakout = len(reasons) > 0
        return has_breakout, reasons


class GapStrategy(FilterStrategy):
    """Filter tickers with price gaps.

    Detects:
    - Gap ups (open significantly higher than previous close)
    - Gap downs (open significantly lower than previous close)
    - Large gaps that may reverse or continue
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize gap detection strategy.

        Config options:
            min_gap_percent: Minimum gap size as % (default: 3.0)
            lookback_days: Days to check for gaps (default: 5)
        """
        super().__init__(config)
        self.min_gap_percent = self.config.get("min_gap_percent", 3.0)
        self.lookback_days = self.config.get("lookback_days", 5)

    @property
    def name(self) -> str:
        return "gap"

    @property
    def description(self) -> str:
        return "Filter tickers with significant price gaps (gap up/down)"

    def filter(self, ticker: str, prices: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Detect price gaps.

        Args:
            ticker: Stock ticker
            prices: List of price data points

        Returns:
            Tuple of (has_gap, reasons)
        """
        if len(prices) < 2:
            return False, ["Insufficient data for gap analysis"]

        reasons = []
        check_window = min(self.lookback_days, len(prices) - 1)

        for i in range(-1, -check_window - 1, -1):
            current = prices[i]
            previous = prices[i - 1]

            # Gap calculation: (open - previous_close) / previous_close * 100
            gap_percent = (
                (current["open_price"] - previous["close_price"]) / previous["close_price"] * 100
            )

            if abs(gap_percent) >= self.min_gap_percent:
                direction = "up" if gap_percent > 0 else "down"
                days_ago = abs(i) - 1
                time_ref = "today" if days_ago == 0 else f"{days_ago} days ago"
                reasons.append(f"Gap {direction} {time_ref}: {gap_percent:+.2f}%")

        has_gap = len(reasons) > 0
        return has_gap, reasons


class AllStrategy(FilterStrategy):
    """Pass-through strategy that includes all tickers.

    Useful for:
    - Testing
    - Small ticker lists where filtering isn't needed
    - Full market analysis regardless of anomalies
    """

    @property
    def name(self) -> str:
        return "all"

    @property
    def description(self) -> str:
        return "Include all tickers without filtering (no cost optimization)"

    def filter(self, ticker: str, prices: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Include all tickers without filtering.

        Args:
            ticker: Stock ticker
            prices: List of price data points (unused)

        Returns:
            Always returns (True, ["All tickers included"])
        """
        return True, ["All tickers included"]


# Registry of available strategies
STRATEGY_REGISTRY: dict[str, type[FilterStrategy]] = {
    "anomaly": AnomalyStrategy,
    "volume": VolumeStrategy,
    "momentum": MomentumStrategy,
    "volatility": VolatilityStrategy,
    "breakout": BreakoutStrategy,
    "gap": GapStrategy,
    "all": AllStrategy,
}


def get_strategy(strategy_name: str, config: dict[str, Any] | None = None) -> FilterStrategy:
    """Get a filtering strategy by name.

    Args:
        strategy_name: Name of the strategy ("anomaly", "volume", "all")
        config: Optional strategy-specific configuration

    Returns:
        FilterStrategy instance

    Raises:
        ValueError: If strategy_name is not recognized
    """
    strategy_class = STRATEGY_REGISTRY.get(strategy_name.lower())
    if not strategy_class:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(f"Unknown filtering strategy: {strategy_name}. Available: {available}")

    return strategy_class(config)


def list_strategies() -> list[tuple[str, str]]:
    """List all available strategies with descriptions.

    Returns:
        List of (name, description) tuples
    """
    return [(name, cls(None).description) for name, cls in STRATEGY_REGISTRY.items()]
