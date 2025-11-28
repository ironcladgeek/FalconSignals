"""Report generation for daily market analysis and signals."""

from datetime import datetime
from typing import Any

from src.analysis.models import DailyReport, InvestmentSignal
from src.utils.llm_check import check_llm_configuration
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generates daily analysis reports with signals and recommendations."""

    # Standard disclaimers
    STANDARD_DISCLAIMERS = [
        "This report is for informational purposes only and does not constitute investment advice.",
        "Past performance does not guarantee future results.",
        "All investments carry risk, including potential loss of principal.",
        "Consult with a financial advisor before making investment decisions.",
        "Market conditions can change rapidly; signals may become outdated.",
    ]

    # Data sources
    DATA_SOURCES = [
        "Yahoo Finance (price data)",
        "Finnhub (news and sentiment)",
        "Technical indicators (internal calculation)",
        "Market scanner (anomaly detection)",
    ]

    def __init__(self, include_disclaimers: bool = True):
        """Initialize report generator.

        Args:
            include_disclaimers: Whether to include legal disclaimers
        """
        self.include_disclaimers = include_disclaimers
        logger.debug("Report generator initialized")

    def generate_daily_report(
        self,
        signals: list[InvestmentSignal],
        market_overview: str = "",
        portfolio_alerts: list[dict[str, str]] | None = None,
        key_news: list[dict[str, str]] | None = None,
        allocation_suggestion: Any = None,
        report_date: str | None = None,
        analysis_mode: str = "rule_based",
    ) -> DailyReport:
        """Generate daily market analysis report.

        Args:
            signals: List of investment signals
            market_overview: Summary of market conditions
            portfolio_alerts: Important alerts for existing positions
            key_news: Important news items
            allocation_suggestion: Portfolio allocation suggestion
            report_date: Report date (YYYY-MM-DD), uses today if not provided
            analysis_mode: Analysis mode used ("llm" or "rule_based")

        Returns:
            Daily report object
        """
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        portfolio_alerts = portfolio_alerts or []
        key_news = key_news or []

        # Filter strong signals (confidence >= 70)
        strong_signals = [s for s in signals if s.confidence >= 70]
        moderate_signals = [s for s in signals if 50 <= s.confidence < 70]

        # Take top 10 strong signals
        top_signals = strong_signals[:10]

        # Generate watchlist changes
        watchlist_additions = [
            s.ticker for s in strong_signals if s.recommendation in ["buy", "strong_buy"]
        ][:5]
        watchlist_removals = [
            s.ticker for s in signals if s.recommendation in ["sell", "strong_sell"]
        ][:3]

        # Create report
        report = DailyReport(
            report_date=report_date,
            report_time=datetime.now(),
            market_overview=market_overview or self._generate_market_overview(signals),
            market_indices={},  # Can be populated with actual index data
            strong_signals=top_signals,
            portfolio_alerts=portfolio_alerts,
            key_news=key_news,
            watchlist_additions=watchlist_additions,
            watchlist_removals=watchlist_removals,
            allocation_suggestion=allocation_suggestion,
            total_signals_generated=len(signals),
            strong_signals_count=len(strong_signals),
            moderate_signals_count=len(moderate_signals),
            disclaimers=self.STANDARD_DISCLAIMERS if self.include_disclaimers else [],
            data_sources=self.DATA_SOURCES,
            next_update=self._calculate_next_update(report_date),
            analysis_mode=analysis_mode,
        )

        logger.debug(
            f"Report generated for {report_date}: {len(strong_signals)} strong signals, "
            f"{len(moderate_signals)} moderate signals"
        )

        return report

    def to_markdown(self, report: DailyReport) -> str:
        """Convert report to Markdown format.

        Args:
            report: Daily report object

        Returns:
            Markdown formatted report
        """
        md = []

        # Header
        md.append(f"# Investment Analysis Report - {report.report_date}")
        md.append(f"*Generated: {report.report_time.strftime('%Y-%m-%d %H:%M:%S')}*\n")

        # Add analysis mode indicator
        if report.analysis_mode == "llm":
            # LLM mode - check which provider
            llm_configured, provider = check_llm_configuration()
            if llm_configured:
                md.append(f"*Analysis powered by {provider} AI*\n")
            else:
                md.append("*Analysis: LLM mode (fallback to rule-based)*\n")
        else:
            # Rule-based mode
            md.append("*Analysis: Rule-based (technical indicators & fundamental metrics)*\n")

        # Market Overview
        md.append("## Market Overview\n")
        md.append(report.market_overview)
        md.append("")

        # Strong Signals
        md.append(f"## Investment Opportunities ({report.strong_signals_count} signals)\n")
        if report.strong_signals:
            for signal in report.strong_signals:
                md.append(self._format_signal_markdown(signal))
        else:
            md.append("No strong signals identified.\n")

        # Allocation Suggestion
        if report.allocation_suggestion:
            md.append("\n## Suggested Portfolio Allocation\n")
            md.append(f"- **Total Capital:** €{report.allocation_suggestion.total_capital:,.0f}\n")
            md.append(
                f"- **Diversification Score:** {report.allocation_suggestion.diversification_score}%\n"
            )
            md.append(
                f"- **Capital to Allocate:** €{report.allocation_suggestion.total_allocated:,.0f} "
                f"({report.allocation_suggestion.total_allocated_pct}%)\n"
            )
            md.append(f"- **Unallocated:** €{report.allocation_suggestion.unallocated:,.0f}\n\n")

            md.append("### Suggested Positions\n")
            md.append("| Ticker | Amount (€) | Percentage | Action |\n")
            md.append("|--------|-----------|-----------|--------|\n")
            for pos in report.allocation_suggestion.suggested_positions:
                md.append(f"| {pos.ticker} | €{pos.eur:,.0f} | {pos.percentage}% | BUY |\n")
            md.append("")

        # Portfolio Alerts
        if report.portfolio_alerts:
            md.append("\n## Portfolio Alerts\n")
            for alert in report.portfolio_alerts:
                md.append(f"- **{alert.get('ticker', 'ALERT')}:** {alert.get('message', '')}\n")
            md.append("")

        # Key News
        if report.key_news:
            md.append("\n## Key News & Events\n")
            for item in report.key_news[:10]:  # Top 10 news items
                ticker = item.get("ticker", "MARKET")
                title = item.get("title", "")
                sentiment = item.get("sentiment", "neutral")
                md.append(f"- **{ticker}:** {title} (*{sentiment}*)\n")
            md.append("")

        # Watchlist Changes
        md.append("\n## Watchlist Changes\n")
        if report.watchlist_additions:
            md.append("**Add to watchlist:**\n")
            for ticker in report.watchlist_additions:
                md.append(f"- {ticker}\n")
        if report.watchlist_removals:
            md.append("\n**Remove from watchlist:**\n")
            for ticker in report.watchlist_removals:
                md.append(f"- {ticker}\n")
        md.append("")

        # Summary Statistics
        md.append("\n## Summary\n")
        md.append(f"- **Signals Analyzed:** {report.total_signals_generated}\n")
        md.append(f"- **Strong Signals:** {report.strong_signals_count}\n")
        md.append(f"- **Moderate Signals:** {report.moderate_signals_count}\n")
        md.append(f"- **Next Update:** {report.next_update}\n\n")

        # Disclaimers
        if report.disclaimers:
            md.append("\n## Important Disclaimers\n")
            for disclaimer in report.disclaimers:
                md.append(f"- {disclaimer}\n")
            md.append("")

        # Data Sources
        md.append("\n## Data Sources\n")
        for source in report.data_sources:
            md.append(f"- {source}\n")

        return "\n".join(md)

    def to_json(self, report: DailyReport) -> dict[str, Any]:
        """Convert report to JSON-serializable format.

        Args:
            report: Daily report object

        Returns:
            Dictionary representation
        """
        return report.model_dump(mode="json")

    @staticmethod
    def _format_signal_markdown(signal: InvestmentSignal) -> str:
        """Format single signal as Markdown.

        Args:
            signal: Investment signal

        Returns:
            Markdown formatted signal
        """
        lines = [
            f"\n### {signal.ticker} - {signal.name}\n",
            f"**Recommendation:** {signal.recommendation.value.upper()} "
            f"| **Confidence:** {signal.confidence}%\n",
            f"**Final Score:** {signal.final_score}/100 | **Price:** €{signal.current_price:.2f}\n",
            f"**Time Horizon:** {signal.time_horizon} "
            f"| **Expected Return:** {signal.expected_return_min:.1f}% - {signal.expected_return_max:.1f}%\n\n",
            "**Component Scores:**\n",
            f"- Technical: {signal.scores.technical}/100\n",
            f"- Fundamental: {signal.scores.fundamental}/100\n",
            f"- Sentiment: {signal.scores.sentiment}/100\n\n",
            "**Key Reasons:**\n",
        ]

        for reason in signal.key_reasons:
            lines.append(f"- {reason}\n")

        lines.append(f"\n**Risk Level:** {signal.risk.level.value}\n")
        lines.append(f"**Volatility:** {signal.risk.volatility}\n")

        if signal.risk.flags:
            lines.append("\n**Risk Flags:**\n")
            for flag in signal.risk.flags:
                lines.append(f"- {flag}\n")

        if signal.allocation:
            lines.append(
                f"\n**Suggested Allocation:** €{signal.allocation.eur:,.0f} "
                f"({signal.allocation.percentage}%)\n"
            )

        return "".join(lines)

    @staticmethod
    def _generate_market_overview(signals: list[InvestmentSignal]) -> str:
        """Generate market overview from signals.

        Args:
            signals: List of signals

        Returns:
            Market overview summary
        """
        if not signals:
            return "No signals available for market assessment."

        # Count recommendations
        recommendations = {}
        for signal in signals:
            rec = signal.recommendation.value
            recommendations[rec] = recommendations.get(rec, 0) + 1

        # Generate summary
        buy_count = recommendations.get("strong_buy", 0) + recommendations.get("buy", 0)
        sell_count = recommendations.get("sell", 0) + recommendations.get("strong_sell", 0)
        hold_count = len(signals) - buy_count - sell_count

        sentiment = "Mixed"
        if buy_count > sell_count * 2:
            sentiment = "Bullish"
        elif sell_count > buy_count * 2:
            sentiment = "Bearish"

        overview = (
            f"Market sentiment is **{sentiment}** with {buy_count} buy signals, "
            f"{hold_count} hold signals, and {sell_count} sell signals out of "
            f"{len(signals)} total analyzed instruments."
        )

        return overview

    @staticmethod
    def _calculate_next_update(report_date: str) -> str:
        """Calculate expected time of next update.

        Args:
            report_date: Report date (YYYY-MM-DD)

        Returns:
            Next update time estimate
        """
        try:
            from datetime import datetime, timedelta

            current_date = datetime.strptime(report_date, "%Y-%m-%d")
            next_date = current_date + timedelta(days=1)
            return next_date.strftime("%Y-%m-%d 08:00 UTC")
        except Exception:
            return "Next trading day 08:00 UTC"
