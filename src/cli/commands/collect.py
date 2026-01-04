"""Collect fundamental data and persist to database."""

import time
from datetime import date, datetime
from pathlib import Path

import typer

from src.cli.app import app
from src.config import load_config
from src.data.db import DatabaseManager
from src.data.provider_manager import ProviderManager
from src.data.repository import FundamentalSnapshotRepository
from src.MARKET_TICKERS import get_tickers_for_analysis, get_tickers_for_markets
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@app.command()
def collect_fundamentals(
    market: str = typer.Option(
        None,
        "--market",
        "-m",
        help="Market to collect: 'global', 'us', 'eu', 'nordic', or comma-separated (e.g., 'us,eu')",
    ),
    group: str = typer.Option(
        None,
        "--group",
        "-g",
        help="Ticker group: sector categories or portfolios. Comma-separated for multiple.",
    ),
    ticker: str = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Comma-separated list of tickers to collect (e.g., 'AAPL,MSFT,GOOGL')",
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of instruments to collect per market/group",
    ),
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file (default: config/local.yaml or config/default.yaml)",
        exists=True,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force re-fetch even if snapshot exists for today",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be collected without actually storing to database",
    ),
    snapshot_date: str = typer.Option(
        None,
        "--date",
        help="Snapshot date (YYYY-MM-DD format). Defaults to today.",
    ),
) -> None:
    """Collect fundamental data for tickers and persist to database.

    Fetches comprehensive fundamental data from all sources (Alpha Vantage,
    Finnhub, Yahoo Finance) and stores snapshots in the database for historical
    analysis and backtesting.

    Examples:
        # Collect for specific tickers (default: today's date)
        collect-fundamentals --ticker AAPL,MSFT,GOOGL

        # Collect for a market
        collect-fundamentals --market us --limit 50

        # Collect for a group
        collect-fundamentals --group us_tech_software

        # Dry run to see what would be collected
        collect-fundamentals --market nordic --dry-run

        # Force re-fetch even if snapshot exists
        collect-fundamentals --ticker AAPL --force

        # Collect for a specific historical date
        collect-fundamentals --ticker AAPL --date 2025-12-01
    """
    # Validate inputs
    if not market and not group and not ticker:
        typer.echo(
            "❌ Error: Either --market, --group, or --ticker must be provided\n"
            "Examples:\n"
            "  collect-fundamentals --market us\n"
            "  collect-fundamentals --group us_tech_software\n"
            "  collect-fundamentals --ticker AAPL,MSFT,GOOGL",
            err=True,
        )
        raise typer.Exit(code=1)

    if (market or group) and ticker:
        typer.echo("❌ Error: Cannot specify --ticker with --market or --group", err=True)
        raise typer.Exit(code=1)

    # Parse snapshot date
    target_date = date.today()
    if snapshot_date:
        try:
            target_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
        except ValueError:
            typer.echo(
                f"❌ Error: Invalid date format '{snapshot_date}'. Use YYYY-MM-DD format.",
                err=True,
            )
            raise typer.Exit(code=1) from None

    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)

        typer.echo("📊 Fundamental Data Collection Pipeline")
        typer.echo(f"  Snapshot date: {target_date}")
        typer.echo("  Data sources: Alpha Vantage, Finnhub, Yahoo Finance")

        # Initialize database
        db_path = config_obj.database.db_path
        db = DatabaseManager(db_path)
        db.initialize()

        # Initialize repository
        repository = FundamentalSnapshotRepository(db_path)

        # Initialize provider manager
        provider_manager = ProviderManager(
            primary_provider=config_obj.data.primary_provider,
            backup_providers=config_obj.data.backup_providers,
        )

        # Determine tickers to collect
        if ticker:
            tickers = [t.strip().upper() for t in ticker.split(",")]
            typer.echo(f"  Mode: Specific tickers ({len(tickers)} specified)")
        elif group:
            groups = [g.strip() for g in group.split(",")]
            typer.echo(f"  Mode: Group collection ({', '.join(groups)})")
            tickers = get_tickers_for_analysis(
                markets=None, categories=groups, limit_per_category=limit
            )
        else:
            markets_list = [m.strip().lower() for m in market.split(",")]
            typer.echo(f"  Mode: Market collection ({', '.join(markets_list)})")
            tickers = get_tickers_for_markets(markets_list, limit=limit)

        typer.echo(f"  Tickers to process: {len(tickers)}")

        if dry_run:
            typer.echo("\n🔍 DRY RUN MODE - No data will be stored to database")
            typer.echo(f"\nTickers that would be processed ({len(tickers)}):")
            for i, t in enumerate(tickers[:20], 1):
                typer.echo(f"  {i}. {t}")
            if len(tickers) > 20:
                typer.echo(f"  ... and {len(tickers) - 20} more")
            typer.echo()
            return

        typer.echo()

        # Process each ticker
        success_count = 0
        skipped_count = 0
        error_count = 0

        for i, ticker_symbol in enumerate(tickers, 1):
            try:
                prefix = f"[{i}/{len(tickers)}] {ticker_symbol}"

                # Check if snapshot exists (unless force)
                if not force:
                    existing = repository.get_snapshot(ticker_symbol, target_date)
                    if existing:
                        typer.echo(f"{prefix}: ⊘ Skipped (snapshot exists)")
                        skipped_count += 1
                        continue

                # Fetch fundamental data
                # Note: Only pass as_of_date for historical backtesting (when explicitly set)
                # For current data collection, use None to get Alpha Vantage enriched data
                typer.echo(f"{prefix}: Fetching data...", nl=False)
                as_of_date_param = target_date if snapshot_date else None
                fundamental_data = provider_manager.get_enriched_fundamentals(
                    ticker_symbol, as_of_date=as_of_date_param
                )

                if not fundamental_data:
                    typer.echo(" ✗ Failed (no data)")
                    logger.warning(f"No fundamental data available for {ticker_symbol}")
                    error_count += 1
                    continue

                # Store snapshot
                success = repository.store_snapshot(
                    ticker=ticker_symbol,
                    snapshot_date=target_date,
                    fundamental_data=fundamental_data,
                )

                if success:
                    typer.echo(" ✓ Stored")
                    success_count += 1
                else:
                    typer.echo(" ✗ Failed (storage)")
                    error_count += 1

                # Rate limiting (1 request per second to respect API limits)
                if i < len(tickers):
                    time.sleep(1.0)

            except Exception as e:
                typer.echo(f"{prefix}: ✗ Error - {e}")
                logger.error(f"Error collecting fundamental data for {ticker_symbol}: {e}")
                error_count += 1

        # Summary
        typer.echo("\n" + "=" * 70)
        typer.echo("✅ COLLECTION SUMMARY")
        typer.echo("=" * 70)
        typer.echo(f"Successfully stored: {success_count}")
        typer.echo(f"Skipped (already exists): {skipped_count}")
        typer.echo(f"Errors: {error_count}")
        typer.echo(f"Total processed: {success_count + skipped_count + error_count}")
        typer.echo(f"\n💾 Database: {db_path}")

        if success_count > 0:
            typer.echo(f"\n📈 {success_count} fundamental snapshot(s) stored for {target_date}")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        logger.exception(f"Unexpected error during collection: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
