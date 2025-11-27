"""Scheduling utilities for automated analysis runs."""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ScheduleConfig:
    """Configuration for scheduled analysis runs."""

    def __init__(
        self,
        frequency: str = "daily",
        time_of_day: str = "08:00",
        timezone: str = "UTC",
        max_retries: int = 3,
        retry_interval_minutes: int = 30,
    ):
        """Initialize schedule configuration.

        Args:
            frequency: Frequency of runs (daily, weekly, monthly)
            time_of_day: Time to run in HH:MM format
            timezone: Timezone for scheduling
            max_retries: Maximum retry attempts if run fails
            retry_interval_minutes: Minutes between retries
        """
        self.frequency = frequency
        self.time_of_day = time_of_day
        self.timezone = timezone
        self.max_retries = max_retries
        self.retry_interval_minutes = retry_interval_minutes

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "frequency": self.frequency,
            "time_of_day": self.time_of_day,
            "timezone": self.timezone,
            "max_retries": self.max_retries,
            "retry_interval_minutes": self.retry_interval_minutes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleConfig":
        """Create from dictionary."""
        return cls(**data)


class CronScheduler:
    """Cron-based scheduler configuration."""

    def __init__(self, config_path: str | Path):
        """Initialize cron scheduler.

        Args:
            config_path: Path to store cron configuration
        """
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Cron scheduler initialized: {config_path}")

    def schedule_daily_run(
        self,
        script_path: str | Path,
        time_of_day: str = "08:00",
        timezone: str = "UTC",
    ) -> str:
        """Generate cron expression for daily run.

        Args:
            script_path: Path to script to run
            time_of_day: Time in HH:MM format
            timezone: Timezone

        Returns:
            Cron expression
        """
        try:
            hour, minute = map(int, time_of_day.split(":"))
            cron_expr = f"{minute} {hour} * * *"
            logger.info(f"Daily cron expression: {cron_expr} ({timezone})")
            return cron_expr
        except (ValueError, AttributeError) as e:
            logger.error(f"Invalid time format: {e}")
            return "0 8 * * *"  # Default 08:00

    def schedule_weekly_run(
        self,
        script_path: str | Path,
        day_of_week: int = 1,
        time_of_day: str = "08:00",
    ) -> str:
        """Generate cron expression for weekly run.

        Args:
            script_path: Path to script to run
            day_of_week: Day of week (0=Sunday, 1=Monday, etc.)
            time_of_day: Time in HH:MM format

        Returns:
            Cron expression
        """
        try:
            hour, minute = map(int, time_of_day.split(":"))
            cron_expr = f"{minute} {hour} * * {day_of_week}"
            logger.info(f"Weekly cron expression: {cron_expr}")
            return cron_expr
        except (ValueError, AttributeError) as e:
            logger.error(f"Invalid time format: {e}")
            return "0 8 * * 1"  # Default Monday 08:00

    def generate_install_command(
        self,
        script_path: str | Path,
        cron_expr: str,
        email: str | None = None,
    ) -> str:
        """Generate command to install cron job.

        Args:
            script_path: Path to script
            cron_expr: Cron expression
            email: Optional email for notifications

        Returns:
            Installation command
        """
        script_path = Path(script_path).resolve()

        # Create wrapper script that logs output
        log_file = script_path.parent / "cron_runs.log"
        wrapper_cmd = f"cd {script_path.parent} && python -m {script_path.stem} >> {log_file} 2>&1"

        cron_job = f"{cron_expr} {wrapper_cmd}"

        if email:
            cron_job = f"MAILTO={email}\n{cron_job}"

        # Command to add to crontab
        install_cmd = f'(crontab -l 2>/dev/null; echo "{cron_job}") | crontab -'

        logger.debug(f"Install command: {install_cmd}")
        return install_cmd

    def install_cron_job(
        self,
        script_path: str | Path,
        cron_expr: str,
        email: str | None = None,
    ) -> bool:
        """Attempt to install cron job.

        Args:
            script_path: Path to script
            cron_expr: Cron expression
            email: Optional email for notifications

        Returns:
            True if installation succeeded
        """
        try:
            cmd = self.generate_install_command(script_path, cron_expr, email)
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info(f"Cron job installed: {cron_expr}")
                return True
            else:
                logger.error(f"Cron installation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Cron installation timed out")
            return False
        except Exception as e:
            logger.error(f"Cron installation error: {e}")
            return False

    def list_cron_jobs(self) -> list[str]:
        """List currently installed cron jobs.

        Returns:
            List of cron job expressions
        """
        try:
            result = subprocess.run(
                "crontab -l",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return [
                    line.strip()
                    for line in result.stdout.split("\n")
                    if line.strip() and not line.startswith("#")
                ]
            else:
                logger.warning("No cron jobs found or crontab not available")
                return []

        except Exception as e:
            logger.error(f"Error listing cron jobs: {e}")
            return []

    def remove_cron_job(self, cron_expr: str) -> bool:
        """Remove a cron job.

        Args:
            cron_expr: Cron expression to remove

        Returns:
            True if removal succeeded
        """
        try:
            jobs = self.list_cron_jobs()
            remaining_jobs = [j for j in jobs if cron_expr not in j]

            if len(remaining_jobs) == len(jobs):
                logger.warning(f"Cron job not found: {cron_expr}")
                return False

            # Reinstall without the removed job
            crontab_content = "\n".join(remaining_jobs)
            result = subprocess.run(
                "crontab -",
                input=crontab_content,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info(f"Cron job removed: {cron_expr}")
                return True
            else:
                logger.error(f"Cron removal failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error removing cron job: {e}")
            return False


class RunLog:
    """Log of analysis runs for monitoring and troubleshooting."""

    def __init__(self, log_path: str | Path):
        """Initialize run log.

        Args:
            log_path: Path to store run logs
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Run log initialized: {log_path}")

    def log_run(
        self,
        success: bool,
        duration_seconds: float,
        signal_count: int = 0,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Log an analysis run.

        Args:
            success: Whether run succeeded
            duration_seconds: Duration of run
            signal_count: Number of signals generated
            error_message: Error message if failed
            metadata: Additional metadata
        """
        run_entry = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration_seconds": round(duration_seconds, 2),
            "signal_count": signal_count,
            "error_message": error_message,
            "metadata": metadata or {},
        }

        try:
            # Append to log file (JSONL format)
            with open(self.log_path, "a") as f:
                f.write(json.dumps(run_entry) + "\n")

            status = "SUCCESS" if success else "FAILED"
            logger.info(f"Run logged: {status} ({duration_seconds:.2f}s, {signal_count} signals)")

        except Exception as e:
            logger.error(f"Error logging run: {e}")

    def get_run_statistics(self) -> dict:
        """Get statistics from run logs.

        Returns:
            Dictionary with run statistics
        """
        try:
            runs = []
            if self.log_path.exists():
                with open(self.log_path, "r") as f:
                    for line in f:
                        if line.strip():
                            runs.append(json.loads(line))

            if not runs:
                return {}

            successful_runs = [r for r in runs if r.get("success")]
            failed_runs = [r for r in runs if not r.get("success")]

            avg_duration = (
                sum(r.get("duration_seconds", 0) for r in successful_runs) / len(successful_runs)
                if successful_runs
                else 0
            )

            total_signals = sum(r.get("signal_count", 0) for r in successful_runs)

            return {
                "total_runs": len(runs),
                "successful_runs": len(successful_runs),
                "failed_runs": len(failed_runs),
                "success_rate": len(successful_runs) / len(runs) if runs else 0,
                "average_duration_seconds": round(avg_duration, 2),
                "total_signals_generated": total_signals,
                "last_run": runs[-1].get("timestamp") if runs else None,
            }

        except Exception as e:
            logger.error(f"Error getting run statistics: {e}")
            return {}

    def export_logs(self, export_path: str | Path, days: int = 7) -> bool:
        """Export logs from last N days.

        Args:
            export_path: Path to export logs to
            days: Number of days to include

        Returns:
            True if export succeeded
        """
        try:
            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)

            cutoff_time = datetime.now() - timedelta(days=days)
            exported_count = 0

            with open(export_path, "w") as out_f:
                if self.log_path.exists():
                    with open(self.log_path, "r") as in_f:
                        for line in in_f:
                            if line.strip():
                                entry = json.loads(line)
                                entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                                if entry_time >= cutoff_time:
                                    out_f.write(line)
                                    exported_count += 1

            logger.info(f"Exported {exported_count} log entries to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            return False
