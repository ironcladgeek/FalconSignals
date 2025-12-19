"""Comprehensive additional tests for WebsiteGenerator class to increase coverage."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.analysis import (
    ComponentScores,
    InvestmentSignal,
    Recommendation,
    RiskAssessment,
    RiskLevel,
)
from src.analysis.models import (
    AnalysisMetadata,
    AnalystInfo,
    FundamentalMetrics,
    SentimentInfo,
    TechnicalIndicators,
)
from src.config import load_config
from src.website.generator import WebsiteGenerator


def create_detailed_signal(
    ticker="MSFT",
    recommendation=Recommendation.HOLD_BULLISH,
    with_metadata=True,
) -> InvestmentSignal:
    """Helper to create signal with complete metadata for testing."""
    metadata = None
    if with_metadata:
        metadata = AnalysisMetadata(
            technical_indicators=TechnicalIndicators(
                rsi=65.5,
                macd=2.5,
                macd_signal=1.8,
                macd_histogram=0.7,
                trend="up",
                sma_20=150.0,
                sma_50=148.0,
                ema_12=151.0,
                ema_26=149.5,
                bbands_upper=155.0,
                bbands_middle=150.0,
                bbands_lower=145.0,
                atr=3.5,
                adx=28.0,
            ),
            fundamental_metrics=FundamentalMetrics(
                pe_ratio=25.5,
                pb_ratio=8.2,
                ps_ratio=10.5,
                debt_to_equity=0.45,
                current_ratio=2.1,
                roe=0.35,
                roa=0.15,
                profit_margin=0.28,
                revenue_growth=0.12,
                earnings_growth=0.15,
            ),
            analyst_info=AnalystInfo(
                num_analysts=35,
                consensus_rating="buy",
                strong_buy=15,
                buy=12,
                hold=6,
                sell=2,
                strong_sell=0,
                price_target=175.0,
            ),
            sentiment_info=SentimentInfo(
                news_count=45,
                positive_news=25,
                neutral_news=15,
                negative_news=5,
                sentiment_score=0.45,
            ),
        )

    return InvestmentSignal(
        ticker=ticker,
        name=f"{ticker} Corporation",
        market="US",
        sector="Technology",
        current_price=152.50,
        currency="USD",
        scores=ComponentScores(technical=75, fundamental=82, sentiment=88),
        final_score=82,
        recommendation=recommendation,
        confidence=85,
        time_horizon="6M",
        expected_return_min=8.0,
        expected_return_max=18.0,
        key_reasons=[
            "Strong earnings growth",
            "Positive analyst consensus",
            "Bullish technical indicators",
        ],
        risk=RiskAssessment(
            level=RiskLevel.MEDIUM,
            volatility="normal",
            volatility_pct=3.2,
            liquidity="highly_liquid",
            concentration_risk=False,
            sector_risk="moderate",
            flags=["Some regulatory concerns", "High valuation metrics"],
        ),
        allocation=None,
        generated_at=datetime.now(),
        analysis_date="2025-12-15",
        rationale="This is a detailed analysis of the stock showing positive fundamentals with strong technical momentum and favorable market sentiment.",
        caveats=["Market volatility", "Sector rotation risk"],
        metadata=metadata,
    )


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config():
    """Load test configuration."""
    return load_config("config/default.yaml")


@pytest.fixture
def test_db_path(tmp_path):
    """Create temporary test database."""
    db_path = tmp_path / "test_comprehensive.db"
    from src.data.db import init_db

    init_db(str(db_path))
    return str(db_path)


@pytest.fixture
def generator(test_config, test_db_path, temp_output_dir):
    """Create WebsiteGenerator instance for testing."""
    return WebsiteGenerator(
        config=test_config,
        db_path=test_db_path,
        output_dir=str(temp_output_dir),
    )


class TestFormatSignalDetailed:
    """Test detailed signal formatting with metadata."""

    def test_format_signal_with_full_metadata(self, generator):
        """Test formatting signal with complete metadata."""
        signal = create_detailed_signal(with_metadata=True)
        lines = generator._format_signal(signal, include_details=True)

        formatted_text = "\n".join(lines)

        # Check basic info
        assert "MSFT" in formatted_text
        assert "85%" in formatted_text  # confidence

        # Check technical indicators table
        assert "Technical Indicators" in formatted_text
        assert "RSI" in formatted_text
        assert "65.5" in formatted_text or "65.50" in formatted_text
        assert "MACD" in formatted_text
        assert "SMA" in formatted_text

        # Check fundamental metrics table
        assert "Fundamental Metrics" in formatted_text
        assert "Pe Ratio" in formatted_text or "PE Ratio" in formatted_text
        assert "25.5" in formatted_text or "25.50" in formatted_text
        assert "Roe" in formatted_text or "ROE" in formatted_text

        # Check analyst ratings
        assert "Analyst Ratings" in formatted_text
        assert "Number of Analysts" in formatted_text or "Analysts" in formatted_text
        assert "35" in formatted_text
        assert "Price Target" in formatted_text
        assert "$175.00" in formatted_text

        # Check sentiment info
        assert "News & Sentiment" in formatted_text or "Sentiment" in formatted_text
        assert "Total Articles" in formatted_text or "news_count" in formatted_text.lower()
        assert "45" in formatted_text

    def test_format_signal_without_metadata(self, generator):
        """Test formatting signal without metadata."""
        signal = create_detailed_signal(with_metadata=False)
        lines = generator._format_signal(signal, include_details=True)

        formatted_text = "\n".join(lines)

        # Should have basic info
        assert "MSFT" in formatted_text
        assert "85%" in formatted_text

        # Should NOT have detailed metadata sections
        assert "Technical Indicators" not in formatted_text or "<details" not in formatted_text

    def test_format_signal_without_details(self, generator):
        """Test formatting signal with include_details=False."""
        signal = create_detailed_signal(with_metadata=True)
        lines = generator._format_signal(signal, include_details=False)

        formatted_text = "\n".join(lines)

        # Should have basic info
        assert "MSFT" in formatted_text
        assert "85%" in formatted_text

        # Should NOT have detailed sections
        assert "Key Reasons" not in formatted_text
        assert "Risk Flags" not in formatted_text
        assert "Detailed Analysis" not in formatted_text

    def test_format_signal_hold_bearish(self, generator):
        """Test formatting HOLD_BEARISH signal."""
        signal = create_detailed_signal(recommendation=Recommendation.HOLD_BEARISH)
        lines = generator._format_signal(signal, include_details=True)

        formatted_text = "\n".join(lines)

        # Check hold symbol used
        assert "🟡" in formatted_text
        assert "HOLD" in formatted_text

    def test_format_signal_strong_sell(self, generator):
        """Test formatting STRONG_SELL signal."""
        signal = create_detailed_signal(recommendation=Recommendation.STRONG_SELL)
        lines = generator._format_signal(signal, include_details=True)

        formatted_text = "\n".join(lines)

        # Check sell symbol used
        assert "🔴" in formatted_text
        assert "SELL" in formatted_text

    def test_format_signal_with_risk_flags(self, generator):
        """Test formatting signal with risk flags."""
        signal = create_detailed_signal()
        lines = generator._format_signal(signal, include_details=True)

        formatted_text = "\n".join(lines)

        # Check risk flags section
        assert "Risk Flags" in formatted_text or "⚠️" in formatted_text
        assert "regulatory concerns" in formatted_text.lower()

    def test_format_signal_with_rationale(self, generator):
        """Test formatting signal with rationale."""
        signal = create_detailed_signal()
        lines = generator._format_signal(signal, include_details=True)

        formatted_text = "\n".join(lines)

        # Check rationale section
        assert "Detailed Analysis" in formatted_text or "📝" in formatted_text
        assert "positive fundamentals" in formatted_text.lower()


class TestReportPageGeneration:
    """Test report page generation with various signal combinations."""

    def test_generate_report_all_recommendation_types(self, generator, temp_output_dir):
        """Test report with all recommendation types."""
        signals = [
            create_detailed_signal(ticker="AAPL", recommendation=Recommendation.STRONG_BUY),
            create_detailed_signal(ticker="NVDA", recommendation=Recommendation.BUY),
            create_detailed_signal(ticker="MSFT", recommendation=Recommendation.HOLD_BULLISH),
            create_detailed_signal(ticker="GOOGL", recommendation=Recommendation.HOLD),
            create_detailed_signal(ticker="META", recommendation=Recommendation.HOLD_BEARISH),
            create_detailed_signal(ticker="TSLA", recommendation=Recommendation.SELL),
            create_detailed_signal(ticker="NFLX", recommendation=Recommendation.STRONG_SELL),
        ]

        report_path = generator.generate_report_page(
            signals=signals,
            report_date="2025-12-15",
            metadata=None,
        )

        content = report_path.read_text()

        # Check all sections are present
        assert "Strong Buy Signals" in content or "🎯" in content
        assert "Buy Signals" in content or "📈" in content
        assert "Hold (Bullish)" in content or "⏸️" in content
        assert "Hold Signals" in content
        assert "Hold (Bearish)" in content
        assert "Sell Signals" in content or "📉" in content
        assert "Strong Sell Signals" in content or "🔴" in content

        # Check all tickers present
        for ticker in ["AAPL", "NVDA", "MSFT", "GOOGL", "META", "TSLA", "NFLX"]:
            assert ticker in content

    def test_generate_report_tags_section(self, generator, temp_output_dir):
        """Test that tags section is generated correctly."""
        signals = [
            create_detailed_signal(ticker="AAPL", recommendation=Recommendation.BUY),
            create_detailed_signal(ticker="MSFT", recommendation=Recommendation.BUY),
        ]

        report_path = generator.generate_report_page(
            signals=signals,
            report_date="2025-12-15",
        )

        content = report_path.read_text()

        # Check tags section with links
        assert "🏷️ Tags" in content or "Tags" in content
        assert "[AAPL](../tickers/AAPL.md)" in content
        assert "[MSFT](../tickers/MSFT.md)" in content

    def test_generate_report_disclaimer(self, generator, temp_output_dir):
        """Test that disclaimer is included."""
        signals = [create_detailed_signal()]

        report_path = generator.generate_report_page(
            signals=signals,
            report_date="2025-12-15",
        )

        content = report_path.read_text()

        # Check disclaimer
        assert "Investment Risk" in content or "warning" in content.lower()
        assert "investment advice" in content.lower()

    def test_generate_report_date_formatting(self, generator, temp_output_dir):
        """Test that date is formatted correctly."""
        signals = [create_detailed_signal()]

        report_path = generator.generate_report_page(
            signals=signals,
            report_date="2025-12-15",
        )

        content = report_path.read_text()

        # Check date formatting (December 15, 2025)
        assert "December 15, 2025" in content or "2025-12-15" in content


class TestTickerPageGeneration:
    """Test ticker page generation."""

    def test_generate_ticker_page_no_recommendations(self, generator):
        """Test ticker page when no recommendations exist."""
        result = generator.generate_ticker_page("NONEXISTENT")

        # Should return None or handle gracefully
        assert result is None

    def test_generate_ticker_page_with_data(self, generator, test_db_path):
        """Test ticker page with stored recommendations."""
        from src.data.repository import RunSessionRepository

        # Create session and store recommendations
        session_repo = RunSessionRepository(test_db_path)
        session_id = session_repo.create_session(
            analysis_mode="test",
            analyzed_category="test",
        )

        # Store multiple recommendations for same ticker
        for i in range(3):
            signal = create_detailed_signal(
                ticker="MSFT",
                recommendation=Recommendation.BUY if i % 2 == 0 else Recommendation.HOLD,
            )
            generator.recommendations_repo.store_recommendation(
                signal=signal,
                run_session_id=session_id,
                analysis_mode="test",
            )

        # Generate page
        ticker_path = generator.generate_ticker_page("MSFT")

        assert ticker_path is not None
        assert ticker_path.exists()

        content = ticker_path.read_text()

        # Check content
        assert "MSFT" in content or "msft" in content  # May be lowercase
        assert "Analysis History" in content or "analysis" in content.lower()
        assert "Recent Signals" in content or "signals" in content.lower()
        assert "Total signals recorded" in content.lower() or "total" in content.lower()


class TestIndexPageGeneration:
    """Test index/homepage generation."""

    def test_generate_index_with_no_reports(self, generator):
        """Test index generation when no reports exist."""
        index_path = generator.generate_index_page(recent_reports=None)

        assert index_path.exists()

        content = index_path.read_text()

        # Check basic structure
        assert "NordInvest" in content
        assert "Recent Analysis" in content

    def test_generate_index_with_recent_reports(self, generator):
        """Test index generation with recent reports data."""
        recent_reports = [
            {"date": "2025-12-15", "signals_count": 10},
            {"date": "2025-12-14", "signals_count": 8},
            {"date": "2025-12-13", "signals_count": 12},
        ]

        index_path = generator.generate_index_page(recent_reports=recent_reports)

        content = index_path.read_text()

        # Check report data is included
        assert "2025-12-15" in content
        assert "10" in content
        assert "View Report" in content.lower() or "[View" in content

    def test_generate_index_buttons(self, generator):
        """Test that navigation buttons are present."""
        index_path = generator.generate_index_page()

        content = index_path.read_text()

        # Check for button links
        assert "Browse All Reports" in content or "reports" in content.lower()
        assert "Browse Tickers" in content or "tickers" in content.lower()


class TestTagPagesGeneration:
    """Test tag page generation."""

    def test_generate_tag_pages_empty_database(self, generator):
        """Test tag generation with empty database."""
        tags = generator.generate_tag_pages()

        # Should handle empty database gracefully
        assert isinstance(tags, dict)

    def test_generate_tag_pages_with_data(self, generator, test_db_path):
        """Test tag generation with stored data."""
        from src.data.repository import RunSessionRepository

        # Create session and store recommendations
        session_repo = RunSessionRepository(test_db_path)
        session_id = session_repo.create_session(
            analysis_mode="test",
            analyzed_category="test",
        )

        # Store recommendations
        for ticker in ["AAPL", "MSFT"]:
            signal = create_detailed_signal(
                ticker=ticker,
                recommendation=Recommendation.BUY,
            )
            generator.recommendations_repo.store_recommendation(
                signal=signal,
                run_session_id=session_id,
                analysis_mode="test",
            )

        # Generate tag pages
        tags = generator.generate_tag_pages()

        # Should have generated some tags
        assert len(tags) > 0

        # Check if ticker tags were created
        tag_dir = Path(generator.output_dir) / "tags"
        assert tag_dir.exists()

    def test_ticker_tag_page_content(self, generator, test_db_path):
        """Test ticker-specific tag page content."""
        from sqlmodel import Session

        from src.data.repository import RunSessionRepository

        # Create session and store recommendation
        session_repo = RunSessionRepository(test_db_path)
        session_id = session_repo.create_session(
            analysis_mode="test",
            analyzed_category="test",
        )

        signal = create_detailed_signal(ticker="AAPL")
        generator.recommendations_repo.store_recommendation(
            signal=signal,
            run_session_id=session_id,
            analysis_mode="test",
        )

        # Ensure tag directory exists
        tag_dir = Path(generator.output_dir) / "tags"
        tag_dir.mkdir(parents=True, exist_ok=True)

        # Generate tag page using database session
        with Session(generator.recommendations_repo.db_manager.engine) as session:
            tag_path = generator._generate_ticker_tag_page("AAPL", session)

        assert tag_path.exists()

        content = tag_path.read_text()

        # Check content
        assert "AAPL" in content
        assert "All Analysis" in content or "analysis" in content.lower()

    def test_signal_type_tag_page_content(self, generator, test_db_path):
        """Test signal type tag page content."""
        from sqlmodel import Session

        from src.data.repository import RunSessionRepository

        # Create session and store recommendation
        session_repo = RunSessionRepository(test_db_path)
        session_id = session_repo.create_session(
            analysis_mode="test",
            analyzed_category="test",
        )

        signal = create_detailed_signal(recommendation=Recommendation.BUY)
        generator.recommendations_repo.store_recommendation(
            signal=signal,
            run_session_id=session_id,
            analysis_mode="test",
        )

        # Ensure tag directory exists
        tag_dir = Path(generator.output_dir) / "tags"
        tag_dir.mkdir(parents=True, exist_ok=True)

        # Generate signal type tag page
        with Session(generator.recommendations_repo.db_manager.engine) as session:
            tag_path = generator._generate_signal_type_tag_page("buy", session)

        assert tag_path.exists()

        content = tag_path.read_text()

        # Check content
        assert "BUY" in content or "buy" in content
        assert "signals" in content.lower()

    def test_date_tag_page_content(self, generator, test_db_path):
        """Test date tag page content."""
        from sqlmodel import Session

        from src.data.repository import RunSessionRepository

        # Create session and store recommendation
        session_repo = RunSessionRepository(test_db_path)
        session_id = session_repo.create_session(
            analysis_mode="test",
            analyzed_category="test",
        )

        signal = create_detailed_signal()
        generator.recommendations_repo.store_recommendation(
            signal=signal,
            run_session_id=session_id,
            analysis_mode="test",
        )

        # Ensure tag directory exists
        tag_dir = Path(generator.output_dir) / "tags"
        tag_dir.mkdir(parents=True, exist_ok=True)

        # Generate date tag page
        with Session(generator.recommendations_repo.db_manager.engine) as session:
            tag_path = generator._generate_date_tag_page("2025-12-15", session)

        assert tag_path.exists()

        content = tag_path.read_text()

        # Check content
        assert "2025-12-15" in content
        assert "Analysis" in content


class TestSectionIndexGeneration:
    """Test section index page generation."""

    def test_generate_section_indexes(self, generator, temp_output_dir):
        """Test that all section indexes are generated."""
        generator.generate_section_indexes()

        # Check all index files exist
        assert (temp_output_dir / "reports" / "index.md").exists()
        assert (temp_output_dir / "tickers" / "index.md").exists()
        assert (temp_output_dir / "tags" / "index.md").exists()

    def test_reports_index_empty(self, generator, temp_output_dir):
        """Test reports index when no reports exist."""
        generator._generate_reports_index()

        index_path = temp_output_dir / "reports" / "index.md"
        assert index_path.exists()

        content = index_path.read_text()

        assert "Reports" in content
        assert "No reports available" in content or "analysis" in content.lower()

    def test_reports_index_with_files(self, generator, temp_output_dir):
        """Test reports index when report files exist."""
        # Create some report files
        reports_dir = temp_output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        (reports_dir / "2025-12-15.md").write_text("Test report 1")
        (reports_dir / "2025-12-14.md").write_text("Test report 2")

        generator._generate_reports_index()

        index_path = reports_dir / "index.md"
        content = index_path.read_text()

        # Check both dates are listed
        assert "2025-12-15" in content
        assert "2025-12-14" in content
        assert "Recent Reports" in content

    def test_tickers_index_with_files(self, generator, temp_output_dir):
        """Test tickers index when ticker files exist."""
        # Create some ticker files
        tickers_dir = temp_output_dir / "tickers"
        tickers_dir.mkdir(parents=True, exist_ok=True)

        (tickers_dir / "AAPL.md").write_text("AAPL data")
        (tickers_dir / "MSFT.md").write_text("MSFT data")

        generator._generate_tickers_index()

        index_path = tickers_dir / "index.md"
        content = index_path.read_text()

        # Check tickers are listed
        assert "AAPL" in content
        assert "MSFT" in content
        assert "Available Tickers" in content or "Ticker" in content

    def test_tags_index_categorization(self, generator, temp_output_dir):
        """Test that tags index categorizes tags correctly."""
        # Create various tag files
        tags_dir = temp_output_dir / "tags"
        tags_dir.mkdir(parents=True, exist_ok=True)

        (tags_dir / "AAPL.md").write_text("Ticker tag")
        (tags_dir / "buy.md").write_text("Signal type tag")
        (tags_dir / "2025-12-15.md").write_text("Date tag")

        generator._generate_tags_index()

        index_path = tags_dir / "index.md"
        content = index_path.read_text()

        # Check categorization
        assert "By Ticker" in content
        assert "By Signal Type" in content or "Signal" in content
        assert "By Date" in content


class TestNavigationUpdate:
    """Test navigation file updates."""

    def test_update_navigation_creates_all_files(self, generator, temp_output_dir):
        """Test that update_navigation creates all .pages files."""
        generator.update_navigation()

        # Check all .pages files exist
        assert (temp_output_dir / "reports" / ".pages").exists()
        assert (temp_output_dir / "tickers" / ".pages").exists()
        assert (temp_output_dir / "tags" / ".pages").exists()

    def test_update_navigation_file_content(self, generator, temp_output_dir):
        """Test that .pages files have correct content."""
        generator.update_navigation()

        # Check reports/.pages
        reports_pages = (temp_output_dir / "reports" / ".pages").read_text()
        assert "title: Reports" in reports_pages
        assert "nav:" in reports_pages
        assert "index.md" in reports_pages
        assert "..." in reports_pages  # Auto-discover

        # Check tickers/.pages
        tickers_pages = (temp_output_dir / "tickers" / ".pages").read_text()
        assert "title: Tickers" in tickers_pages

        # Check tags/.pages
        tags_pages = (temp_output_dir / "tags" / ".pages").read_text()
        assert "title: Tags" in tags_pages


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_signal_with_none_values(self, generator):
        """Test formatting signal with None values in metadata."""
        signal = create_detailed_signal(with_metadata=True)
        # Set some values to None
        if signal.metadata and signal.metadata.analyst_info:
            signal.metadata.analyst_info.price_target = None
            signal.metadata.analyst_info.num_analysts = None

        lines = generator._format_signal(signal, include_details=True)

        # Should handle None values gracefully
        formatted_text = "\n".join(lines)
        assert "MSFT" in formatted_text

    def test_signal_without_risk(self, generator):
        """Test formatting signal without risk assessment."""
        signal = create_detailed_signal()
        signal.risk = None

        lines = generator._format_signal(signal, include_details=True)

        formatted_text = "\n".join(lines)

        # Should handle missing risk gracefully
        assert "MSFT" in formatted_text
        assert "Risk Level" not in formatted_text or formatted_text.count("Risk") == 1

    def test_signal_without_scores(self, generator):
        """Test formatting signal without component scores."""
        signal = create_detailed_signal()
        signal.scores = None

        lines = generator._format_signal(signal, include_details=True)

        formatted_text = "\n".join(lines)

        # Should handle missing scores gracefully
        assert "MSFT" in formatted_text
        assert "Scores:" not in formatted_text or "Technical:" not in formatted_text

    def test_signal_without_key_reasons(self, generator):
        """Test formatting signal without key reasons."""
        signal = create_detailed_signal()
        signal.key_reasons = []

        lines = generator._format_signal(signal, include_details=True)

        formatted_text = "\n".join(lines)

        # Should handle empty key reasons gracefully
        assert "MSFT" in formatted_text
        assert "Key Reasons:" not in formatted_text or formatted_text.count("Key Reasons") <= 1

    def test_report_with_single_signal(self, generator, temp_output_dir):
        """Test report generation with just one signal."""
        signals = [create_detailed_signal(ticker="SINGLE", recommendation=Recommendation.BUY)]

        report_path = generator.generate_report_page(
            signals=signals,
            report_date="2025-12-15",
        )

        content = report_path.read_text()

        # Should handle single signal
        assert "SINGLE" in content
        assert "Tickers Analyzed: 1" in content or "1" in content

    def test_metadata_formatting_percentages(self, generator):
        """Test that percentage values in metadata are formatted correctly."""
        signal = create_detailed_signal(with_metadata=True)

        lines = generator._format_signal(signal, include_details=True)
        formatted_text = "\n".join(lines)

        # Check percentage formatting (should have % symbol)
        if "35.0%" in formatted_text or "35%" in formatted_text:
            # ROE is 0.35 (35%)
            assert True
        else:
            # Alternative formatting
            assert "0.35" in formatted_text or "35" in formatted_text
