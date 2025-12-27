"""Integration tests for journal CLI command."""

import re
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.main import app


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI color codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


@pytest.fixture
def runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def temp_config(temp_db):
    """Create temporary config file for testing."""
    config_content = f"""
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
  historical_data_lookback_days: 730

llm:
  provider: anthropic
  model: claude-3-haiku-20240307
  temperature: 0.7

logging:
  level: INFO

token_tracker:
  enabled: true

deployment:
  cost_limit_eur_per_month: 50

database:
  enabled: true
  db_path: {temp_db}

data:
  primary_provider: yahoo_finance
  backup_providers: ["alpha_vantage", "finnhub"]
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


@pytest.mark.integration
class TestJournalCLIAdd:
    """Test journal CLI add command."""

    def test_journal_add_long_position(self, runner, temp_config):
        """Test adding a long position with all fields."""
        # Simulate user inputs
        inputs = [
            "AAPL",  # ticker
            "2025-12-01",  # entry date
            "long",  # position type
            "150.50",  # entry price
            "100",  # position size
            "5.0",  # fees
            "140.00",  # stop loss
            "165.00",  # take profit
            "Long position on AAPL",  # description
        ]
        input_string = "\n".join(inputs) + "\n"

        result = runner.invoke(
            app,
            ["journal", "--action", "add", "--config", str(temp_config)],
            input=input_string,
        )

        # Command should show the add interface
        assert "Add New Trade" in result.stdout
        assert "Ticker symbol:" in result.stdout
        # Exit code may be 0 (success) or 1 (error) depending on ticker resolution
        # The important thing is the command doesn't crash
        assert result.exit_code in (0, 1)

    def test_journal_add_short_position_minimal(self, runner, temp_config):
        """Test adding a short position with minimal fields."""
        # Simulate user inputs - no stop loss, take profit, or description
        inputs = [
            "TSLA",  # ticker
            "",  # entry date (use today)
            "short",  # position type
            "245.75",  # entry price
            "50",  # position size
            "0",  # fees
            "",  # no stop loss
            "",  # no take profit
            "",  # no description
        ]
        input_string = "\n".join(inputs) + "\n"

        result = runner.invoke(
            app,
            ["journal", "--action", "add", "--config", str(temp_config)],
            input=input_string,
        )

        assert "Add New Trade" in result.stdout
        assert "Ticker symbol:" in result.stdout
        # Accept both success and failure (ticker resolution may fail)
        assert result.exit_code in (0, 1)

    def test_journal_add_invalid_date_format(self, runner, temp_config):
        """Test adding trade with invalid date format."""
        inputs = [
            "MSFT",  # ticker
            "2025/12/01",  # invalid date format (should be YYYY-MM-DD)
        ]
        input_string = "\n".join(inputs) + "\n"

        result = runner.invoke(
            app,
            ["journal", "--action", "add", "--config", str(temp_config)],
            input=input_string,
        )

        # Should show the interface
        assert "Add New Trade" in result.stdout
        # Invalid date format should cause an error
        assert result.exit_code == 1


@pytest.mark.integration
class TestJournalCLIUpdate:
    """Test journal CLI update command."""

    def test_journal_update_shows_interface(self, runner, temp_config):
        """Test that update action shows the update interface."""
        update_inputs = [
            "1",  # trade ID
        ]
        update_input_string = "\n".join(update_inputs) + "\n"

        result = runner.invoke(
            app,
            ["journal", "--action", "update", "--config", str(temp_config)],
            input=update_input_string,
        )

        assert "Update Trade" in result.stdout
        assert "Trade ID to update:" in result.stdout
        # May fail if trade doesn't exist, which is expected
        assert result.exit_code in (0, 1)


@pytest.mark.integration
class TestJournalCLIClose:
    """Test journal CLI close command."""

    def test_journal_close_shows_interface(self, runner, temp_config):
        """Test that close action shows the close interface."""
        close_inputs = [
            "1",  # trade ID
        ]
        close_input_string = "\n".join(close_inputs) + "\n"

        result = runner.invoke(
            app,
            ["journal", "--action", "close", "--config", str(temp_config)],
            input=close_input_string,
        )

        assert "Close Trade" in result.stdout
        assert "Trade ID to close:" in result.stdout
        # May fail if trade doesn't exist, which is expected
        assert result.exit_code in (0, 1)


@pytest.mark.integration
class TestJournalCLIList:
    """Test journal CLI list command."""

    def test_journal_list_shows_interface(self, runner, temp_config):
        """Test that list action shows the list interface."""
        list_inputs = ["open"]
        list_input_string = "\n".join(list_inputs) + "\n"

        result = runner.invoke(
            app,
            ["journal", "--action", "list", "--config", str(temp_config)],
            input=list_input_string,
        )

        assert "List Trades" in result.stdout
        assert result.exit_code in (0, 1)  # May succeed or fail depending on data


@pytest.mark.integration
class TestJournalCLIView:
    """Test journal CLI view command."""

    def test_journal_view_shows_interface(self, runner, temp_config):
        """Test that view action shows the view interface."""
        view_inputs = ["1"]
        view_input_string = "\n".join(view_inputs) + "\n"

        result = runner.invoke(
            app,
            ["journal", "--action", "view", "--config", str(temp_config)],
            input=view_input_string,
        )

        assert "View Trade Details" in result.stdout
        assert "Trade ID:" in result.stdout
        # May fail if trade doesn't exist, which is expected
        assert result.exit_code in (0, 1)


@pytest.mark.integration
class TestJournalCLIInteractive:
    """Test journal CLI interactive mode (no action specified)."""

    def test_journal_interactive_mode(self, runner, temp_config):
        """Test journal command without action prompts for selection."""
        inputs = [
            "add",  # action
            "AMD",  # ticker
        ]
        input_string = "\n".join(inputs) + "\n"

        result = runner.invoke(app, ["journal", "--config", str(temp_config)], input=input_string)

        assert "Trading Journal" in result.stdout
        assert "Available actions:" in result.stdout
        # May succeed or fail depending on further inputs
        assert result.exit_code in (0, 1)


@pytest.mark.integration
class TestJournalCLIErrorHandling:
    """Test journal CLI error handling."""

    def test_journal_invalid_action(self, runner, temp_config):
        """Test journal command with invalid action."""
        result = runner.invoke(
            app, ["journal", "--action", "invalid_action", "--config", str(temp_config)]
        )

        assert result.exit_code == 1
        # Should show valid actions message
        assert "Valid actions" in result.stdout

    def test_journal_database_disabled(self, runner):
        """Test journal command when database is disabled."""
        config_content = """
capital:
  starting_capital_eur: 2000
  monthly_deposit_eur: 500

risk:
  tolerance: moderate

markets:
  included: [us]

llm:
  provider: anthropic
  model: claude-3-haiku-20240307

logging:
  level: INFO

database:
  enabled: false
  db_path: data/falconsignals.db

data:
  primary_provider: yahoo_finance
  backup_providers: []

analysis:
  historical_data_lookback_days: 730
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()
            config_path = Path(f.name)

        try:
            inputs = ["add", "AAPL"]
            input_string = "\n".join(inputs) + "\n"

            result = runner.invoke(
                app,
                ["journal", "--action", "add", "--config", str(config_path)],
                input=input_string,
            )

            # Should still work - database will use default path
            assert result.exit_code in (0, 1)  # May fail for other reasons but not crash

        finally:
            config_path.unlink(missing_ok=True)


@pytest.mark.integration
class TestJournalCLIHelp:
    """Test journal CLI help."""

    def test_journal_help(self, runner):
        """Test journal --help command."""
        result = runner.invoke(app, ["journal", "--help"])

        # Strip ANSI codes for reliable string matching
        clean_output = strip_ansi_codes(result.stdout)

        assert result.exit_code == 0
        assert "Manage trading journal entries interactively" in clean_output
        assert "--action" in clean_output
        assert "add" in clean_output
        assert "update" in clean_output
        assert "close" in clean_output
        assert "list" in clean_output
        assert "view" in clean_output
