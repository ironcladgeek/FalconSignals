"""Unit tests for the scheduler module."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.utils.scheduler import RunLog


class TestRunLog:
    """Test suite for RunLog class."""

    @pytest.fixture
    def temp_log_path(self):
        """Create temporary log file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "run_log.jsonl"

    @pytest.fixture
    def run_log(self, temp_log_path):
        """Create RunLog instance with temporary path."""
        return RunLog(temp_log_path)

    def test_initialization_creates_parent_directories(self, temp_log_path):
        """Test that RunLog creates parent directories."""
        nested_path = temp_log_path.parent / "nested" / "dir" / "log.jsonl"
        log = RunLog(nested_path)

        assert nested_path.parent.exists()
        assert log.log_path == nested_path

    def test_log_run_success(self, run_log, temp_log_path):
        """Test logging a successful run."""
        run_log.log_run(
            success=True,
            duration_seconds=45.67,
            signal_count=10,
        )

        assert temp_log_path.exists()
        with open(temp_log_path) as f:
            entry = json.loads(f.readline())

        assert entry["success"] is True
        assert entry["duration_seconds"] == 45.67
        assert entry["signal_count"] == 10
        assert entry["error_message"] is None
        assert "timestamp" in entry

    def test_log_run_failure(self, run_log, temp_log_path):
        """Test logging a failed run."""
        run_log.log_run(
            success=False,
            duration_seconds=10.5,
            signal_count=0,
            error_message="API rate limit exceeded",
        )

        with open(temp_log_path) as f:
            entry = json.loads(f.readline())

        assert entry["success"] is False
        assert entry["error_message"] == "API rate limit exceeded"
        assert entry["signal_count"] == 0

    def test_log_run_with_metadata(self, run_log, temp_log_path):
        """Test logging run with metadata."""
        metadata = {"tickers": ["AAPL", "MSFT"], "mode": "llm"}
        run_log.log_run(
            success=True,
            duration_seconds=30.0,
            signal_count=5,
            metadata=metadata,
        )

        with open(temp_log_path) as f:
            entry = json.loads(f.readline())

        assert entry["metadata"] == metadata

    def test_log_run_appends_entries(self, run_log, temp_log_path):
        """Test that multiple runs are appended."""
        run_log.log_run(success=True, duration_seconds=10.0, signal_count=1)
        run_log.log_run(success=True, duration_seconds=20.0, signal_count=2)
        run_log.log_run(success=False, duration_seconds=5.0, signal_count=0)

        with open(temp_log_path) as f:
            lines = f.readlines()

        assert len(lines) == 3

    def test_get_run_statistics_empty_log(self, run_log):
        """Test statistics from empty log file."""
        stats = run_log.get_run_statistics()
        assert stats == {}

    def test_get_run_statistics_single_run(self, run_log):
        """Test statistics from single run."""
        run_log.log_run(success=True, duration_seconds=30.0, signal_count=5)

        stats = run_log.get_run_statistics()

        assert stats["total_runs"] == 1
        assert stats["successful_runs"] == 1
        assert stats["failed_runs"] == 0
        assert stats["success_rate"] == 1.0
        assert stats["average_duration_seconds"] == 30.0
        assert stats["total_signals_generated"] == 5
        assert stats["last_run"] is not None

    def test_get_run_statistics_multiple_runs(self, run_log):
        """Test statistics from multiple runs."""
        run_log.log_run(success=True, duration_seconds=20.0, signal_count=5)
        run_log.log_run(success=True, duration_seconds=40.0, signal_count=10)
        run_log.log_run(success=False, duration_seconds=5.0, signal_count=0)

        stats = run_log.get_run_statistics()

        assert stats["total_runs"] == 3
        assert stats["successful_runs"] == 2
        assert stats["failed_runs"] == 1
        assert stats["success_rate"] == pytest.approx(0.666, rel=0.01)
        assert stats["average_duration_seconds"] == 30.0  # (20+40)/2
        assert stats["total_signals_generated"] == 15

    def test_get_run_statistics_all_failed(self, run_log):
        """Test statistics when all runs failed."""
        run_log.log_run(success=False, duration_seconds=5.0, signal_count=0)
        run_log.log_run(success=False, duration_seconds=3.0, signal_count=0)

        stats = run_log.get_run_statistics()

        assert stats["total_runs"] == 2
        assert stats["successful_runs"] == 0
        assert stats["failed_runs"] == 2
        assert stats["success_rate"] == 0.0
        assert stats["average_duration_seconds"] == 0  # No successful runs

    def test_export_logs_empty(self, run_log):
        """Test exporting empty logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "export.jsonl"
            result = run_log.export_logs(export_path)

            assert result is True
            assert export_path.exists()

    def test_export_logs_filters_by_date(self, run_log, temp_log_path):
        """Test that export filters logs by date."""
        # Manually create log entries with different timestamps
        old_entry = {
            "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
            "success": True,
            "duration_seconds": 10.0,
            "signal_count": 1,
            "error_message": None,
            "metadata": {},
        }
        recent_entry = {
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "duration_seconds": 20.0,
            "signal_count": 2,
            "error_message": None,
            "metadata": {},
        }

        with open(temp_log_path, "w") as f:
            f.write(json.dumps(old_entry) + "\n")
            f.write(json.dumps(recent_entry) + "\n")

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "export.jsonl"
            result = run_log.export_logs(export_path, days=7)

            assert result is True

            with open(export_path) as f:
                lines = f.readlines()

            # Only recent entry should be exported (within 7 days)
            assert len(lines) == 1
            exported = json.loads(lines[0])
            assert exported["signal_count"] == 2

    def test_export_logs_creates_parent_directories(self, run_log):
        """Test that export creates parent directories."""
        run_log.log_run(success=True, duration_seconds=10.0, signal_count=1)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "nested" / "dir" / "export.jsonl"
            result = run_log.export_logs(export_path)

            assert result is True
            assert export_path.exists()

    def test_export_logs_all_entries_within_range(self, run_log):
        """Test exporting when all entries are within range."""
        run_log.log_run(success=True, duration_seconds=10.0, signal_count=1)
        run_log.log_run(success=True, duration_seconds=20.0, signal_count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "export.jsonl"
            result = run_log.export_logs(export_path, days=30)

            assert result is True

            with open(export_path) as f:
                lines = f.readlines()

            assert len(lines) == 2

    def test_duration_is_rounded(self, run_log, temp_log_path):
        """Test that duration is rounded to 2 decimal places."""
        run_log.log_run(
            success=True,
            duration_seconds=45.6789,
            signal_count=1,
        )

        with open(temp_log_path) as f:
            entry = json.loads(f.readline())

        assert entry["duration_seconds"] == 45.68

    def test_log_path_as_string(self):
        """Test RunLog accepts string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = str(Path(tmpdir) / "log.jsonl")
            run_log = RunLog(log_path)

            assert run_log.log_path == Path(log_path)
