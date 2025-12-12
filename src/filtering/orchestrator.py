"""Orchestrator for executing filtering strategies."""

from typing import Any

import typer

from src.filtering.strategies import FilterStrategy, get_strategy
from src.tools.fetchers import PriceFetcherTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class FilterOrchestrator:
    """Orchestrates ticker filtering using configurable strategies."""

    def __init__(
        self,
        strategy: FilterStrategy | str,
        price_fetcher: PriceFetcherTool | None = None,
        provider_name: str | None = None,
        fixture_path: str | None = None,
        config: Any | None = None,
        strategy_config: dict[str, Any] | None = None,
    ):
        """Initialize filter orchestrator.

        Args:
            strategy: FilterStrategy instance or strategy name string
            price_fetcher: Optional existing PriceFetcherTool instance
            provider_name: Data provider to use (if creating new fetcher)
            fixture_path: Path to fixture directory (if using fixture provider)
            config: Configuration object with analysis settings
            strategy_config: Strategy-specific configuration
        """
        # Initialize or convert strategy
        if isinstance(strategy, str):
            self.strategy = get_strategy(strategy, strategy_config)
        else:
            self.strategy = strategy

        # Initialize or use existing price fetcher
        if price_fetcher:
            self.price_fetcher = price_fetcher
        else:
            self.price_fetcher = PriceFetcherTool(
                provider_name=provider_name, fixture_path=fixture_path, config=config
            )

        self.config = config
        logger.debug(f"FilterOrchestrator initialized with strategy: {self.strategy.name}")

    def filter_tickers(
        self,
        tickers: list[str],
        historical_date: Any | None = None,
        lookback_days: int = 730,
        show_progress: bool = True,
    ) -> dict[str, Any]:
        """Filter tickers using the configured strategy.

        Args:
            tickers: List of ticker symbols to filter
            historical_date: Optional date for historical analysis
            lookback_days: Days of price history to fetch
            show_progress: Show progress bar during filtering

        Returns:
            Dictionary with:
                - status: "success" or "error"
                - filtered_tickers: List of tickers that passed the filter
                - total_scanned: Total tickers scanned
                - total_filtered: Number of tickers that passed
                - filter_details: Dict mapping ticker to filter reasons
                - message: Optional error message
        """
        try:
            # Set historical date if provided
            if historical_date and hasattr(self.price_fetcher, "set_historical_date"):
                self.price_fetcher.set_historical_date(historical_date)
                logger.debug(f"Set historical date {historical_date} for price fetcher")

            filtered_tickers = []
            filter_details = {}

            # Process tickers with optional progress bar
            if show_progress:
                with typer.progressbar(
                    tickers,
                    label=f"🔍 Filtering ({self.strategy.name})",
                    show_pos=True,
                    show_percent=True,
                ) as progress:
                    for ticker in progress:
                        # Fetch price data
                        result = self.price_fetcher.run(ticker, days_back=lookback_days)

                        if "error" in result:
                            logger.debug(f"Error fetching prices for {ticker}: {result['error']}")
                            filter_details[ticker] = {
                                "included": False,
                                "reasons": [f"Data error: {result['error']}"],
                            }
                            continue

                        prices = result.get("prices", [])
                        if len(prices) < 5:
                            filter_details[ticker] = {
                                "included": False,
                                "reasons": ["Insufficient price data"],
                            }
                            continue

                        # Apply strategy filter
                        should_include, reasons = self.strategy.filter(ticker, prices)

                        filter_details[ticker] = {
                            "included": should_include,
                            "reasons": reasons,
                            "latest_price": result.get("latest_price"),
                        }

                        if should_include:
                            filtered_tickers.append(ticker)
            else:
                # Process without progress bar
                for ticker in tickers:
                    # Fetch price data
                    result = self.price_fetcher.run(ticker, days_back=lookback_days)

                    if "error" in result:
                        logger.debug(f"Error fetching prices for {ticker}: {result['error']}")
                        filter_details[ticker] = {
                            "included": False,
                            "reasons": [f"Data error: {result['error']}"],
                        }
                        continue

                    prices = result.get("prices", [])
                    if len(prices) < 5:
                        filter_details[ticker] = {
                            "included": False,
                            "reasons": ["Insufficient price data"],
                        }
                        continue

                    # Apply strategy filter
                    should_include, reasons = self.strategy.filter(ticker, prices)

                    filter_details[ticker] = {
                        "included": should_include,
                        "reasons": reasons,
                        "latest_price": result.get("latest_price"),
                    }

                    if should_include:
                        filtered_tickers.append(ticker)

            logger.debug(
                f"Filtered {len(filtered_tickers)}/{len(tickers)} tickers "
                f"using {self.strategy.name} strategy"
            )

            return {
                "status": "success",
                "filtered_tickers": filtered_tickers,
                "total_scanned": len(tickers),
                "total_filtered": len(filtered_tickers),
                "filter_details": filter_details,
                "strategy": self.strategy.name,
            }

        except Exception as e:
            logger.error(f"Error during filtering: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "filtered_tickers": [],
                "total_scanned": len(tickers),
                "total_filtered": 0,
                "filter_details": {},
            }

    def set_historical_date(self, historical_date: Any) -> None:
        """Set historical date for price fetcher.

        Args:
            historical_date: Date object or string
        """
        if hasattr(self.price_fetcher, "set_historical_date"):
            self.price_fetcher.set_historical_date(historical_date)
            logger.debug(f"Set historical date {historical_date} on FilterOrchestrator")
