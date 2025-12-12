"""Token usage tracking and cost monitoring."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from src.config.schemas import TokenTrackerConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TokenUsage(BaseModel):
    """Token usage record."""

    timestamp: datetime = Field(default_factory=datetime.now)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    model: str
    cost_eur: float = Field(ge=0.0)
    success: bool = True


class DailyStats(BaseModel):
    """Daily token usage statistics."""

    date: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_eur: float = 0.0
    requests: int = 0


class TokenTracker:
    """Tracks token usage and costs across LLM API calls."""

    def __init__(
        self,
        config: TokenTrackerConfig,
        storage_dir: Optional[Path] = None,
    ):
        """Initialize token tracker.

        Args:
            config: Token tracking configuration
            storage_dir: Directory to store tracking data
        """
        self.config = config
        self.storage_dir = storage_dir or Path("data/tracking")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.daily_usage: list[TokenUsage] = []
        self._load_today_stats()

    def _load_today_stats(self) -> None:
        """Load today's statistics from file."""
        today = datetime.now().strftime("%Y-%m-%d")
        stats_file = self.storage_dir / f"tokens_{today}.json"

        if stats_file.exists():
            try:
                import json

                with open(stats_file) as f:
                    data = json.load(f)
                    self.daily_usage = [TokenUsage(**item) for item in data.get("usages", [])]
                    logger.debug(f"Loaded {len(self.daily_usage)} token usages from today")
            except Exception as e:
                logger.warning(f"Failed to load token tracking data: {e}")
                self.daily_usage = []

    def track(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        success: bool = True,
    ) -> float:
        """Track token usage and calculate cost.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            model: Model identifier
            success: Whether the request was successful

        Returns:
            Cost in EUR for this request

        Raises:
            ValueError: If usage exceeds daily limit and config requires it
        """
        # Calculate cost
        cost = self._calculate_cost(input_tokens, output_tokens)

        # Create usage record
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            cost_eur=cost,
            success=success,
        )

        self.daily_usage.append(usage)

        # Check limits
        daily_tokens = self.get_daily_tokens()
        daily_cost = self.get_daily_cost()

        if daily_tokens > self.config.daily_limit:
            logger.warning(
                f"Daily token limit exceeded: {daily_tokens} > {self.config.daily_limit}"
            )

        if daily_cost > 100:  # Warn at 100 EUR
            logger.warning(f"Daily cost getting high: €{daily_cost:.2f}")

        # Check warning threshold
        if daily_tokens > self.config.daily_limit * self.config.warn_on_daily_usage_percent:
            percent = int(self.config.warn_on_daily_usage_percent * 100)
            logger.warning(
                f"Daily token usage at {percent}% of limit: {daily_tokens}/{self.config.daily_limit}"
            )

        # Save tracking data
        self._save_tracking_data()

        return cost

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in EUR for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in EUR
        """
        input_cost = (input_tokens / 1000) * self.config.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * self.config.cost_per_1k_output_tokens
        return input_cost + output_cost

    def get_daily_tokens(self) -> int:
        """Get total tokens used today.

        Returns:
            Total token count (input + output)
        """
        return sum(u.input_tokens + u.output_tokens for u in self.daily_usage)

    def get_daily_cost(self) -> float:
        """Get total cost today in EUR.

        Returns:
            Total cost
        """
        return sum(u.cost_eur for u in self.daily_usage)

    def get_daily_stats(self) -> DailyStats:
        """Get today's statistics.

        Returns:
            Daily statistics
        """
        return DailyStats(
            date=datetime.now().strftime("%Y-%m-%d"),
            total_input_tokens=sum(u.input_tokens for u in self.daily_usage),
            total_output_tokens=sum(u.output_tokens for u in self.daily_usage),
            total_cost_eur=self.get_daily_cost(),
            requests=len([u for u in self.daily_usage if u.success]),
        )

    def get_monthly_stats(self) -> DailyStats:
        """Get monthly statistics.

        Returns:
            Monthly statistics aggregated
        """
        month_start = datetime.now().replace(day=1)
        month_usage = [u for u in self._load_month_history() if u.timestamp >= month_start]

        return DailyStats(
            date=datetime.now().strftime("%Y-%m"),
            total_input_tokens=sum(u.input_tokens for u in month_usage),
            total_output_tokens=sum(u.output_tokens for u in month_usage),
            total_cost_eur=sum(u.cost_eur for u in month_usage),
            requests=len([u for u in month_usage if u.success]),
        )

    def _load_month_history(self) -> list[TokenUsage]:
        """Load all token usage data for current month.

        Returns:
            List of token usage records
        """
        month_start = datetime.now().replace(day=1)
        all_usage = []

        # Load files from current month
        for i in range(32):
            check_date = month_start + timedelta(days=i)
            if check_date.month != month_start.month:
                break

            stats_file = self.storage_dir / f"tokens_{check_date.strftime('%Y-%m-%d')}.json"
            if stats_file.exists():
                try:
                    import json

                    with open(stats_file) as f:
                        data = json.load(f)
                        all_usage.extend([TokenUsage(**item) for item in data.get("usages", [])])
                except Exception as e:
                    logger.warning(f"Failed to load {stats_file}: {e}")

        return all_usage

    def _save_tracking_data(self) -> None:
        """Save today's tracking data to file."""
        today = datetime.now().strftime("%Y-%m-%d")
        stats_file = self.storage_dir / f"tokens_{today}.json"

        try:
            import json

            with open(stats_file, "w") as f:
                json.dump(
                    {
                        "date": today,
                        "usages": [u.model_dump() for u in self.daily_usage],
                    },
                    f,
                    default=str,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save tracking data: {e}")

    def reset_daily(self) -> None:
        """Reset daily tracking data (for new day)."""
        self.daily_usage = []
        logger.info("Daily token tracking reset")

    def log_summary(self) -> None:
        """Log daily summary of token usage and costs."""
        stats = self.get_daily_stats()
        monthly = self.get_monthly_stats()

        logger.info(
            f"Token usage - Daily: {stats.total_input_tokens + stats.total_output_tokens} "
            f"({stats.requests} requests, €{stats.total_cost_eur:.2f}) | "
            f"Monthly: {monthly.total_input_tokens + monthly.total_output_tokens} "
            f"(€{monthly.total_cost_eur:.2f})"
        )
