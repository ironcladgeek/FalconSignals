"""Market Scanner agent for identifying trading opportunities."""

from typing import Any

import typer

from src.agents.base import AgentConfig, BaseAgent
from src.tools.fetchers import PriceFetcherTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MarketScannerAgent(BaseAgent):
    """Agent for scanning markets and identifying anomalies."""

    def __init__(
        self, tools: list = None, provider_name: str = None, fixture_path: str = None, config=None
    ):
        """Initialize Market Scanner agent.

        Args:
            tools: Optional list of tools
            provider_name: Data provider to use (default: yahoo_finance)
            fixture_path: Path to fixture directory (required if provider_name is 'fixture')
            config: Configuration object with analysis settings
        """
        agent_config = AgentConfig(
            role="Market Scanner",
            goal="Identify financial instruments with significant price movements and anomalies that warrant further analysis",
            backstory=(
                "You are an expert market analyst with deep knowledge of technical patterns. "
                "You excel at detecting emerging trends, unusual volume patterns, and price movements "
                "that signal potential trading opportunities. Your keen eye for detail helps identify "
                "instruments that deserve deeper analysis."
            ),
        )
        super().__init__(
            agent_config,
            tools
            or [
                PriceFetcherTool(
                    provider_name=provider_name, fixture_path=fixture_path, config=config
                )
            ],
        )

    def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """Execute market scanning task.

        Args:
            task: Task description
            context: Context with tickers to scan

        Returns:
            Scanning results with flagged instruments
        """
        try:
            context = context or {}
            tickers = context.get("tickers", [])

            if not tickers:
                return {
                    "status": "error",
                    "message": "No tickers provided for scanning",
                    "instruments": [],
                }

            logger.debug(f"Scanning {len(tickers)} instruments for anomalies")

            scanned_instruments = []

            # Get price fetcher tool
            price_fetcher = next(
                (t for t in self.tools if hasattr(t, "name") and t.name == "PriceFetcher"),
                None,
            )

            if not price_fetcher:
                return {
                    "status": "error",
                    "message": "Price fetcher tool not available",
                    "instruments": [],
                }

            # Set historical date if provided in context
            if "analysis_date" in context and hasattr(price_fetcher, "set_historical_date"):
                price_fetcher.set_historical_date(context["analysis_date"])
                logger.debug(f"Set historical date {context['analysis_date']} for market scanner")

            # Scan each ticker with progress bar
            with typer.progressbar(
                tickers, label="🔍 Scanning instruments", show_pos=True, show_percent=True
            ) as progress:
                for ticker in progress:
                    # Use configured lookback period for historical data
                    lookback_days = context.get("historical_data_lookback_days", 730)
                    result = price_fetcher.run(ticker, days_back=lookback_days)

                    if "error" in result:
                        logger.debug(f"Error scanning {ticker}: {result['error']}")
                        continue

                    prices = result.get("prices", [])
                    if len(prices) < 5:
                        continue

                    # Analyze for anomalies
                    anomalies = self._detect_anomalies(ticker, prices)

                    if anomalies:
                        scanned_instruments.append(
                            {
                                "ticker": ticker,
                                "latest_price": result.get("latest_price"),
                                "anomalies": anomalies,
                                "requires_analysis": True,
                            }
                        )

            logger.debug(f"Found {len(scanned_instruments)} instruments with anomalies")

            return {
                "status": "success",
                "instruments": scanned_instruments,
                "total_scanned": len(tickers),
                "anomalies_found": len(scanned_instruments),
            }

        except Exception as e:
            logger.error(f"Error during market scanning: {e}")
            return {
                "status": "error",
                "message": str(e),
                "instruments": [],
            }

    @staticmethod
    def _detect_anomalies(ticker: str, prices: list[dict[str, Any]]) -> list[str]:
        """Detect anomalies in price data.

        Args:
            ticker: Stock ticker
            prices: List of price data points

        Returns:
            List of anomalies detected
        """
        anomalies = []

        if len(prices) < 5:
            return anomalies

        # Calculate recent changes
        latest = prices[-1]
        prev_day = prices[-2]
        week_ago = prices[-5] if len(prices) >= 5 else prices[0]

        # Price change detection
        daily_change = (
            (latest["close_price"] - prev_day["close_price"]) / prev_day["close_price"] * 100
        )
        weekly_change = (
            (latest["close_price"] - week_ago["close_price"]) / week_ago["close_price"] * 100
        )

        if abs(daily_change) > 5:
            anomalies.append(f"Large daily move: {daily_change:.2f}%")

        if abs(weekly_change) > 15:
            anomalies.append(f"Large weekly move: {weekly_change:.2f}%")

        # Volume anomaly
        avg_volume = sum(p["volume"] for p in prices[-5:]) / 5
        current_volume = latest["volume"]

        if current_volume > avg_volume * 1.5:
            anomalies.append(f"Unusual volume spike: {current_volume / avg_volume:.1f}x average")

        # Price at new highs/lows
        high_30d = max(p["high_price"] for p in prices[-30:])
        low_30d = min(p["low_price"] for p in prices[-30:])

        if latest["high_price"] >= high_30d:
            anomalies.append("Trading at 30-day high")

        if latest["low_price"] <= low_30d:
            anomalies.append("Trading at 30-day low")

        return anomalies
