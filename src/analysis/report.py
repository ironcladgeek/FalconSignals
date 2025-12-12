"""Report generation for daily market analysis and signals."""

from collections import defaultdict
from datetime import datetime
from typing import Any

from src.analysis.models import (
    DailyReport,
    InvestmentSignal,
    TechnicalIndicators,
)
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
        "Filtering strategies (anomaly/volume detection)",
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
        analyzed_category: str | None = None,
        analyzed_market: str | None = None,
        analyzed_tickers_specified: list[str] | None = None,
        initial_tickers: list[str] | None = None,
        tickers_with_anomalies: list[str] | None = None,
        force_full_analysis_used: bool = False,
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
            analyzed_category: Category analyzed (e.g., us_tech_software)
            analyzed_market: Market analyzed (e.g., us, nordic, eu, global)
            analyzed_tickers_specified: Specific tickers analyzed (if --ticker was used)
            initial_tickers: Complete list of initial tickers before filtering
            tickers_with_anomalies: Tickers with anomalies from Stage 1 market scan (LLM mode)
            force_full_analysis_used: Whether --force-full-analysis flag was provided

        Returns:
            Daily report object
        """
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        # Extract analysis_date from first signal if available (for backtesting)
        analysis_date = None
        if signals:
            analysis_date = signals[0].analysis_date

        portfolio_alerts = portfolio_alerts or []
        key_news = key_news or []
        analyzed_tickers_specified = analyzed_tickers_specified or []
        initial_tickers = initial_tickers or []
        tickers_with_anomalies = tickers_with_anomalies or []

        # Filter strong signals (confidence >= 70)
        strong_signals = [s for s in signals if s.confidence >= 70]
        moderate_signals = [s for s in signals if 50 <= s.confidence < 70]

        # Take top 10 strong signals and top 10 moderate signals
        top_signals = strong_signals[:10]
        top_moderate_signals = moderate_signals[:10]

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
            analysis_date=analysis_date,
            market_overview=market_overview or self._generate_market_overview(signals),
            market_indices={},  # Can be populated with actual index data
            strong_signals=top_signals,
            moderate_signals=top_moderate_signals,
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
            analyzed_category=analyzed_category,
            analyzed_market=analyzed_market,
            analyzed_tickers_specified=analyzed_tickers_specified,
            initial_tickers=initial_tickers,
            tickers_with_anomalies=tickers_with_anomalies,
            force_full_analysis_used=force_full_analysis_used,
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
        md.append(f"*Generated: {report.report_time.strftime('%Y-%m-%d %H:%M:%S')}*")

        # Add analysis date if present (for backtesting transparency)
        if report.analysis_date:
            md.append(f"*Analysis Date: {report.analysis_date}*\n")
        else:
            md.append("")  # Empty line for spacing

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

        # Analysis Context
        md.append("\n## Analysis Context\n")
        context_items = []
        if report.analyzed_category:
            context_items.append(f"- **Category:** {report.analyzed_category.upper()}")
        if report.analyzed_market:
            context_items.append(f"- **Market:** {report.analyzed_market.upper()}")
        if report.analyzed_tickers_specified:
            context_items.append(
                f"- **Specified Tickers:** {', '.join(report.analyzed_tickers_specified)}"
            )
        if report.initial_tickers:
            context_items.append(
                f"- **Initial Instruments:** {len(report.initial_tickers)} tickers"
            )

        md.append("\n".join(context_items))
        if context_items:
            md.append("")

        # Stage 1 Anomaly Detection (LLM mode only)
        if report.analysis_mode == "llm" and report.tickers_with_anomalies:
            md.append("\n### Market Scan Results\n")
            md.append(f"Anomalies detected in **{len(report.tickers_with_anomalies)}** out of ")
            md.append(f"**{len(report.initial_tickers)}** instruments:\n")
            if len(report.tickers_with_anomalies) <= 20:
                md.append(f"\n{', '.join(report.tickers_with_anomalies)}\n")
            else:
                md.append(
                    f"\n{', '.join(report.tickers_with_anomalies[:15])} ... and {len(report.tickers_with_anomalies) - 15} more\n"
                )
        elif report.analysis_mode == "llm" and not report.tickers_with_anomalies:
            md.append("\n### Market Scan Results\n")
            if report.force_full_analysis_used:
                md.append(
                    "No anomalies detected (full analysis performed due to --force-full-analysis)\n"
                )
            else:
                md.append("No anomalies detected (all instruments analyzed)\n")

        # Market Overview
        md.append("\n## Market Overview\n")
        md.append(report.market_overview)
        md.append("")

        # Strong Signals
        all_displayed_signals = len(report.strong_signals) + len(report.moderate_signals)
        md.append(f"## 🎯 Investment Opportunities ({all_displayed_signals} signals)\n")

        # Strong signals section
        if report.strong_signals:
            md.append("### 🚀 Strong Buy Signals\n")
            for signal in report.strong_signals:
                md.append(self._format_signal_markdown(signal))

        # Moderate signals section
        if report.moderate_signals:
            md.append("\n### ⏸️ Moderate Hold Signals\n")
            for signal in report.moderate_signals:
                md.append(self._format_signal_markdown(signal))

        if not report.strong_signals and not report.moderate_signals:
            md.append("No signals identified.\n")

        # Allocation Suggestion
        if report.allocation_suggestion:
            md.append("\n## 💼 Suggested Portfolio Allocation\n")
            md.append(f"- **Total Capital:** €{report.allocation_suggestion.total_capital:,.0f}\n")
            md.append(
                f"- **Diversification Score:** {report.allocation_suggestion.diversification_score}%\n"
            )
            md.append(
                f"- **Capital to Allocate:** €{report.allocation_suggestion.total_allocated:,.0f} "
                f"({report.allocation_suggestion.total_allocated_pct}%)\n"
            )
            md.append(f"- **Unallocated:** €{report.allocation_suggestion.unallocated:,.0f}\n")

            # Create mapping of ticker to recommendation from signals
            signal_map = {s.ticker: s.recommendation.value.upper() for s in report.strong_signals}

            md.append("\n### Suggested Positions")
            md.append("| Ticker | Amount (€) | Percentage | Recommendation |")
            md.append("|--------|-----------|-----------|----------------|")
            for pos in report.allocation_suggestion.suggested_positions:
                recommendation = signal_map.get(pos.ticker, "HOLD")
                md.append(
                    f"| {pos.ticker} | €{pos.eur:,.0f} | {pos.percentage}% | {recommendation} |"
                )
            md.append("")

        # Portfolio Alerts
        if report.portfolio_alerts:
            md.append("\n## 🚨 Portfolio Alerts\n")
            for alert in report.portfolio_alerts:
                md.append(f"- **{alert.get('ticker', 'ALERT')}:** {alert.get('message', '')}\n")
            md.append("")

        # Key News
        if report.key_news:
            md.append("\n## 📰 Key News & Events\n")
            for item in report.key_news[:10]:  # Top 10 news items
                ticker = item.get("ticker", "MARKET")
                title = item.get("title", "")
                sentiment = item.get("sentiment", "neutral")
                md.append(f"- **{ticker}:** {title} (*{sentiment}*)\n")
            md.append("")

        # Watchlist Changes
        md.append("\n## 📋 Watchlist Changes\n")
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
        md.append("\n## 📊 Summary\n")
        md.append(f"- **Signals Analyzed:** {report.total_signals_generated}\n")
        md.append(f"- **Strong Signals:** {report.strong_signals_count}\n")
        md.append(f"- **Moderate Signals:** {report.moderate_signals_count}\n")
        md.append(f"- **Next Update:** {report.next_update}\n\n")

        # Initial Instruments List (reference section)
        if report.initial_tickers:
            md.append("\n## 📑 Initial Instruments List\n")
            md.append(
                f"Complete list of {len(report.initial_tickers)} instruments analyzed in this session:\n\n"
            )
            # Display in formatted columns for readability
            tickers = report.initial_tickers
            cols = 10  # Show 10 tickers per row
            for i in range(0, len(tickers), cols):
                row = tickers[i : i + cols]
                md.append(", ".join(f"`{t}`" for t in row) + "\n")
            md.append("")

        # Disclaimers
        if report.disclaimers:
            md.append("\n## ⚖️ Important Disclaimers\n")
            for disclaimer in report.disclaimers:
                md.append(f"- {disclaimer}\n")
            md.append("")

        # Data Sources
        md.append("\n## 📚 Data Sources\n")
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
    def _format_recommendation_with_color(recommendation: str) -> str:
        """Format recommendation with emoji and color.

        Args:
            recommendation: Recommendation string

        Returns:
            Formatted recommendation with emoji
        """
        rec_upper = recommendation.upper()
        if "BUY" in rec_upper:
            emoji = "🟢"  # Green circle for BUY
        elif "SELL" in rec_upper:
            emoji = "🔴"  # Red circle for SELL
        else:
            emoji = "🟡"  # Yellow circle for HOLD
        return f"{emoji} {rec_upper}"

    @staticmethod
    def _format_risk_level_with_color(level: str) -> str:
        """Format risk level with emoji and color.

        Args:
            level: Risk level string

        Returns:
            Formatted risk level with emoji
        """
        level_lower = level.lower()
        if "very_high" in level_lower or "very high" in level_lower:
            emoji = "🔴"  # Red circle
        elif "high" in level_lower:
            emoji = "🟠"  # Orange circle
        elif "medium" in level_lower:
            emoji = "🔵"  # Blue circle
        else:
            emoji = "🟢"  # Green circle for low
        return f"{emoji} {level}"

    @staticmethod
    def _format_signal_markdown(signal: InvestmentSignal) -> str:
        """Format single signal as Markdown.

        Args:
            signal: Investment signal

        Returns:
            Markdown formatted signal
        """
        # Map currency codes to symbols
        currency_symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CHF": "CHF",
            "SEK": "kr",
            "NOK": "kr",
            "DKK": "kr",
        }
        currency_symbol = currency_symbols.get(signal.currency, signal.currency)

        # Format recommendation with emoji
        recommendation_formatted = ReportGenerator._format_recommendation_with_color(
            signal.recommendation.value
        )

        # Format risk level with emoji
        risk_level_formatted = ReportGenerator._format_risk_level_with_color(
            signal.risk.level.value
        )

        lines = [
            f"\n### {signal.ticker} - {signal.name}\n",
            "| | |\n",
            "|---|---|\n",
            f"| **Recommendation** | {recommendation_formatted} |\n",
            f"| **Confidence** | {signal.confidence}% |\n",
            f"| **Final Score** | {signal.final_score}/100 |\n",
            f"| **Price** | {currency_symbol}{signal.current_price:.2f} |\n",
            f"| **Time Horizon** | {signal.time_horizon} |\n",
            f"| **Expected Return** | {signal.expected_return_min:.1f}% - {signal.expected_return_max:.1f}% |\n",
            f"| **Risk Level** | {risk_level_formatted} |\n",
            f"| **Volatility** | {signal.risk.volatility} |\n\n",
            "📊 **Component Scores:**\n",
            f"- Technical: {signal.scores.technical:.2f}/100\n",
            f"- Fundamental: {signal.scores.fundamental:.2f}/100\n",
            f"- Sentiment: {signal.scores.sentiment:.2f}/100\n\n",
            "💡 **Key Reasons:**\n",
        ]

        for reason in signal.key_reasons:
            lines.append(f"- {reason}\n")

        if signal.risk.flags:
            lines.append("\n⚠️ **Risk Flags:**\n")
            for flag in signal.risk.flags:
                lines.append(f"- {flag}\n")

        if signal.rationale:
            lines.append("\n📝 **Detailed Rationale:**\n")
            lines.append(f"{signal.rationale}\n")

        # Add metadata tables if available
        metadata_tables = format_metadata_tables(signal)
        if metadata_tables:
            lines.append("\n## Analysis Details\n\n")
            lines.append(metadata_tables)

        if signal.allocation:
            lines.append(
                f"\n💰 **Suggested Allocation:** €{signal.allocation.eur:,.0f} "
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


def format_metadata_tables(signal: InvestmentSignal) -> str:
    """Format signal metadata as markdown tables.

    Args:
        signal: Investment signal with metadata

    Returns:
        Markdown-formatted tables string
    """
    if not signal.metadata:
        return ""

    sections = []

    # Technical Indicators Table
    if signal.metadata.technical_indicators:
        tech = signal.metadata.technical_indicators
        sections.append("### Technical Indicators\n")
        sections.append("| Indicator | Value |")
        sections.append("|-----------|-------|")

        # GENERIC DISPLAY: Automatically format all indicators from dynamic fields
        # This works for ANY indicator without code changes!
        indicator_rows = _format_technical_indicators_generic(tech)
        sections.extend(indicator_rows)

        # Volume (special case - not a technical indicator)
        if tech.volume_avg is not None:
            sections.append(f"| Avg Volume (20d) | {tech.volume_avg:,} |")

        sections.append("")

    # Fundamental Metrics Table
    if signal.metadata.fundamental_metrics:
        fund = signal.metadata.fundamental_metrics
        sections.append("### Fundamental Metrics\n")
        sections.append("| Metric | Value |")
        sections.append("|--------|-------|")

        if fund.pe_ratio is not None:
            sections.append(f"| P/E Ratio | {fund.pe_ratio:.2f} |")
        if fund.pb_ratio is not None:
            sections.append(f"| P/B Ratio | {fund.pb_ratio:.2f} |")
        if fund.ps_ratio is not None:
            sections.append(f"| P/S Ratio | {fund.ps_ratio:.2f} |")
        if fund.peg_ratio is not None:
            sections.append(f"| PEG Ratio | {fund.peg_ratio:.2f} |")
        if fund.ev_ebitda is not None:
            sections.append(f"| EV/EBITDA | {fund.ev_ebitda:.2f} |")
        if fund.profit_margin is not None:
            sections.append(f"| Profit Margin | {fund.profit_margin:.1f}% |")
        if fund.operating_margin is not None:
            sections.append(f"| Operating Margin | {fund.operating_margin:.1f}% |")
        if fund.roe is not None:
            sections.append(f"| ROE | {fund.roe:.1f}% |")
        if fund.roa is not None:
            sections.append(f"| ROA | {fund.roa:.1f}% |")
        if fund.debt_to_equity is not None:
            sections.append(f"| Debt/Equity | {fund.debt_to_equity:.2f} |")
        if fund.current_ratio is not None:
            sections.append(f"| Current Ratio | {fund.current_ratio:.2f} |")
        if fund.revenue_growth is not None:
            sections.append(f"| Revenue Growth | {fund.revenue_growth:+.1f}% |")
        if fund.earnings_growth is not None:
            sections.append(f"| Earnings Growth | {fund.earnings_growth:+.1f}% |")

        sections.append("")

    # Analyst Info Table
    if signal.metadata.analyst_info:
        analyst = signal.metadata.analyst_info
        sections.append("### Analyst Ratings\n")
        sections.append("| Metric | Value |")
        sections.append("|--------|-------|")

        if analyst.num_analysts is not None:
            sections.append(f"| Number of Analysts | {analyst.num_analysts} |")
        if analyst.consensus_rating:
            sections.append(f"| Consensus | {analyst.consensus_rating.replace('_', ' ').title()} |")

        # Rating distribution
        if any([analyst.strong_buy, analyst.buy, analyst.hold, analyst.sell, analyst.strong_sell]):
            ratings = []
            if analyst.strong_buy:
                ratings.append(f"Strong Buy: {analyst.strong_buy}")
            if analyst.buy:
                ratings.append(f"Buy: {analyst.buy}")
            if analyst.hold:
                ratings.append(f"Hold: {analyst.hold}")
            if analyst.sell:
                ratings.append(f"Sell: {analyst.sell}")
            if analyst.strong_sell:
                ratings.append(f"Strong Sell: {analyst.strong_sell}")
            sections.append(f"| Distribution | {' / '.join(ratings)} |")

        if analyst.price_target is not None:
            sections.append(f"| Avg Price Target | ${analyst.price_target:.2f} |")
        if analyst.price_target_low is not None and analyst.price_target_high is not None:
            sections.append(
                f"| Price Target Range | ${analyst.price_target_low:.2f} - ${analyst.price_target_high:.2f} |"
            )

        sections.append("")

    # Sentiment Info Table
    if signal.metadata.sentiment_info:
        sent = signal.metadata.sentiment_info
        sections.append("### News & Sentiment\n")
        sections.append("| Metric | Value |")
        sections.append("|--------|-------|")

        if sent.news_count is not None:
            sections.append(f"| News Articles | {sent.news_count} |")
        if sent.sentiment_score is not None:
            sentiment_label = (
                "Positive"
                if sent.sentiment_score > 0.1
                else "Negative"
                if sent.sentiment_score < -0.1
                else "Neutral"
            )
            sections.append(f"| Sentiment | {sentiment_label} ({sent.sentiment_score:+.2f}) |")

        if any([sent.positive_news, sent.negative_news, sent.neutral_news]):
            breakdown = []
            if sent.positive_news:
                breakdown.append(f"Positive: {sent.positive_news}")
            if sent.neutral_news:
                breakdown.append(f"Neutral: {sent.neutral_news}")
            if sent.negative_news:
                breakdown.append(f"Negative: {sent.negative_news}")
            sections.append(f"| News Breakdown | {' / '.join(breakdown)} |")

        sections.append("")

    return "\n".join(sections)


def _format_technical_indicators_generic(tech: "TechnicalIndicators") -> list[str]:
    """Format technical indicators using GENERIC approach.

    This function automatically displays ANY indicator without code changes!
    It works by:
    1. Grouping fields by base indicator name (e.g., macd_12_26_9_*)
    2. Detecting multi-component indicators (line/signal, upper/lower, etc.)
    3. Formatting based on indicator type patterns

    Adding Ichimoku Cloud or any new indicator requires ZERO code changes -
    just add to config and this will display it!

    Args:
        tech: TechnicalIndicators model with dynamic fields

    Returns:
        List of markdown table rows
    """

    rows = []

    # Get all field names except volume_avg (handled separately)
    # Pydantic models with extra="allow" store extra fields in model_extra
    all_fields = {}

    # Get defined fields
    for field_name in tech.model_fields.keys():
        if field_name == "volume_avg":
            continue
        value = getattr(tech, field_name, None)
        if value is not None and isinstance(value, (int, float)):
            all_fields[field_name] = value

    # Get extra fields (dynamically added indicators)
    if hasattr(tech, "__pydantic_extra__") and tech.__pydantic_extra__:
        for field_name, value in tech.__pydantic_extra__.items():
            if value is not None and isinstance(value, (int, float)):
                all_fields[field_name] = value

    # Group fields by base indicator (e.g., macd_12_26_9_line/signal → macd_12_26_9)
    indicator_groups = defaultdict(dict)
    for field_name, value in all_fields.items():
        # Try to split into base_indicator_component
        # Pattern: indicator_params_component (e.g., macd_12_26_9_line, bbands_20_2_upper)
        parts = field_name.rsplit("_", 1)
        if len(parts) == 2:
            base, component = parts
            indicator_groups[base][component] = value
        else:
            # Simple indicator (e.g., rsi_14)
            indicator_groups[field_name]["value"] = value

    # Define display order and formatting rules
    INDICATOR_ORDER = [
        "rsi",
        "macd",
        "bbands",
        "sma",
        "ema",
        "adx",
        "stoch",
        "atr",
        "ichimoku",
        "obv",
        "cmf",
        "vwap",  # Future-proof for common indicators
    ]

    # Sort indicators by predefined order (if defined), then alphabetically
    def sort_key(item):
        base_name = item[0]
        # Extract indicator type (rsi, macd, etc.) from base_name
        indicator_type = base_name.split("_")[0]
        if indicator_type in INDICATOR_ORDER:
            return (INDICATOR_ORDER.index(indicator_type), base_name)
        return (len(INDICATOR_ORDER), base_name)

    sorted_groups = sorted(indicator_groups.items(), key=sort_key)

    # Format each indicator group
    for base_name, components in sorted_groups:
        indicator_type = base_name.split("_")[0]
        params = "_".join(base_name.split("_")[1:])  # Extract parameters (14, 12_26_9, etc.)

        # Detect indicator pattern and format accordingly
        if "value" in components and len(components) == 1:
            # Simple single-value indicator (RSI, SMA, EMA, ATR)
            value = components["value"]
            display_name = _format_indicator_name(indicator_type, params)

            # Price-based indicators get $ formatting
            if indicator_type in ["sma", "ema", "atr", "vwap"]:
                rows.append(f"| {display_name} | ${value:.2f} |")
            else:
                rows.append(f"| {display_name} | {value:.2f} |")

        elif "line" in components and "signal" in components:
            # MACD-like indicators with line/signal/histogram
            display_name = _format_indicator_name(indicator_type, params)
            display_values = [f"{components['line']:.2f}", f"{components['signal']:.2f}"]
            if "histogram" in components:
                display_values.append(f"{components['histogram']:.2f}")
            rows.append(f"| {display_name} | {' / '.join(display_values)} |")

        elif "upper" in components and "lower" in components:
            # Band indicators (Bollinger Bands, Ichimoku Senkou)
            display_name = _format_indicator_name(indicator_type, params)
            display_values = []
            if "lower" in components:
                display_values.append(f"${components['lower']:.2f}")
            if "middle" in components:
                display_values.append(f"${components['middle']:.2f}")
            if "upper" in components:
                display_values.append(f"${components['upper']:.2f}")
            rows.append(f"| {display_name} | {' / '.join(display_values)} |")

        elif indicator_type == "adx" and ("dmp" in components or "dmn" in components):
            # ADX with directional movement
            display_name = _format_indicator_name("adx", params)
            # The main ADX value is stored without suffix (handled by flattening)
            adx_val = components.get(base_name.split("_")[-1], components.get("value", 0))
            display = f"{adx_val:.2f}"
            if "dmp" in components and "dmn" in components:
                display += f" (+DI: {components['dmp']:.2f}, -DI: {components['dmn']:.2f})"
            rows.append(f"| {display_name} | {display} |")

        elif indicator_type == "stoch" and "k" in components:
            # Stochastic with %K and %D
            display_name = _format_indicator_name("stoch", params)
            display = f"%K: {components['k']:.2f}"
            if "d" in components:
                display += f", %D: {components['d']:.2f}"
            rows.append(f"| {display_name} | {display} |")

        else:
            # Generic multi-component display (works for Ichimoku, future indicators)
            display_name = _format_indicator_name(indicator_type, params)
            component_strs = [f"{k}: {v:.2f}" for k, v in sorted(components.items())]
            rows.append(f"| {display_name} | {', '.join(component_strs)} |")

    return rows


def _format_indicator_name(indicator_type: str, params: str) -> str:
    """Format indicator display name with parameters in parentheses.

    Examples:
    - ("rsi", "14") → "RSI (14)"
    - ("macd", "12_26_9") → "MACD (12, 26, 9)"
    - ("bbands", "20_2") → "Bollinger Bands (20, 2.0)"
    - ("ichimoku", "9_26_52") → "Ichimoku Cloud (9, 26, 52)"
    """
    # Indicator display names
    DISPLAY_NAMES = {
        "rsi": "RSI",
        "macd": "MACD",
        "bbands": "Bollinger Bands",
        "sma": "SMA",
        "ema": "EMA",
        "adx": "ADX",
        "stoch": "Stochastic",
        "atr": "ATR",
        "ichimoku": "Ichimoku Cloud",
        "obv": "OBV",
        "cmf": "CMF",
        "vwap": "VWAP",
    }

    display_name = DISPLAY_NAMES.get(indicator_type, indicator_type.upper())

    if params:
        # Convert 12_26_9 → "12, 26, 9"
        # Convert 20_2 → "20, 2.0" (special case for Bollinger Bands std dev)
        param_parts = params.split("_")
        if indicator_type == "bbands" and len(param_parts) == 2:
            # Format std dev as decimal
            formatted_params = f"{param_parts[0]}, {float(param_parts[1]):.1f}"
        else:
            formatted_params = ", ".join(param_parts)
        return f"{display_name} ({formatted_params})"

    return display_name
