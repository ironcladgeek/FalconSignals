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
                f"**Analysis Mode:** {metadata.get('analysis_mode', 'unknown').replace('_', '-').title()}  ",
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
                    "## 📊 Buy Signals",
                    "",
                ]
            )
            for signal in buy:
                lines.extend(self._format_signal(signal))

        # Hold Signals (optional, only if not too many)
        if hold_bullish and len(hold_bullish) <= 5:
            lines.extend(
                [
                    "## ⏸️ Hold (Bullish) Signals",
                    "",
                ]
            )
            for signal in hold_bullish:
                lines.extend(self._format_signal(signal, include_details=False))

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
                "",
            ]
        )

        # Write to file
        report_dir = self.output_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        file_path = report_dir / f"{report_date}.md"
        with open(file_path, "w") as f:
            f.write("\n".join(lines))

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
        lines = [
            f"### {signal.ticker}",
            "",
            f"**Recommendation:** {signal.recommendation.value.upper().replace('_', ' ')}  ",
            f"**Confidence:** {signal.confidence}%  ",
            f"**Current Price:** ${signal.current_price:.2f}",
            "",
        ]

        if include_details:
            # Add analysis summary
            if signal.reasoning:
                lines.extend(
                    [
                        "**Analysis:**",
                        "",
                        signal.reasoning,
                        "",
                    ]
                )

            # Add component scores
            if signal.component_scores:
                lines.extend(
                    [
                        "**Component Scores:**",
                        "",
                        f"- Technical: {signal.component_scores.technical:.0f}/100",
                        f"- Fundamental: {signal.component_scores.fundamental:.0f}/100",
                        f"- Sentiment: {signal.component_scores.sentiment:.0f}/100",
                        "",
                    ]
                )

            # Add risk assessment
            if signal.risk_assessment:
                lines.extend(
                    [
                        f"**Risk Assessment:** {signal.risk_assessment.level.value.replace('_', ' ').title()}",
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
            # Get recent sessions from database
            recent_sessions = self.sessions_repo.get_recent_sessions(limit=10)
            recent_reports = [
                {
                    "date": session.get("analysis_date", session.get("started_at", "")[:10]),
                    "signals_count": session.get("total_signals", 0),
                    "session_id": session.get("id"),
                }
                for session in recent_sessions
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

        with Session(self.recommendations_repo.engine) as session:
            # Get all unique tickers
            tickers_stmt = select(Ticker.symbol).distinct()
            tickers = session.exec(tickers_stmt).all()

            for ticker_symbol in tickers:
                tag_path = self._generate_ticker_tag_page(ticker_symbol, session)
                generated_tags[ticker_symbol] = tag_path

            # Get all unique recommendation types
            rec_types_stmt = select(Recommendation.recommendation).distinct()
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
                f"**{rec.recommendation.upper()}** | "
                f"{rec.confidence}% | "
                f"${rec.price_at_analysis:.2f} | "
                f"{rec.mode} |"
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
            .where(Recommendation.recommendation == signal_type)
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
            if rec.recommendation not in type_groups:
                type_groups[rec.recommendation] = []
            type_groups[rec.recommendation].append((ticker.symbol, rec))

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
                    f"${rec.price_at_analysis:.2f} "
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

    def update_navigation(self):
        """Update .pages files for navigation."""
        # Create reports/.pages
        reports_pages = self.output_dir / "reports" / ".pages"
        reports_pages.parent.mkdir(parents=True, exist_ok=True)
        with open(reports_pages, "w") as f:
            f.write("title: Reports\n")
            f.write("nav:\n")
            f.write("  - ...\n")  # Auto-discover all markdown files

        # Create tickers/.pages
        tickers_pages = self.output_dir / "tickers" / ".pages"
        tickers_pages.parent.mkdir(parents=True, exist_ok=True)
        with open(tickers_pages, "w") as f:
            f.write("title: Tickers\n")
            f.write("nav:\n")
            f.write("  - ...\n")

        # Create tags/.pages
        tags_pages = self.output_dir / "tags" / ".pages"
        tags_pages.parent.mkdir(parents=True, exist_ok=True)
        with open(tags_pages, "w") as f:
            f.write("title: Tags\n")
            f.write("nav:\n")
            f.write("  - ...\n")

        logger.info("Updated navigation files")
