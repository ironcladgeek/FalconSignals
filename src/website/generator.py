"""Website content generator for static site publishing.

Generates markdown pages from analysis data for MkDocs static site.
"""

from datetime import datetime
from pathlib import Path

from src.analysis.models import InvestmentSignal
from src.config import Config
from src.data.repository import RecommendationsRepository, RunSessionRepository
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WebsiteGenerator:
    """Generates static website content from analysis data."""

    def __init__(self, config: Config, db_path: str, output_dir: Path | str):
        """Initialize website generator.

        Args:
            config: Application configuration
            db_path: Path to SQLite database
            output_dir: Output directory for generated markdown files (website/docs/)
        """
        self.config = config
        self.db_path = db_path
        self.output_dir = Path(output_dir)

        # Initialize repositories
        self.recommendations_repo = RecommendationsRepository(db_path)
        self.sessions_repo = RunSessionRepository(db_path)

        logger.info(f"WebsiteGenerator initialized. Output: {self.output_dir}")

    def generate_report_page(
        self,
        signals: list[InvestmentSignal],
        report_date: str,
        metadata: dict | None = None,
    ) -> Path:
        """Generate markdown page for a report (without portfolio info).

        Args:
            signals: List of investment signals
            report_date: Report date (YYYY-MM-DD)
            metadata: Optional metadata (analysis_mode, tickers_analyzed, etc.)

        Returns:
            Path to generated markdown file
        """
        metadata = metadata or {}

        # Organize signals by recommendation type
        strong_buy = [s for s in signals if s.recommendation.value == "strong_buy"]
        buy = [s for s in signals if s.recommendation.value == "buy"]
        hold_bullish = [s for s in signals if s.recommendation.value == "hold_bullish"]
        hold = [s for s in signals if s.recommendation.value == "hold"]
        hold_bearish = [s for s in signals if s.recommendation.value == "hold_bearish"]
        sell = [s for s in signals if s.recommendation.value == "sell"]
        strong_sell = [s for s in signals if s.recommendation.value == "strong_sell"]

        # Generate tags
        tickers = list(set(s.ticker for s in signals))
        signal_types = list(set(s.recommendation.value for s in signals))

        # Build markdown content
        lines = [
            "---",
            "tags:",
        ]

        # Add ticker tags
        for ticker in sorted(tickers):
            lines.append(f"  - {ticker}")

        # Add signal type tags
        for signal_type in sorted(signal_types):
            lines.append(f"  - {signal_type}")

        # Add date tag
        lines.append(f"  - {report_date}")

        lines.extend(
            [
                "---",
                "",
                f"# Market Analysis - {datetime.strptime(report_date, '%Y-%m-%d').strftime('%B %d, %Y')}",
                "",
                f"**Tickers Analyzed:** {len(signals)}  ",
                f"**Strong Signals:** {len(strong_buy) + len(buy)}",
                "",
            ]
        )

        # Strong Buy Signals
        if strong_buy:
            lines.extend(
                [
                    "## 🎯 Strong Buy Signals",
                    "",
                ]
            )
            for signal in strong_buy:
                lines.extend(self._format_signal(signal))

        # Buy Signals
        if buy:
            lines.extend(
                [
                    "## 📈 Buy Signals",
                    "",
                ]
            )
            for signal in buy:
                lines.extend(self._format_signal(signal))

        # Hold Bullish Signals
        if hold_bullish:
            lines.extend(
                [
                    "## ⏸️ Hold (Bullish) Signals",
                    "",
                ]
            )
            for signal in hold_bullish:
                lines.extend(self._format_signal(signal, include_details=True))

        # Hold Signals
        if hold:
            lines.extend(
                [
                    "## ⏸️ Hold Signals",
                    "",
                ]
            )
            for signal in hold:
                lines.extend(self._format_signal(signal, include_details=True))

        # Hold Bearish Signals
        if hold_bearish:
            lines.extend(
                [
                    "## ⏸️ Hold (Bearish) Signals",
                    "",
                ]
            )
            for signal in hold_bearish:
                lines.extend(self._format_signal(signal, include_details=True))

        # Sell Signals
        if sell:
            lines.extend(
                [
                    "## 📉 Sell Signals",
                    "",
                ]
            )
            for signal in sell:
                lines.extend(self._format_signal(signal, include_details=True))

        # Strong Sell Signals
        if strong_sell:
            lines.extend(
                [
                    "## 🔴 Strong Sell Signals",
                    "",
                ]
            )
            for signal in strong_sell:
                lines.extend(self._format_signal(signal, include_details=True))

        # Add tags section
        lines.extend(
            [
                "",
                "## 🏷️ Tags",
                "",
            ]
        )
        for ticker in sorted(tickers):
            lines.append(f"- [{ticker}](../tickers/{ticker}.md)")

        # Add disclaimers
        lines.extend(
            [
                "",
                "---",
                "",
                '!!! warning "Investment Risk"',
                "    This analysis is for informational purposes only and does not constitute investment advice. All investments carry risk, including potential loss of principal. Consult with a financial advisor before making investment decisions.",
            ]
        )

        # Write to file
        report_dir = self.output_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        file_path = report_dir / f"{report_date}.md"
        with open(file_path, "w") as f:
            f.write("\n".join(lines) + "\n")

        logger.info(f"Generated report page: {file_path}")
        return file_path

    def _format_signal(self, signal: InvestmentSignal, include_details: bool = True) -> list[str]:
        """Format investment signal as markdown.

        Args:
            signal: Investment signal
            include_details: Whether to include full details

        Returns:
            List of markdown lines
        """
        recommendation = signal.recommendation.value.upper().replace("_", " ")
        if "BUY" in recommendation:
            symbol = "🟢"
        elif "HOLD" in recommendation:
            symbol = "🟡"
        elif "SELL" in recommendation:
            symbol = "🔴"
        lines = [
            f"#### [{signal.ticker} - {signal.name}]"
            f'(https://finance.yahoo.com/quote/{signal.ticker}/){{:target="_blank"}}',
            "",
            f"**Recommendation:** {symbol} {recommendation}  ",
            f"**Confidence:** {signal.confidence:.0f}%  ",
            f"**Current Price:** ${signal.current_price:.2f}",
            "",
        ]

        if include_details:
            # Add risk level
            if signal.risk:
                lines.extend(
                    [
                        f"**Risk Level:** {signal.risk.level.value.replace('_', ' ').title()}",
                        "",
                    ]
                )

            # Add component scores
            if signal.scores:
                lines.extend(
                    [
                        "**Scores:**",
                        "",
                        f"- Technical: {signal.scores.technical:.0f}/100",
                        f"- Fundamental: {signal.scores.fundamental:.0f}/100",
                        f"- Sentiment: {signal.scores.sentiment:.0f}/100",
                        "",
                    ]
                )

            # Add key reasons section
            if signal.key_reasons:
                lines.extend(
                    [
                        "💡 **Key Reasons:**",
                        "",
                    ]
                )
                for reason in signal.key_reasons:
                    lines.append(f"- {reason}")
                lines.append("")

            # Add risk flags section
            if signal.risk and signal.risk.flags:
                lines.extend(
                    [
                        "⚠️ **Risk Flags:**",
                        "",
                    ]
                )
                for flag in signal.risk.flags:
                    lines.append(f"- {flag}")
                lines.append("")

            # Add analysis summary
            if signal.rationale:
                lines.extend(
                    [
                        "📝 **Detailed Analysis:**",
                        "",
                        signal.rationale,
                        "",
                    ]
                )

            # Add detailed metadata tables if available
            if signal.metadata:
                lines.extend(
                    [
                        '<details markdown="1">',
                        "<summary><strong>📊 Analysis Details</strong> (click to expand)</summary>",
                        "",
                    ]
                )

                # Technical Indicators
                if signal.metadata.technical_indicators:
                    tech = signal.metadata.technical_indicators
                    lines.extend(
                        [
                            "",
                            "**Technical Indicators**",
                            "",
                            "| Indicator | Value |",
                            "|-----------|-------|",
                        ]
                    )

                    # Get all fields dynamically
                    tech_dict = tech.model_dump(exclude_none=True)

                    # Display technical indicators in a readable format
                    for key, value in sorted(tech_dict.items()):
                        if key == "volume_avg":
                            continue  # Skip volume for now

                        # Format the key nicely
                        display_key = key.replace("_", " ").upper()

                        # Format the value
                        if isinstance(value, (int, float)):
                            if abs(value) < 1:
                                formatted_value = f"{value:.4f}"
                            elif abs(value) < 100:
                                formatted_value = f"{value:.2f}"
                            else:
                                formatted_value = f"{value:.0f}"
                            lines.append(f"| {display_key} | {formatted_value} |")
                        else:
                            lines.append(f"| {display_key} | {value} |")

                    lines.append("")

                # Fundamental Metrics
                if signal.metadata.fundamental_metrics:
                    fund = signal.metadata.fundamental_metrics
                    lines.extend(
                        [
                            "**Fundamental Metrics**",
                            "",
                            "| Metric | Value |",
                            "|--------|-------|",
                        ]
                    )

                    # Get all fields dynamically
                    fund_dict = fund.model_dump(exclude_none=True)

                    # Display metrics in a readable format
                    for key, value in sorted(fund_dict.items()):
                        # Format the key nicely
                        display_key = key.replace("_", " ").title()

                        # Format the value based on the metric type
                        if "margin" in key or "roe" in key or "roa" in key or "growth" in key:
                            # Display as percentage
                            formatted_value = (
                                f"{value:.1%}" if isinstance(value, (int, float)) else str(value)
                            )
                        elif "ratio" in key:
                            formatted_value = (
                                f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
                            )
                        elif isinstance(value, (int, float)):
                            formatted_value = f"{value:.2f}"
                        else:
                            formatted_value = str(value)

                        lines.append(f"| {display_key} | {formatted_value} |")

                    lines.append("")

                # Analyst Ratings
                if signal.metadata.analyst_info:
                    analyst = signal.metadata.analyst_info
                    lines.extend(
                        [
                            "**Analyst Ratings**",
                            "",
                            "| Metric | Value |",
                            "|--------|-------|",
                        ]
                    )

                    if analyst.num_analysts is not None:
                        lines.append(f"| Number of Analysts | {analyst.num_analysts} |")
                    if analyst.consensus_rating:
                        lines.append(
                            f"| Consensus | {analyst.consensus_rating.replace('_', ' ').title()} |"
                        )
                    if analyst.strong_buy is not None:
                        lines.append(f"| Strong Buy | {analyst.strong_buy} |")
                    if analyst.buy is not None:
                        lines.append(f"| Buy | {analyst.buy} |")
                    if analyst.hold is not None:
                        lines.append(f"| Hold | {analyst.hold} |")
                    if analyst.sell is not None:
                        lines.append(f"| Sell | {analyst.sell} |")
                    if analyst.strong_sell is not None:
                        lines.append(f"| Strong Sell | {analyst.strong_sell} |")
                    if analyst.price_target is not None:
                        lines.append(f"| Price Target | ${analyst.price_target:.2f} |")

                    lines.append("")

                # Sentiment Info
                if signal.metadata.sentiment_info:
                    sent = signal.metadata.sentiment_info
                    lines.extend(
                        [
                            "**News & Sentiment**",
                            "",
                            "| Metric | Value |",
                            "|--------|-------|",
                        ]
                    )

                    if sent.news_count is not None:
                        lines.append(f"| Total Articles | {sent.news_count} |")
                    if sent.sentiment_score is not None:
                        sign = "+" if sent.sentiment_score >= 0 else ""
                        lines.append(f"| Sentiment Score | {sign}{sent.sentiment_score:.2f} |")
                    if sent.positive_news is not None:
                        lines.append(f"| Positive Articles | {sent.positive_news} |")
                    if sent.neutral_news is not None:
                        lines.append(f"| Neutral Articles | {sent.neutral_news} |")
                    if sent.negative_news is not None:
                        lines.append(f"| Negative Articles | {sent.negative_news} |")

                    lines.append("")

                lines.extend(
                    [
                        "</details>",
                        "",
                    ]
                )

        lines.append("---")
        lines.append("")

        return lines

    def generate_ticker_page(self, ticker: str) -> Path:
        """Generate ticker-specific page with all signals/analysis.

        Args:
            ticker: Ticker symbol

        Returns:
            Path to generated markdown file
        """
        # Get all recommendations for this ticker
        all_recs = self.recommendations_repo.get_recommendations_by_ticker(ticker)

        if not all_recs:
            logger.warning(f"No recommendations found for ticker: {ticker}")
            return None

        # Build markdown content
        lines = [
            "---",
            "tags:",
            f"  - {ticker}",
            "---",
            "",
            f"# {ticker} - Analysis History",
            "",
            "## Recent Signals",
            "",
            "| Date | Recommendation | Confidence | Price | Analysis Mode |",
            "|------|---------------|------------|-------|---------------|",
        ]

        # Sort by date (most recent first)
        sorted_recs = sorted(all_recs, key=lambda x: x.get("analysis_date", ""), reverse=True)

        for rec in sorted_recs[:20]:  # Show last 20 signals
            date = rec.get("analysis_date", "N/A")
            recommendation = rec.get("recommendation", "unknown").replace("_", " ").title()
            confidence = rec.get("confidence", 0)
            price = rec.get("current_price", 0)
            mode = rec.get("analysis_mode", "unknown").replace("_", "-").title()

            lines.append(f"| {date} | {recommendation} | {confidence}% | ${price:.2f} | {mode} |")

        lines.extend(
            [
                "",
                "## Analysis Details",
                "",
                f"Total signals recorded: {len(all_recs)}",
                "",
                "---",
                "",
                f"[View all reports containing {ticker}](../reports/)",
                "",
            ]
        )

        # Write to file
        ticker_dir = self.output_dir / "tickers"
        ticker_dir.mkdir(parents=True, exist_ok=True)

        file_path = ticker_dir / f"{ticker}.md"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"Generated ticker page: {file_path}")
        return file_path

    def generate_index_page(self, recent_reports: list[dict] | None = None) -> Path:
        """Generate homepage with recent reports.

        Args:
            recent_reports: Optional list of recent report metadata

        Returns:
            Path to generated index file
        """
        if recent_reports is None:
            # Get recent analysis dates from recommendations (more accurate than run sessions)
            recent_dates = self.recommendations_repo.get_recent_analysis_dates(limit=5)
            recent_reports = [
                {
                    "date": item["date"],
                    "signals_count": item["signals_count"],
                }
                for item in recent_dates
            ]

        lines = [
            "# Welcome to NordInvest Analysis",
            "",
            "AI-powered financial analysis and investment recommendations.",
            "",
            "## 📊 Recent Analysis",
            "",
        ]

        if recent_reports:
            lines.append("| Date | Signals | View |")
            lines.append("|------|---------|------|")

            for report in recent_reports:
                date = report["date"]
                count = report["signals_count"]
                lines.append(f"| {date} | {count} | [View Report](reports/{date}.md) |")
        else:
            lines.append("*No reports available yet.*")

        lines.extend(
            [
                "",
                "[Browse All Reports](reports/){ .md-button .md-button--primary }",
                "[Browse Tickers](tickers/){ .md-button }",
                "",
                "## ⚠️ Important Disclaimers",
                "",
                '!!! warning "Investment Risk"',
                "    This website is for informational purposes only and does not constitute investment advice. All investments carry risk, including potential loss of principal. Past performance does not guarantee future results. Consult with a financial advisor before making investment decisions.",
                "",
                f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                "",
            ]
        )

        # Write to file
        file_path = self.output_dir / "index.md"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"Updated index page: {file_path}")
        return file_path

    def generate_tag_pages(self) -> dict[str, Path]:
        """Generate tag index pages for filtering content.

        Creates pages for:
        - Ticker tags (e.g., tags/AAPL.md)
        - Signal type tags (e.g., tags/buy.md, tags/strong_buy.md)
        - Date tags (e.g., tags/2025-12-10.md)

        Returns:
            Dictionary mapping tag name to generated file path
        """
        logger.info("Generating tag pages...")

        tag_dir = self.output_dir / "tags"
        tag_dir.mkdir(parents=True, exist_ok=True)

        generated_tags = {}

        # Get all recommendations from database
        from sqlmodel import Session, select

        from src.data.models import Recommendation, Ticker

        with Session(self.recommendations_repo.db_manager.engine) as session:
            # Get all unique tickers
            tickers_stmt = select(Ticker.symbol).distinct()
            tickers = session.exec(tickers_stmt).all()

            for ticker_symbol in tickers:
                tag_path = self._generate_ticker_tag_page(ticker_symbol, session)
                generated_tags[ticker_symbol] = tag_path

            # Get all unique recommendation types
            rec_types_stmt = select(Recommendation.signal_type).distinct()
            rec_types = session.exec(rec_types_stmt).all()

            for rec_type in rec_types:
                if rec_type:  # Skip null values
                    tag_path = self._generate_signal_type_tag_page(rec_type, session)
                    generated_tags[rec_type] = tag_path

            # Get all unique dates
            dates_stmt = select(Recommendation.analysis_date).distinct()
            dates = session.exec(dates_stmt).all()

            for analysis_date in dates:
                if analysis_date:
                    date_str = (
                        analysis_date.strftime("%Y-%m-%d")
                        if hasattr(analysis_date, "strftime")
                        else str(analysis_date)
                    )
                    tag_path = self._generate_date_tag_page(date_str, session)
                    generated_tags[date_str] = tag_path

        logger.info(f"Generated {len(generated_tags)} tag pages")
        return generated_tags

    def _generate_ticker_tag_page(self, ticker: str, session) -> Path:
        """Generate tag page for a specific ticker."""
        from sqlmodel import select

        from src.data.models import Recommendation, Ticker

        # Get all recommendations for this ticker
        stmt = (
            select(Recommendation)
            .join(Ticker)
            .where(Ticker.symbol == ticker)
            .order_by(Recommendation.analysis_date.desc())
        )
        recommendations = session.exec(stmt).all()

        lines = [
            f"# {ticker} - All Analysis",
            "",
            f"Complete analysis history for **{ticker}**.",
            "",
            f"Total recommendations: {len(recommendations)}",
            "",
            "## Recent Analysis",
            "",
            "| Date | Recommendation | Confidence | Price | Mode |",
            "|------|---------------|-----------|-------|------|",
        ]

        for rec in recommendations[:20]:  # Show last 20
            lines.append(
                f"| {rec.analysis_date} | "
                f"**{rec.signal_type.upper()}** | "
                f"{rec.confidence}% | "
                f"${rec.current_price:.2f} | "
                f"{rec.analysis_mode} |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                f"[View detailed {ticker} page](../tickers/{ticker}.md)",
                "",
            ]
        )

        file_path = self.output_dir / "tags" / f"{ticker}.md"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))

        return file_path

    def _generate_signal_type_tag_page(self, signal_type: str, session) -> Path:
        """Generate tag page for a specific signal type (buy, sell, etc)."""
        from sqlmodel import select

        from src.data.models import Recommendation, Ticker

        # Get all recommendations of this type
        stmt = (
            select(Recommendation, Ticker)
            .join(Ticker)
            .where(Recommendation.signal_type == signal_type)
            .order_by(Recommendation.analysis_date.desc())
        )
        results = session.exec(stmt).all()

        # Group by ticker
        ticker_groups = {}
        for rec, ticker in results:
            if ticker.symbol not in ticker_groups:
                ticker_groups[ticker.symbol] = []
            ticker_groups[ticker.symbol].append(rec)

        lines = [
            f"# {signal_type.upper()} Signals",
            "",
            f"All **{signal_type}** recommendations across all tickers.",
            "",
            f"Total signals: {len(results)}",
            f"Unique tickers: {len(ticker_groups)}",
            "",
            "## By Ticker",
            "",
        ]

        for ticker_symbol in sorted(ticker_groups.keys()):
            recs = ticker_groups[ticker_symbol]
            latest = recs[0]
            lines.extend(
                [
                    f"### {ticker_symbol}",
                    "",
                    f"- Latest: {latest.analysis_date} (Confidence: {latest.confidence}%)",
                    f"- Total {signal_type} signals: {len(recs)}",
                    f"- [View {ticker_symbol} details](../tickers/{ticker_symbol}.md)",
                    "",
                ]
            )

        file_path = self.output_dir / "tags" / f"{signal_type}.md"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))

        return file_path

    def _generate_date_tag_page(self, date_str: str, session) -> Path:
        """Generate tag page for a specific analysis date."""
        from sqlmodel import select

        from src.data.models import Recommendation, Ticker

        # Get all recommendations for this date
        stmt = (
            select(Recommendation, Ticker)
            .join(Ticker)
            .where(Recommendation.analysis_date == date_str)
            .order_by(Ticker.symbol)
        )
        results = session.exec(stmt).all()

        # Group by recommendation type
        type_groups = {}
        for rec, ticker in results:
            if rec.signal_type not in type_groups:
                type_groups[rec.signal_type] = []
            type_groups[rec.signal_type].append((ticker.symbol, rec))

        lines = [
            f"# Analysis - {date_str}",
            "",
            f"All analysis signals from **{date_str}**.",
            "",
            f"Total signals: {len(results)}",
            "",
            "## Summary by Signal Type",
            "",
        ]

        for sig_type in sorted(type_groups.keys()):
            items = type_groups[sig_type]
            lines.append(f"### {sig_type.upper()} ({len(items)})")
            lines.append("")

            for ticker_symbol, rec in items:
                lines.append(
                    f"- **{ticker_symbol}**: {rec.confidence}% confidence, "
                    f"${rec.current_price:.2f} "
                    f"([details](../tickers/{ticker_symbol}.md))"
                )

            lines.append("")

        lines.extend(
            [
                "---",
                "",
                f"[View full report for {date_str}](../reports/{date_str}.md)",
                "",
            ]
        )

        file_path = self.output_dir / "tags" / f"{date_str}.md"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))

        return file_path

    def generate_section_indexes(self):
        """Generate index pages for Reports, Tickers, and Tags sections."""
        self._generate_reports_index()
        self._generate_tickers_index()
        self._generate_tags_index()
        logger.info("Generated section index pages")

    def _generate_reports_index(self):
        """Generate index page for Reports section."""
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Get all report files
        report_files = sorted(reports_dir.glob("*.md"), reverse=True)

        lines = [
            "# Analysis Reports",
            "",
            "Daily market analysis reports with investment signals and recommendations.",
            "",
        ]

        if report_files:
            lines.extend(
                [
                    "## Recent Reports",
                    "",
                ]
            )
            for report_file in report_files:
                if report_file.name == "index.md":
                    continue
                date_str = report_file.stem
                lines.append(f"- [{date_str}]({report_file.name})")
            lines.append("")
        else:
            lines.extend(
                [
                    "No reports available yet. Reports are generated when you run analysis with the `--publish` flag or use the `publish` command.",
                    "",
                ]
            )

        index_path = reports_dir / "index.md"
        with open(index_path, "w") as f:
            f.write("\n".join(lines))

    def _generate_tickers_index(self):
        """Generate index page for Tickers section."""
        tickers_dir = self.output_dir / "tickers"
        tickers_dir.mkdir(parents=True, exist_ok=True)

        # Get all ticker files
        ticker_files = sorted(tickers_dir.glob("*.md"))

        lines = [
            "# Ticker Analysis",
            "",
            "Historical analysis and signals for individual stocks.",
            "",
        ]

        if ticker_files:
            lines.extend(
                [
                    "## Available Tickers",
                    "",
                ]
            )
            for ticker_file in ticker_files:
                if ticker_file.name == "index.md":
                    continue
                ticker = ticker_file.stem
                lines.append(f"- [{ticker}]({ticker_file.name})")
            lines.append("")
        else:
            lines.extend(
                [
                    "No ticker pages available yet.",
                    "",
                ]
            )

        index_path = tickers_dir / "index.md"
        with open(index_path, "w") as f:
            f.write("\n".join(lines))

    def _generate_tags_index(self):
        """Generate index page for Tags section."""
        tags_dir = self.output_dir / "tags"
        tags_dir.mkdir(parents=True, exist_ok=True)

        # Get all tag files
        tag_files = sorted(tags_dir.glob("*.md"))

        lines = [
            "# Tags",
            "",
            "Browse analysis by ticker, signal type, or date.",
            "",
        ]

        if tag_files:
            # Separate by type
            ticker_tags = []
            signal_tags = []
            date_tags = []

            for tag_file in tag_files:
                if tag_file.name == "index.md" or tag_file.name == ".pages":
                    continue
                tag_name = tag_file.stem

                # Categorize
                if tag_name[0].isdigit():  # Date tags start with year
                    date_tags.append(tag_name)
                elif tag_name.isupper():  # Ticker symbols are uppercase
                    ticker_tags.append(tag_name)
                else:  # Signal types
                    signal_tags.append(tag_name)

            if ticker_tags:
                lines.extend(
                    [
                        "## By Ticker",
                        "",
                    ]
                )
                for tag in sorted(ticker_tags):
                    lines.append(f"- [{tag}]({tag}.md)")
                lines.append("")

            if signal_tags:
                lines.extend(
                    [
                        "## By Signal Type",
                        "",
                    ]
                )
                for tag in sorted(signal_tags):
                    display_name = tag.replace("_", " ").title()
                    lines.append(f"- [{display_name}]({tag}.md)")
                lines.append("")

            if date_tags:
                lines.extend(
                    [
                        "## By Date",
                        "",
                    ]
                )
                for tag in sorted(date_tags, reverse=True):
                    lines.append(f"- [{tag}]({tag}.md)")
                lines.append("")
        else:
            lines.extend(
                [
                    "No tags available yet.",
                    "",
                ]
            )

        index_path = tags_dir / "index.md"
        with open(index_path, "w") as f:
            f.write("\n".join(lines))

    def update_navigation(self):
        """Update .pages files for navigation."""
        # Generate section index pages first
        self.generate_section_indexes()

        # Create reports/.pages
        reports_pages = self.output_dir / "reports" / ".pages"
        reports_pages.parent.mkdir(parents=True, exist_ok=True)
        with open(reports_pages, "w") as f:
            f.write("title: Reports\n")
            f.write("nav:\n")
            f.write("  - index.md\n")
            f.write("  - ...\n")  # Auto-discover all markdown files

        # Create tickers/.pages
        tickers_pages = self.output_dir / "tickers" / ".pages"
        tickers_pages.parent.mkdir(parents=True, exist_ok=True)
        with open(tickers_pages, "w") as f:
            f.write("title: Tickers\n")
            f.write("nav:\n")
            f.write("  - index.md\n")
            f.write("  - ...\n")

        # Create tags/.pages
        tags_pages = self.output_dir / "tags" / ".pages"
        tags_pages.parent.mkdir(parents=True, exist_ok=True)
        with open(tags_pages, "w") as f:
            f.write("title: Tags\n")
            f.write("nav:\n")
            f.write("  - index.md\n")
            f.write("  - ...\n")

        logger.info("Updated navigation files")
