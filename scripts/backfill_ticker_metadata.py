#!/usr/bin/env python3
"""Backfill metadata for existing tickers in the database.

This script updates all existing ticker records to populate the newly added
metadata fields: description, sector, industry, currency, and exchange.

Usage:
    # Dry run (preview changes without applying)
    uv run python scripts/backfill_ticker_metadata.py --dry-run

    # Apply changes
    uv run python scripts/backfill_ticker_metadata.py

    # Update only tickers with missing metadata
    uv run python scripts/backfill_ticker_metadata.py --only-missing

    # Update specific tickers
    uv run python scripts/backfill_ticker_metadata.py --ticker AAPL,MSFT,GOOGL
"""

import argparse
import sys
import time
from pathlib import Path

import yfinance as yf
from loguru import logger
from sqlmodel import select

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.db import DatabaseManager
from src.data.models import Ticker

# Configure logging for this script
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="INFO", format="<level>{message}</level>")


def fetch_ticker_metadata(symbol: str) -> dict | None:
    """Fetch metadata for a ticker from yfinance.

    Args:
        symbol: Ticker symbol.

    Returns:
        Dict with metadata fields or None if fetch fails.
    """
    try:
        ticker_obj = yf.Ticker(symbol)
        info = ticker_obj.info

        metadata = {
            "name": info.get("longName") or info.get("shortName") or symbol,
            "description": info.get("longBusinessSummary"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency") or info.get("financialCurrency") or "USD",
            "exchange": info.get("exchange"),
        }

        return metadata

    except Exception as e:
        logger.warning(f"Failed to fetch metadata for {symbol}: {e}")
        return None


def needs_update(ticker: Ticker, only_missing: bool = False) -> bool:
    """Check if a ticker needs metadata update.

    Args:
        ticker: Ticker object.
        only_missing: If True, only update if ALL metadata fields are missing.

    Returns:
        True if ticker needs update.
    """
    if only_missing:
        # Only update if all metadata fields are missing
        return not any([ticker.description, ticker.sector, ticker.industry, ticker.exchange])

    # Update if any metadata field is missing
    return not all([ticker.description, ticker.sector, ticker.industry, ticker.exchange])


def backfill_metadata(
    db_path: str = "data/falconsignals.db",
    dry_run: bool = False,
    only_missing: bool = False,
    ticker_symbols: list[str] | None = None,
) -> None:
    """Backfill metadata for existing tickers.

    Args:
        db_path: Path to database.
        dry_run: If True, preview changes without applying.
        only_missing: If True, only update tickers with all metadata missing.
        ticker_symbols: Optional list of specific tickers to update.
    """
    db = DatabaseManager(db_path)
    db.initialize()

    session = db.get_session()

    try:
        # Get tickers to update
        if ticker_symbols:
            # Update specific tickers
            tickers = []
            for symbol in ticker_symbols:
                ticker = session.exec(select(Ticker).where(Ticker.symbol == symbol.upper())).first()
                if ticker:
                    tickers.append(ticker)
                else:
                    logger.warning(f"Ticker {symbol} not found in database")
        else:
            # Get all tickers
            tickers = session.exec(select(Ticker)).all()

        # Filter tickers that need update
        tickers_to_update = [t for t in tickers if needs_update(t, only_missing)]

        total = len(tickers_to_update)
        logger.info(f"Found {total} ticker(s) to update (total: {len(tickers)} tickers)")

        if total == 0:
            logger.info("No tickers need updating. Exiting.")
            return

        if dry_run:
            logger.info("DRY RUN MODE - No changes will be applied")

        # Update each ticker
        updated = 0
        failed = 0
        skipped = 0

        for i, ticker in enumerate(tickers_to_update, 1):
            logger.info(f"[{i}/{total}] Processing {ticker.symbol}...")

            # Fetch metadata
            metadata = fetch_ticker_metadata(ticker.symbol)

            if not metadata:
                logger.warning(f"  ✗ Failed to fetch metadata for {ticker.symbol}")
                failed += 1
                continue

            # Check what changed
            changes = []
            if metadata["description"] and metadata["description"] != ticker.description:
                changes.append("description")
            if metadata["sector"] and metadata["sector"] != ticker.sector:
                changes.append("sector")
            if metadata["industry"] and metadata["industry"] != ticker.industry:
                changes.append("industry")
            if metadata["currency"] and metadata["currency"] != ticker.currency:
                changes.append("currency")
            if metadata["exchange"] and metadata["exchange"] != ticker.exchange:
                changes.append("exchange")

            if not changes:
                logger.info(f"  ⊘ No changes needed for {ticker.symbol}")
                skipped += 1
                continue

            # Display changes
            logger.info(f"  → Changes: {', '.join(changes)}")
            if "sector" in changes:
                logger.debug(f"     sector: {ticker.sector} → {metadata['sector']}")
            if "industry" in changes:
                logger.debug(f"     industry: {ticker.industry} → {metadata['industry']}")
            if "exchange" in changes:
                logger.debug(f"     exchange: {ticker.exchange} → {metadata['exchange']}")

            # Apply changes (unless dry run)
            if not dry_run:
                ticker.name = metadata["name"]
                ticker.description = metadata["description"]
                ticker.sector = metadata["sector"]
                ticker.industry = metadata["industry"]
                ticker.currency = metadata["currency"]
                ticker.exchange = metadata["exchange"]

                session.add(ticker)
                updated += 1
                logger.info(f"  ✓ Updated {ticker.symbol}")
            else:
                logger.info(f"  [DRY RUN] Would update {ticker.symbol}")

            # Rate limiting (1 request per second to be respectful)
            if i < total:
                time.sleep(1.0)

        # Commit changes
        if not dry_run and updated > 0:
            session.commit()
            logger.success(f"✅ Committed {updated} updates to database")

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total tickers processed: {total}")
        logger.info(f"Updated: {updated}")
        logger.info(f"Skipped (no changes): {skipped}")
        logger.info(f"Failed: {failed}")

        if dry_run:
            logger.info("\n⚠️  DRY RUN MODE - No changes were applied")
            logger.info("Run without --dry-run to apply changes")

    finally:
        session.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill metadata for existing tickers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )

    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Only update tickers with ALL metadata fields missing",
    )

    parser.add_argument(
        "--ticker",
        "-t",
        type=str,
        help="Comma-separated list of specific tickers to update (e.g., AAPL,MSFT,GOOGL)",
    )

    parser.add_argument(
        "--db",
        type=str,
        default="data/falconsignals.db",
        help="Path to database (default: data/falconsignals.db)",
    )

    args = parser.parse_args()

    # Parse ticker list
    ticker_symbols = None
    if args.ticker:
        ticker_symbols = [s.strip().upper() for s in args.ticker.split(",")]

    # Run backfill
    backfill_metadata(
        db_path=args.db,
        dry_run=args.dry_run,
        only_missing=args.only_missing,
        ticker_symbols=ticker_symbols,
    )


if __name__ == "__main__":
    main()
