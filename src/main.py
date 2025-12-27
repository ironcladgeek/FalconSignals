"""FalconSignals CLI interface.

This is the main entry point for the FalconSignals CLI application.
All commands are modularized in src/cli/commands/.
"""

from src.cli import app


def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
