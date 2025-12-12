"""Scheduling utilities for automated analysis runs."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)


class RunLog:
    """Log of analysis runs for monitoring and troubleshooting."""

    def __init__(self, log_path: str | Path):
        """Initialize run log.

        Args:
            log_path: Path to store run logs
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Run log initialized: {log_path}")

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
            logger.debug(f"Run logged: {status} ({duration_seconds:.2f}s, {signal_count} signals)")

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

            logger.debug(f"Exported {exported_count} log entries to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            return False
