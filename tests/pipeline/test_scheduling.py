"""Tests for scheduling utilities."""

import pytest

from src.utils.scheduler import CronScheduler, RunLog


@pytest.mark.integration
class TestScheduling:
    """Test suite for scheduling utilities."""

    def test_cron_scheduler_initialization(self, tmp_path):
        """Test cron scheduler initialization."""
        scheduler = CronScheduler(tmp_path / "cron.json")
        assert scheduler.config_path == tmp_path / "cron.json"

    def test_daily_cron_expression(self, tmp_path):
        """Test daily cron expression generation."""
        scheduler = CronScheduler(tmp_path / "cron.json")
        cron_expr = scheduler.schedule_daily_run(
            "test_script.py",
            time_of_day="08:30",
        )

        assert cron_expr == "30 8 * * *"

    def test_weekly_cron_expression(self, tmp_path):
        """Test weekly cron expression generation."""
        scheduler = CronScheduler(tmp_path / "cron.json")
        cron_expr = scheduler.schedule_weekly_run(
            "test_script.py",
            day_of_week=1,
            time_of_day="09:00",
        )

        assert cron_expr == "0 9 * * 1"

    def test_run_log_initialization(self, tmp_path):
        """Test run log initialization."""
        log = RunLog(tmp_path / "runs.jsonl")
        assert log.log_path == tmp_path / "runs.jsonl"

    def test_run_log_entry(self, tmp_path):
        """Test logging a run entry."""
        log = RunLog(tmp_path / "runs.jsonl")

        log.log_run(
            success=True,
            duration_seconds=45.5,
            signal_count=10,
            metadata={"test": "data"},
        )

        assert log.log_path.exists()

    def test_run_statistics(self, tmp_path):
        """Test run statistics calculation."""
        log = RunLog(tmp_path / "runs.jsonl")

        log.log_run(success=True, duration_seconds=30, signal_count=5)
        log.log_run(success=True, duration_seconds=40, signal_count=8)
        log.log_run(success=False, duration_seconds=15, error_message="Test error")

        stats = log.get_run_statistics()

        assert stats["total_runs"] == 3
        assert stats["successful_runs"] == 2
        assert stats["failed_runs"] == 1
        assert stats["success_rate"] == pytest.approx(2 / 3)
        assert stats["total_signals_generated"] == 13
