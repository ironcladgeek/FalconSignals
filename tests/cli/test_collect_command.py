"""Tests for collect-fundamentals CLI command."""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


@pytest.fixture
def mock_config():
    """Mock configuration object."""
    config = MagicMock()
    config.database.db_path = "test.db"
    config.logging.level = "INFO"
    config.data.primary_provider = "alpha_vantage"
    config.data.backup_providers = ["yahoo_finance"]
    return config


@pytest.fixture
def mock_fundamental_data():
    """Mock fundamental data response."""
    return {
        "ticker": "AAPL",
        "company_info": {
            "name": "Apple Inc.",
            "sector": "TECHNOLOGY",
            "pe_ratio": 25.5,
        },
        "analyst_data": {"total_analysts": 50},
        "price_context": {"latest_price": 150.0},
        "metrics": {},
    }


class TestCollectFundamentalsValidation:
    """Test input validation for collect-fundamentals command."""

    def test_no_arguments_error(self):
        """Test that command fails when no arguments provided."""
        result = runner.invoke(app, ["collect-fundamentals"])
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Either --market, --group, or --ticker must be provided" in output

    def test_ticker_with_market_error(self):
        """Test that ticker and market cannot be used together."""
        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "AAPL", "--market", "us"])
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Cannot specify --ticker with --market or --group" in output

    def test_ticker_with_group_error(self):
        """Test that ticker and group cannot be used together."""
        result = runner.invoke(
            app, ["collect-fundamentals", "--ticker", "AAPL", "--group", "us_tech_software"]
        )
        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Cannot specify --ticker with --market or --group" in output

    def test_invalid_date_format(self):
        """Test that invalid date format is rejected."""
        with patch("src.cli.commands.collect.load_config"):
            result = runner.invoke(
                app, ["collect-fundamentals", "--ticker", "AAPL", "--date", "2025-13-45"]
            )
            assert result.exit_code == 1
            output = result.stdout + result.stderr
            assert "Invalid date format" in output


class TestCollectFundamentalsTickerMode:
    """Test ticker-specific collection mode."""

    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_single_ticker_success(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_config,
        mock_fundamental_data,
    ):
        """Test successful collection for a single ticker."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None
        mock_repo.store_snapshot.return_value = True

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.return_value = mock_fundamental_data

        # Run command
        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "AAPL", "--force"])

        # Assertions
        assert result.exit_code == 0
        assert "Successfully stored: 1" in result.stdout
        assert "Errors: 0" in result.stdout
        mock_provider.get_enriched_fundamentals.assert_called_once_with("AAPL", as_of_date=None)
        mock_repo.store_snapshot.assert_called_once()

    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    @patch("src.cli.commands.collect.time.sleep")
    def test_multiple_tickers_success(
        self,
        mock_sleep,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_config,
        mock_fundamental_data,
    ):
        """Test successful collection for multiple tickers."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None
        mock_repo.store_snapshot.return_value = True

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.return_value = mock_fundamental_data

        # Run command
        result = runner.invoke(
            app, ["collect-fundamentals", "--ticker", "AAPL,MSFT,GOOGL", "--force"]
        )

        # Assertions
        assert result.exit_code == 0
        assert "Successfully stored: 3" in result.stdout
        assert "Tickers to process: 3" in result.stdout
        assert mock_provider.get_enriched_fundamentals.call_count == 3
        assert mock_repo.store_snapshot.call_count == 3
        # Should sleep between tickers but not after the last one
        assert mock_sleep.call_count == 2

    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_ticker_already_exists_skipped(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_config,
        mock_fundamental_data,
    ):
        """Test that existing snapshots are skipped when force is not used."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = mock_fundamental_data  # Already exists

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider

        # Run command without --force
        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "AAPL"])

        # Assertions
        assert result.exit_code == 0
        assert "Skipped (already exists): 1" in result.stdout
        assert "Successfully stored: 0" in result.stdout
        mock_provider.get_enriched_fundamentals.assert_not_called()
        mock_repo.store_snapshot.assert_not_called()

    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_ticker_fetch_failure(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_config,
    ):
        """Test handling of data fetch failure."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.return_value = None  # Fetch failed

        # Run command
        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "INVALID", "--force"])

        # Assertions
        assert result.exit_code == 0
        assert "Errors: 1" in result.stdout
        assert "Failed (no data)" in result.stdout
        mock_repo.store_snapshot.assert_not_called()

    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_ticker_storage_failure(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_config,
        mock_fundamental_data,
    ):
        """Test handling of storage failure."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None
        mock_repo.store_snapshot.return_value = False  # Storage failed

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.return_value = mock_fundamental_data

        # Run command
        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "AAPL", "--force"])

        # Assertions
        assert result.exit_code == 0
        assert "Errors: 1" in result.stdout
        assert "Failed (storage)" in result.stdout


class TestCollectFundamentalsMarketMode:
    """Test market-based collection mode."""

    @patch("src.cli.commands.collect.get_tickers_for_markets")
    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_market_mode(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_get_tickers,
        mock_config,
        mock_fundamental_data,
    ):
        """Test collection by market."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_get_tickers.return_value = ["AAPL", "MSFT"]

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None
        mock_repo.store_snapshot.return_value = True

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.return_value = mock_fundamental_data

        # Run command
        result = runner.invoke(app, ["collect-fundamentals", "--market", "us", "--force"])

        # Assertions
        assert result.exit_code == 0
        assert "Mode: Market collection" in result.stdout
        assert "Tickers to process: 2" in result.stdout
        mock_get_tickers.assert_called_once_with(["us"], limit=None)

    @patch("src.cli.commands.collect.get_tickers_for_markets")
    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_market_mode_with_limit(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_get_tickers,
        mock_config,
        mock_fundamental_data,
    ):
        """Test collection by market with limit."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_get_tickers.return_value = ["AAPL"]

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None
        mock_repo.store_snapshot.return_value = True

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.return_value = mock_fundamental_data

        # Run command
        result = runner.invoke(
            app, ["collect-fundamentals", "--market", "us", "--limit", "1", "--force"]
        )

        # Assertions
        assert result.exit_code == 0
        mock_get_tickers.assert_called_once_with(["us"], limit=1)


class TestCollectFundamentalsGroupMode:
    """Test group-based collection mode."""

    @patch("src.cli.commands.collect.get_tickers_for_analysis")
    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_group_mode(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_get_tickers,
        mock_config,
        mock_fundamental_data,
    ):
        """Test collection by group."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_get_tickers.return_value = ["AAPL", "MSFT", "GOOGL"]

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None
        mock_repo.store_snapshot.return_value = True

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.return_value = mock_fundamental_data

        # Run command
        result = runner.invoke(
            app, ["collect-fundamentals", "--group", "us_tech_software", "--force"]
        )

        # Assertions
        assert result.exit_code == 0
        assert "Mode: Group collection" in result.stdout
        assert "Tickers to process: 3" in result.stdout
        mock_get_tickers.assert_called_once_with(
            markets=None, categories=["us_tech_software"], limit_per_category=None
        )


class TestCollectFundamentalsDryRun:
    """Test dry-run mode."""

    @patch("src.cli.commands.collect.get_tickers_for_markets")
    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_dry_run_mode(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_get_tickers,
        mock_config,
    ):
        """Test that dry-run mode doesn't store data."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_get_tickers.return_value = ["AAPL", "MSFT", "GOOGL"]

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider

        # Run command
        result = runner.invoke(app, ["collect-fundamentals", "--market", "us", "--dry-run"])

        # Assertions
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Tickers that would be processed (3):" in result.stdout
        assert "1. AAPL" in result.stdout
        assert "2. MSFT" in result.stdout
        assert "3. GOOGL" in result.stdout
        # Should not fetch or store data
        mock_provider.get_enriched_fundamentals.assert_not_called()
        mock_repo.store_snapshot.assert_not_called()

    @patch("src.cli.commands.collect.get_tickers_for_markets")
    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_dry_run_mode_many_tickers(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_get_tickers,
        mock_config,
    ):
        """Test that dry-run mode truncates long ticker lists."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        # Create 25 tickers
        mock_get_tickers.return_value = [f"TICK{i}" for i in range(25)]

        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        # Run command
        result = runner.invoke(app, ["collect-fundamentals", "--market", "us", "--dry-run"])

        # Assertions
        assert result.exit_code == 0
        assert "Tickers that would be processed (25):" in result.stdout
        assert "... and 5 more" in result.stdout


class TestCollectFundamentalsDateHandling:
    """Test snapshot date handling."""

    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_custom_snapshot_date(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_config,
        mock_fundamental_data,
    ):
        """Test collection with custom snapshot date."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None
        mock_repo.store_snapshot.return_value = True

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.return_value = mock_fundamental_data

        # Run command with specific date
        result = runner.invoke(
            app,
            ["collect-fundamentals", "--ticker", "AAPL", "--date", "2025-12-01", "--force"],
        )

        # Assertions
        assert result.exit_code == 0
        assert "Snapshot date: 2025-12-01" in result.stdout
        # Should pass the date for historical mode
        mock_provider.get_enriched_fundamentals.assert_called_once_with(
            "AAPL", as_of_date=date(2025, 12, 1)
        )

    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_default_snapshot_date(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_config,
        mock_fundamental_data,
    ):
        """Test collection uses today's date by default."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None
        mock_repo.store_snapshot.return_value = True

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.return_value = mock_fundamental_data

        # Run command without date
        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "AAPL", "--force"])

        # Assertions
        assert result.exit_code == 0
        today = date.today()
        assert f"Snapshot date: {today}" in result.stdout
        # Should NOT pass date for current mode (use Alpha Vantage)
        mock_provider.get_enriched_fundamentals.assert_called_once_with("AAPL", as_of_date=None)


class TestCollectFundamentalsErrorHandling:
    """Test error handling."""

    @patch("src.cli.commands.collect.load_config")
    def test_config_file_not_found(self, mock_load_config):
        """Test handling of missing config file."""
        mock_load_config.side_effect = FileNotFoundError("Config not found")

        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "AAPL"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Config not found" in output

    @patch("src.cli.commands.collect.load_config")
    def test_config_validation_error(self, mock_load_config):
        """Test handling of invalid config."""
        mock_load_config.side_effect = ValueError("Invalid configuration")

        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "AAPL"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Invalid configuration" in output

    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    def test_unexpected_exception(
        self,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_config,
    ):
        """Test handling of unexpected exceptions during data fetch."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_snapshot.return_value = None
        mock_repo.store_snapshot.return_value = True

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        # Make get_enriched_fundamentals raise an exception
        mock_provider.get_enriched_fundamentals.side_effect = Exception("Unexpected error")

        # Run command
        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "AAPL", "--force"])

        # Assertions
        # Exception during processing is logged but command continues with error count
        assert result.exit_code == 0
        assert "Errors: 1" in result.stdout
        assert "✗ Error - Unexpected error" in result.stdout


class TestCollectFundamentalsMixedResults:
    """Test handling of mixed success/failure scenarios."""

    @patch("src.cli.commands.collect.ProviderManager")
    @patch("src.cli.commands.collect.FundamentalSnapshotRepository")
    @patch("src.cli.commands.collect.DatabaseManager")
    @patch("src.cli.commands.collect.load_config")
    @patch("src.cli.commands.collect.setup_logging")
    @patch("src.cli.commands.collect.time.sleep")
    def test_mixed_success_failure_skip(
        self,
        mock_sleep,
        mock_setup_logging,
        mock_load_config,
        mock_db_manager,
        mock_repo_class,
        mock_provider_class,
        mock_config,
        mock_fundamental_data,
    ):
        """Test collection with mixed results: success, failure, and skip."""
        # Setup mocks
        mock_load_config.return_value = mock_config
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo

        # First ticker: already exists (skip)
        # Second ticker: fetch success, store success
        # Third ticker: fetch failure
        mock_repo.get_snapshot.side_effect = [
            mock_fundamental_data,  # AAPL exists
            None,  # MSFT doesn't exist
            None,  # GOOGL doesn't exist
        ]
        mock_repo.store_snapshot.return_value = True

        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        mock_provider.get_enriched_fundamentals.side_effect = [
            mock_fundamental_data,  # MSFT succeeds
            None,  # GOOGL fails
        ]

        # Run command
        result = runner.invoke(app, ["collect-fundamentals", "--ticker", "AAPL,MSFT,GOOGL"])

        # Assertions
        assert result.exit_code == 0
        assert "Successfully stored: 1" in result.stdout
        assert "Skipped (already exists): 1" in result.stdout
        assert "Errors: 1" in result.stdout
        assert "Total processed: 3" in result.stdout
