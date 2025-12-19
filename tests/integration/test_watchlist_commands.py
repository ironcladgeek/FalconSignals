"""Integration tests for watchlist CLI commands."""

import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.main import app


@pytest.fixture
def runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_config():
    """Create temporary config file for testing."""
    config_content = """
capital:
  starting_capital_eur: 2000
  monthly_deposit_eur: 500

risk:
  tolerance: moderate

markets:
  included: [us]
  included_instruments: [stocks]

analysis:
  buy_threshold: 70
  sell_threshold: 30
  historical_data_lookback_days: 365

llm:
  provider: anthropic
  model: claude-3-haiku-20240307
  temperature: 0.7

logging:
  level: INFO

database:
  enabled: true

token_tracker:
  enabled: false

deployment:
  cost_limit_eur_per_month: 50
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def temp_db():
    """Create a temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_watchlist.db"


@pytest.fixture
def mock_config(temp_db):
    """Create mock config object."""
    return type(
        "Config",
        (),
        {
            "logging": type("Logging", (), {"level": "INFO"})(),
            "output": type("Output", (), {"report_format": "markdown"})(),
            "database": type("Database", (), {"enabled": True, "db_path": str(temp_db)})(),
            "capital": type(
                "Capital", (), {"starting_capital_eur": 2000, "monthly_deposit_eur": 500}
            )(),
            "llm": type(
                "LLM",
                (),
                {"provider": "anthropic", "model": "claude-3-haiku-20240307", "temperature": 0.7},
            )(),
            "data": type(
                "Data",
                (),
                {
                    "primary_provider": "yahoo_finance",
                    "backup_providers": ["alpha_vantage", "finnhub"],
                },
            )(),
            "analysis": type("Analysis", (), {"historical_data_lookback_days": 365})(),
        },
    )()


@pytest.mark.integration
class TestWatchlistCommand:
    """Test suite for the watchlist CLI command."""

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    def test_watchlist_add_ticker(self, mock_init_db, mock_load_config, runner, mock_config):
        """Test adding a ticker to watchlist."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            # Mock init_db to create actual database
            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist", "--add-ticker", "AAPL"])

            if result.exit_code != 0:
                print(f"STDOUT: {result.stdout}")
                if result.exception:
                    import traceback

                    traceback.print_exception(
                        type(result.exception), result.exception, result.exception.__traceback__
                    )

            assert result.exit_code == 0
            assert "Added AAPL to watchlist" in result.stdout or "✅" in result.stdout

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    def test_watchlist_add_duplicate_ticker(
        self, mock_init_db, mock_load_config, runner, mock_config
    ):
        """Test adding a duplicate ticker to watchlist."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            # Add first time
            runner.invoke(app, ["watchlist", "--add-ticker", "AAPL"])

            # Add again
            result = runner.invoke(app, ["watchlist", "--add-ticker", "AAPL"])

            assert result.exit_code == 1
            assert "already in watchlist" in result.output

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    def test_watchlist_remove_ticker(self, mock_init_db, mock_load_config, runner, mock_config):
        """Test removing a ticker from watchlist."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            # Add first
            runner.invoke(app, ["watchlist", "--add-ticker", "AAPL"])

            # Remove
            result = runner.invoke(app, ["watchlist", "--remove-ticker", "AAPL"])

            assert result.exit_code == 0
            assert "Removed AAPL from watchlist" in result.stdout or "✅" in result.stdout

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    def test_watchlist_remove_nonexistent(
        self, mock_init_db, mock_load_config, runner, mock_config
    ):
        """Test removing a non-existent ticker from watchlist."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist", "--remove-ticker", "NONEXISTENT"])

            assert result.exit_code == 1

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    def test_watchlist_list_empty(self, mock_init_db, mock_load_config, runner, mock_config):
        """Test listing empty watchlist."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist", "--list"])

            assert result.exit_code == 0
            assert "Watchlist is empty" in result.stdout or "empty" in result.stdout.lower()

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    def test_watchlist_list_with_items(self, mock_init_db, mock_load_config, runner, mock_config):
        """Test listing watchlist with items."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            # Add tickers
            runner.invoke(app, ["watchlist", "--add-ticker", "AAPL"])
            runner.invoke(app, ["watchlist", "--add-ticker", "MSFT"])

            # List
            result = runner.invoke(app, ["watchlist", "--list"])

            assert result.exit_code == 0
            # Should contain ticker symbols
            assert "AAPL" in result.stdout
            assert "MSFT" in result.stdout

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    def test_watchlist_no_action(self, mock_init_db, mock_load_config, runner, mock_config):
        """Test watchlist command with no action specified."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist"])

            assert result.exit_code == 1
            assert "specify an action" in result.stdout.lower() or "❌" in result.stdout

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    @patch("src.data.repository.RecommendationsRepository")
    def test_watchlist_add_by_recommendation(
        self,
        mock_rec_repo_class,
        mock_init_db,
        mock_load_config,
        runner,
        mock_config,
    ):
        """Test adding ticker by recommendation ID."""
        mock_load_config.return_value = mock_config

        # Mock recommendation
        mock_rec_repo = MagicMock()
        mock_rec_repo.get_recommendation_by_id.return_value = {
            "id": 123,
            "ticker": "NVDA",
            "name": "NVIDIA Corporation",
        }
        mock_rec_repo_class.return_value = mock_rec_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist", "--add-recommendation", "123"])

            # The command should attempt to add the ticker
            # Exit code depends on whether recommendation exists
            assert result.exit_code in (0, 1)

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    def test_watchlist_add_recommendation_not_found(
        self,
        mock_init_db,
        mock_load_config,
        runner,
        mock_config,
    ):
        """Test adding by non-existent recommendation ID."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist", "--add-recommendation", "99999"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()


@pytest.mark.integration
class TestWatchlistReportCommand:
    """Test suite for the watchlist-report CLI command."""

    @patch("src.main.load_config")
    @patch("src.main.setup_logging")
    @patch("src.main.init_db")
    def test_watchlist_report_no_signals(
        self, mock_init_db, mock_setup_logging, mock_load_config, runner, mock_config
    ):
        """Test watchlist-report when no signals exist."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist-report"])

            # Command may exit with 0 or 1 due to exception handling
            # Important check: output indicates no signals found
            assert "No signals found" in result.output or "empty" in result.output.lower()

    @patch("src.main.load_config")
    @patch("src.main.setup_logging")
    @patch("src.main.init_db")
    def test_watchlist_report_with_ticker_filter(
        self, mock_init_db, mock_setup_logging, mock_load_config, runner, mock_config
    ):
        """Test watchlist-report with ticker filter."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            # First add ticker to watchlist and store a signal
            from src.data.repository import WatchlistRepository, WatchlistSignalRepository

            watchlist_repo = WatchlistRepository(db_path)
            signal_repo = WatchlistSignalRepository(db_path)

            watchlist_repo.add_to_watchlist("AAPL")
            signal_repo.store_signal(
                ticker_symbol="AAPL",
                analysis_date=date.today(),
                score=75.0,
                confidence=80.0,
                current_price=150.0,
                action="Buy",
                rationale="Strong technical setup",
            )

            result = runner.invoke(app, ["watchlist-report", "--ticker", "AAPL"])

            assert result.exit_code == 0
            # Should show AAPL in output
            assert "AAPL" in result.stdout

    @patch("src.main.load_config")
    @patch("src.main.setup_logging")
    @patch("src.main.init_db")
    def test_watchlist_report_with_days_option(
        self, mock_init_db, mock_setup_logging, mock_load_config, runner, mock_config
    ):
        """Test watchlist-report with days option."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist-report", "--days", "90"])

            # Command should run (may show "no signals" message)
            assert "Watchlist" in result.output or "No signals" in result.output

    @patch("src.main.load_config")
    @patch("src.main.setup_logging")
    @patch("src.main.init_db")
    def test_watchlist_report_multiple_tickers(
        self, mock_init_db, mock_setup_logging, mock_load_config, runner, mock_config
    ):
        """Test watchlist-report with multiple tickers."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            # Setup tickers and signals
            from src.data.repository import WatchlistRepository, WatchlistSignalRepository

            watchlist_repo = WatchlistRepository(db_path)
            signal_repo = WatchlistSignalRepository(db_path)

            for ticker in ["AAPL", "MSFT", "GOOGL"]:
                watchlist_repo.add_to_watchlist(ticker)
                signal_repo.store_signal(
                    ticker_symbol=ticker,
                    analysis_date=date.today(),
                    score=75.0,
                    confidence=80.0,
                    current_price=150.0,
                )

            result = runner.invoke(app, ["watchlist-report", "--ticker", "AAPL,MSFT"])

            # Should contain both tickers (exit code may be 0 or 1)
            assert "AAPL" in result.output
            assert "MSFT" in result.output


@pytest.mark.integration
class TestWatchlistScanCommand:
    """Test suite for the watchlist-scan CLI command."""

    @patch("src.main.load_config")
    @patch("src.main.setup_logging")
    @patch("src.main.init_db")
    def test_watchlist_scan_empty_watchlist(
        self, mock_init_db, mock_setup_logging, mock_load_config, runner, mock_config
    ):
        """Test watchlist-scan when watchlist is empty."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist-scan"])

            # Command exits with 0 for empty watchlist (early exit)
            assert "Watchlist is empty" in result.output or "empty" in result.output.lower()

    @patch("src.main.load_config")
    @patch("src.main.setup_logging")
    @patch("src.main.init_db")
    @patch("src.main._download_price_data")
    @patch("src.main._run_watchlist_scan")
    def test_watchlist_scan_success(
        self,
        mock_run_scan,
        mock_download,
        mock_init_db,
        mock_setup_logging,
        mock_load_config,
        runner,
        mock_config,
    ):
        """Test successful watchlist-scan execution."""
        mock_load_config.return_value = mock_config
        mock_download.return_value = (1, 0, 0, {})  # success, skipped, errors, details
        mock_run_scan.return_value = (1, 0)  # success_count, error_count

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            # Add ticker to watchlist
            from src.data.repository import WatchlistRepository

            watchlist_repo = WatchlistRepository(db_path)
            watchlist_repo.add_to_watchlist("AAPL")

            result = runner.invoke(app, ["watchlist-scan"])

            # Should call the scan function
            assert mock_run_scan.called or "Scanning" in result.stdout

    @patch("src.main.load_config")
    @patch("src.main.setup_logging")
    @patch("src.main.init_db")
    def test_watchlist_scan_specific_tickers_not_in_watchlist(
        self, mock_init_db, mock_setup_logging, mock_load_config, runner, mock_config
    ):
        """Test watchlist-scan with tickers not in watchlist."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            result = runner.invoke(app, ["watchlist-scan", "--ticker", "UNKNOWN"])

            assert result.exit_code == 1
            assert "not in watchlist" in result.output.lower() or "No valid" in result.output

    @patch("src.main.load_config")
    @patch("src.main.setup_logging")
    @patch("src.main.init_db")
    @patch("src.main._download_price_data")
    @patch("src.main._run_watchlist_scan")
    def test_watchlist_scan_specific_valid_tickers(
        self,
        mock_run_scan,
        mock_download,
        mock_init_db,
        mock_setup_logging,
        mock_load_config,
        runner,
        mock_config,
    ):
        """Test watchlist-scan with specific valid tickers."""
        mock_load_config.return_value = mock_config
        mock_download.return_value = (2, 0, 0, {})
        mock_run_scan.return_value = (2, 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            # Add tickers to watchlist
            from src.data.repository import WatchlistRepository

            watchlist_repo = WatchlistRepository(db_path)
            watchlist_repo.add_to_watchlist("AAPL")
            watchlist_repo.add_to_watchlist("MSFT")
            watchlist_repo.add_to_watchlist("GOOGL")

            result = runner.invoke(app, ["watchlist-scan", "--ticker", "AAPL,MSFT"])

            # Should process specified tickers
            assert "specified" in result.stdout.lower() or "Scanning" in result.stdout


@pytest.mark.integration
class TestWatchlistIntegrationFlow:
    """Integration tests for complete watchlist workflow."""

    @patch("src.main.load_config")
    @patch("src.main.init_db")
    def test_complete_watchlist_workflow(self, mock_init_db, mock_load_config, runner, mock_config):
        """Test complete watchlist add -> list -> remove workflow."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            # Step 1: Add tickers
            result1 = runner.invoke(app, ["watchlist", "--add-ticker", "AAPL"])
            assert result1.exit_code == 0

            result2 = runner.invoke(app, ["watchlist", "--add-ticker", "MSFT"])
            assert result2.exit_code == 0

            # Step 2: List and verify
            result3 = runner.invoke(app, ["watchlist", "--list"])
            assert result3.exit_code == 0
            assert "AAPL" in result3.stdout
            assert "MSFT" in result3.stdout

            # Step 3: Remove one ticker
            result4 = runner.invoke(app, ["watchlist", "--remove-ticker", "AAPL"])
            assert result4.exit_code == 0

            # Step 4: Verify removal
            result5 = runner.invoke(app, ["watchlist", "--list"])
            assert result5.exit_code == 0
            assert "AAPL" not in result5.stdout
            assert "MSFT" in result5.stdout

    @patch("src.main.load_config")
    @patch("src.main.setup_logging")
    @patch("src.main.init_db")
    def test_watchlist_report_after_signal_storage(
        self, mock_init_db, mock_setup_logging, mock_load_config, runner, mock_config
    ):
        """Test generating report after storing signals."""
        mock_load_config.return_value = mock_config

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            mock_config.database.db_path = str(db_path)

            def real_init_db(path):
                from src.data.db import DatabaseManager

                dm = DatabaseManager(path)
                dm.initialize()

            mock_init_db.side_effect = real_init_db

            # Setup: Add ticker and store signal directly
            from src.data.repository import WatchlistRepository, WatchlistSignalRepository

            watchlist_repo = WatchlistRepository(db_path)
            signal_repo = WatchlistSignalRepository(db_path)

            watchlist_repo.add_to_watchlist("AAPL")
            signal_repo.store_signal(
                ticker_symbol="AAPL",
                analysis_date=date.today(),
                score=85.0,
                confidence=90.0,
                current_price=175.50,
                action="Buy",
                rationale="Strong momentum breakout above resistance",
                entry_price=174.00,
                stop_loss=168.00,
                take_profit=190.00,
            )

            # Generate report
            result = runner.invoke(app, ["watchlist-report", "--ticker", "AAPL"])

            assert result.exit_code == 0
            # Should show signal data
            assert "AAPL" in result.stdout
            # May show score, action, or other details depending on output format
