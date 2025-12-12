"""Unified price data management with CSV storage.

Provides a single source of truth for price data per ticker, stored in efficient
CSV format for fast loading and compatibility with pandas-ta for technical analysis.
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from src.utils.logging import get_logger

logger = get_logger(__name__)


class PriceDataManager:
    """Unified price data manager with CSV storage.

    Stores price data as one CSV file per ticker, supporting incremental updates
    and efficient time-series operations.

    Attributes:
        prices_dir: Directory for CSV price files
    """

    # CSV column names matching StockPrice model
    COLUMNS = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "adj_close",
        "currency",
        "ticker",
        "name",
        "market",
        "instrument_type",
    ]

    # Minimal columns required for technical analysis
    REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]

    def __init__(self, prices_dir: str | Path = "data/cache/prices"):
        """Initialize price data manager.

        Args:
            prices_dir: Directory for storing CSV price files
        """
        self.prices_dir = Path(prices_dir)
        self.prices_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"PriceDataManager initialized at {self.prices_dir}")

    def get_file_path(self, ticker: str) -> Path:
        """Get CSV file path for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Path to the CSV file
        """
        return self.prices_dir / f"{ticker.upper()}.csv"

    def has_data(self, ticker: str) -> bool:
        """Check if price data exists for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if data exists
        """
        return self.get_file_path(ticker).exists()

    def get_data_range(self, ticker: str) -> tuple[date | None, date | None]:
        """Get date range of existing price data.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Tuple of (start_date, end_date) or (None, None) if no data
        """
        if not self.has_data(ticker):
            return None, None

        try:
            df = self._read_csv(ticker)
            if df.empty:
                return None, None

            return df["date"].min().date(), df["date"].max().date()
        except Exception as e:
            logger.warning(f"Error reading date range for {ticker}: {e}")
            return None, None

    def get_prices(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Get price data for a ticker within date range.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (inclusive), defaults to all data
            end_date: End date (inclusive), defaults to all data

        Returns:
            DataFrame with price data sorted by date
        """
        if not self.has_data(ticker):
            logger.debug(f"No price data found for {ticker}")
            return pd.DataFrame()

        df = self._read_csv(ticker)
        if df.empty:
            return df

        # Filter by date range
        if start_date:
            df = df[df["date"] >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df["date"] <= pd.Timestamp(end_date)]

        return df.sort_values("date").reset_index(drop=True)

    def get_latest_price(self, ticker: str) -> Optional[dict]:
        """Get the most recent price data for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with latest price data or None if no data
        """
        if not self.has_data(ticker):
            return None

        df = self._read_csv(ticker)
        if df.empty:
            return None

        latest = df.loc[df["date"].idxmax()]
        return {
            "date": latest["date"],
            "open": latest["open"],
            "high": latest["high"],
            "low": latest["low"],
            "close": latest["close"],
            "volume": latest["volume"],
            "adj_close": latest.get("adj_close"),
            "currency": latest.get("currency", "USD"),
        }

    def store_prices(
        self,
        ticker: str,
        prices: list[dict] | pd.DataFrame,
        append: bool = True,
    ) -> int:
        """Store price data for a ticker.

        Args:
            ticker: Stock ticker symbol
            prices: List of price dictionaries or DataFrame
            append: If True, merge with existing data; if False, replace

        Returns:
            Number of rows stored
        """
        # Convert to DataFrame
        if isinstance(prices, list):
            if not prices:
                logger.debug(f"No prices to store for {ticker}")
                return 0
            new_df = self._normalize_prices(prices, ticker)
        else:
            new_df = prices.copy()

        if new_df.empty:
            return 0

        # Ensure date column is datetime
        if "date" in new_df.columns:
            new_df["date"] = pd.to_datetime(new_df["date"])

        # Handle append mode
        if append and self.has_data(ticker):
            existing_df = self._read_csv(ticker)

            # Merge and deduplicate by date
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["date"], keep="last")
            combined = combined.sort_values("date").reset_index(drop=True)
            df_to_store = combined
        else:
            df_to_store = new_df.sort_values("date").reset_index(drop=True)

        # Store to CSV
        file_path = self.get_file_path(ticker)
        try:
            df_to_store.to_csv(file_path, index=False)
            logger.debug(f"Stored {len(df_to_store)} price records for {ticker}")
            return len(df_to_store)
        except Exception as e:
            logger.error(f"Error storing prices for {ticker}: {e}")
            return 0

    def update_from_provider(
        self,
        ticker: str,
        fetch_func,
        lookback_days: int = 365,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Update price data from a provider function.

        Intelligently fetches only missing data by checking existing date range.

        Args:
            ticker: Stock ticker symbol
            fetch_func: Function that takes (ticker, start_date, end_date) and returns prices
            lookback_days: How far back to look for data
            force_refresh: If True, re-fetch all data

        Returns:
            DataFrame with updated price data
        """
        today = date.today()
        start_of_range = today - timedelta(days=lookback_days)

        if not force_refresh and self.has_data(ticker):
            existing_start, existing_end = self.get_data_range(ticker)

            if existing_end:
                # Only fetch new data from day after existing end
                if existing_end >= today:
                    logger.debug(f"{ticker} price data is up to date")
                    return self.get_prices(ticker, start_date=start_of_range)

                fetch_start = existing_end + timedelta(days=1)
                logger.info(f"Updating {ticker} prices from {fetch_start} to {today}")
            else:
                fetch_start = start_of_range
        else:
            fetch_start = start_of_range

        # Fetch new data
        try:
            new_prices = fetch_func(ticker, fetch_start, today)
            if new_prices:
                self.store_prices(ticker, new_prices, append=True)
        except Exception as e:
            logger.error(f"Error fetching prices for {ticker}: {e}")

        return self.get_prices(ticker, start_date=start_of_range)

    def get_price_at_date(
        self,
        ticker: str,
        target_date: date,
        tolerance_days: int = 5,
    ) -> Optional[dict]:
        """Get price for a specific date with tolerance for non-trading days.

        Args:
            ticker: Stock ticker symbol
            target_date: Target date
            tolerance_days: Number of days to look back if exact date not found

        Returns:
            Price data dictionary or None if not found
        """
        df = self.get_prices(ticker)
        if df.empty:
            return None

        target_ts = pd.Timestamp(target_date)

        # Try exact date first
        exact = df[df["date"] == target_ts]
        if not exact.empty:
            row = exact.iloc[0]
            return self._row_to_dict(row)

        # Look for closest previous date within tolerance
        before_target = df[df["date"] <= target_ts]
        if before_target.empty:
            return None

        latest_before = before_target.loc[before_target["date"].idxmax()]
        days_diff = (target_ts - latest_before["date"]).days

        if days_diff <= tolerance_days:
            return self._row_to_dict(latest_before)

        logger.debug(f"No price found for {ticker} within {tolerance_days} days of {target_date}")
        return None

    def cleanup_old_data(self, max_age_days: int = 730) -> int:
        """Remove price data older than specified age.

        Args:
            max_age_days: Maximum age of data to keep

        Returns:
            Number of records removed
        """
        cutoff_date = date.today() - timedelta(days=max_age_days)
        total_removed = 0

        for file_path in self.prices_dir.glob("*.csv"):
            ticker = file_path.stem
            df = self._read_csv(ticker)
            if df.empty:
                continue

            original_len = len(df)
            df = df[df["date"] >= pd.Timestamp(cutoff_date)]

            if len(df) < original_len:
                removed = original_len - len(df)
                df.to_csv(file_path, index=False)
                total_removed += removed
                logger.info(f"Removed {removed} old records from {ticker}")

        return total_removed

    def get_stats(self) -> dict:
        """Get statistics about stored price data.

        Returns:
            Dictionary with stats
        """
        files = list(self.prices_dir.glob("*.csv"))
        total_size = sum(f.stat().st_size for f in files)
        total_records = 0

        for f in files:
            try:
                df = pd.read_csv(f)
                total_records += len(df)
            except Exception:
                pass

        return {
            "tickers_count": len(files),
            "total_records": total_records,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "prices_dir": str(self.prices_dir),
        }

    def validate_data(self, ticker: str) -> list[str]:
        """Validate price data quality for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []

        if not self.has_data(ticker):
            warnings.append(f"No price data found for {ticker}")
            return warnings

        df = self._read_csv(ticker)
        if df.empty:
            warnings.append(f"Price file exists but is empty for {ticker}")
            return warnings

        # Check for required columns
        missing_cols = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            warnings.append(f"Missing required columns: {missing_cols}")

        # Check for null values in critical columns
        for col in ["close", "volume"]:
            if col in df.columns and df[col].isnull().any():
                null_count = df[col].isnull().sum()
                warnings.append(f"Column '{col}' has {null_count} null values")

        # Check for negative prices
        for col in ["open", "high", "low", "close"]:
            if col in df.columns and (df[col] < 0).any():
                warnings.append(f"Column '{col}' has negative values")

        # Check for gaps > 5 trading days
        if len(df) > 1:
            df_sorted = df.sort_values("date")
            gaps = df_sorted["date"].diff()
            large_gaps = gaps[gaps > timedelta(days=5)]
            if not large_gaps.empty:
                warnings.append(f"Found {len(large_gaps)} gaps larger than 5 days in price data")

        # Check data recency
        start_date, end_date = self.get_data_range(ticker)
        if end_date:
            days_old = (date.today() - end_date).days
            if days_old > 7:
                warnings.append(f"Data is {days_old} days old (last date: {end_date})")

        return warnings

    def _read_csv(self, ticker: str) -> pd.DataFrame:
        """Read CSV file for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            DataFrame with price data
        """
        file_path = self.get_file_path(ticker)
        if not file_path.exists():
            return pd.DataFrame()

        try:
            df = pd.read_csv(file_path, parse_dates=["date"])
            return df
        except Exception as e:
            logger.error(f"Error reading CSV for {ticker}: {e}")
            return pd.DataFrame()

    def _normalize_prices(self, prices: list[dict], ticker: str) -> pd.DataFrame:
        """Normalize price data from various formats to standard DataFrame.

        Args:
            prices: List of price dictionaries (may have varied field names)
            ticker: Stock ticker symbol

        Returns:
            Normalized DataFrame
        """
        # Map common field name variations
        field_mapping = {
            "close_price": "close",
            "open_price": "open",
            "high_price": "high",
            "low_price": "low",
            "adjusted_close": "adj_close",
        }

        normalized = []
        for p in prices:
            row = {"ticker": ticker}

            # Map fields
            for orig_key, new_key in field_mapping.items():
                if orig_key in p:
                    row[new_key] = p[orig_key]

            # Copy standard fields
            for key in ["date", "open", "high", "low", "close", "volume", "currency"]:
                if key in p and key not in row:
                    row[key] = p[key]

            # Copy metadata if present
            for key in ["name", "market", "instrument_type"]:
                if key in p:
                    row[key] = p[key]

            normalized.append(row)

        return pd.DataFrame(normalized)

    def _row_to_dict(self, row) -> dict:
        """Convert DataFrame row to dictionary.

        Args:
            row: DataFrame row (Series)

        Returns:
            Dictionary with price data
        """
        result = {
            "date": row["date"],
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": row.get("volume"),
        }

        # Add optional fields if present
        if "adj_close" in row.index:
            result["adj_close"] = row["adj_close"]
        if "currency" in row.index:
            result["currency"] = row["currency"]

        return result
