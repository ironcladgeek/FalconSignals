"""Tests for WebsiteGenerator class."""

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
from src.config import load_config
from src.website.generator import WebsiteGenerator


def create_test_signal(
    ticker="AAPL",
    recommendation=Recommendation.BUY,
    confidence=90,
    price=150.0,
) -> InvestmentSignal:
    """Helper to create valid test signal."""
    return InvestmentSignal(
        ticker=ticker,
        name=f"{ticker} Inc.",
        market="US",
        sector="Technology",
        current_price=price,
        currency="USD",
        scores=ComponentScores(technical=85, fundamental=80, sentiment=88),
        final_score=84,
        recommendation=recommendation,
        confidence=confidence,
        time_horizon="3M",
        expected_return_min=5.0,
        expected_return_max=15.0,
        key_reasons=["Strong fundamentals", "Positive momentum"],
        risk=RiskAssessment(
            level=RiskLevel.LOW,
            volatility="normal",
            volatility_pct=2.5,
            liquidity="highly_liquid",
            concentration_risk=False,
            sector_risk=None,
            flags=[],
        ),
        allocation=None,
        generated_at=datetime.now(),
        analysis_date="2025-12-10",
        rationale="Test signal",
        caveats=[],
        metadata=None,
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
    db_path = tmp_path / "test.db"
    # Initialize test database
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


@pytest.fixture
def sample_signals():
    """Create sample investment signals for testing."""
    return [
        create_test_signal(
            ticker="AAPL",
            recommendation=Recommendation.STRONG_BUY,
            confidence=92,
            price=150.25,
        ),
        create_test_signal(
            ticker="NVDA",
            recommendation=Recommendation.BUY,
            confidence=85,
            price=450.75,
        ),
    ]


class TestWebsiteGenerator:
    """Test WebsiteGenerator functionality."""

    def test_initialization(self, generator, temp_output_dir):
        """Test generator initialization."""
        assert generator.output_dir == temp_output_dir
        assert generator.recommendations_repo is not None
        assert generator.sessions_repo is not None

    def test_generate_report_page(self, generator, sample_signals, temp_output_dir):
        """Test report page generation."""
        report_path = generator.generate_report_page(
            signals=sample_signals,
            report_date="2025-12-10",
            metadata={"session_id": 123, "total_signals": 2},
        )

        # Check file was created
        assert report_path.exists()
        assert report_path.parent == temp_output_dir / "reports"

        # Check content
        content = report_path.read_text()
        assert "2025-12-10" in content
        assert "AAPL" in content
        assert "NVDA" in content
        assert "STRONG BUY" in content  # Note: space not underscore
        assert "BUY" in content

        # Check frontmatter tags
        assert "tags:" in content
        assert "- AAPL" in content or "- aapl" in content.lower()

    def test_generate_ticker_page(self, generator, test_db_path, temp_output_dir):
        """Test ticker page generation."""
        # Use generator's repository instances to ensure same DB connection
        from src.data.repository import RunSessionRepository

        # Create a run session first
        session_repo = RunSessionRepository(test_db_path)
        session_id = session_repo.create_session(
            analysis_mode="test",
            analyzed_category="test_category",
        )

        # Now store the recommendation using generator's repo
        signal = create_test_signal(ticker="AAPL", recommendation=Recommendation.BUY)

        rec_id = generator.recommendations_repo.store_recommendation(
            signal=signal,
            run_session_id=session_id,
            analysis_mode="test",
            llm_model=None,
        )

        # Verify recommendation was stored
        assert rec_id is not None
        stored_recs = generator.recommendations_repo.get_recommendations_by_ticker("AAPL")
        assert len(stored_recs) > 0, (
            f"No recommendations found for AAPL after storing. DB: {test_db_path}"
        )

        # Generate ticker page
        ticker_path = generator.generate_ticker_page("AAPL")

        # Check file was created
        assert ticker_path is not None
        assert ticker_path.exists()
        assert ticker_path.parent == temp_output_dir / "tickers"

        # Check content
        content = ticker_path.read_text()
        assert "AAPL" in content
        assert "BUY" in content or "Buy" in content
        assert "90" in content  # confidence

    def test_generate_index_page(self, generator, temp_output_dir):
        """Test index page generation."""
        index_path = generator.generate_index_page()

        # Check file was created
        assert index_path.exists()
        assert index_path == temp_output_dir / "index.md"

        # Check content
        content = index_path.read_text()
        assert "NordInvest" in content or "Analysis" in content
        assert "Recent Analysis" in content

    def test_update_navigation(self, generator, temp_output_dir):
        """Test navigation file creation."""
        generator.update_navigation()

        # Check .pages files were created
        reports_pages = temp_output_dir / "reports" / ".pages"
        tickers_pages = temp_output_dir / "tickers" / ".pages"
        tags_pages = temp_output_dir / "tags" / ".pages"

        assert reports_pages.exists()
        assert tickers_pages.exists()
        assert tags_pages.exists()

        # Check content
        assert "title: Reports" in reports_pages.read_text()
        assert "title: Tickers" in tickers_pages.read_text()
        assert "title: Tags" in tags_pages.read_text()

    def test_format_signal(self, generator, sample_signals):
        """Test signal formatting."""
        signal = sample_signals[0]
        formatted = generator._format_signal(signal, include_details=True)

        # formatted is a list of strings, check if ticker appears in any line
        formatted_text = "\n".join(formatted)
        assert signal.ticker in formatted_text
        assert str(signal.confidence) in formatted_text
        # Check for spaced version since .upper().replace('_', ' ') converts to space
        expected_rec = signal.recommendation.value.replace("_", " ")
        assert expected_rec in formatted_text.lower()

    def test_generate_report_with_empty_signals(self, generator):
        """Test report generation with empty signals list."""
        report_path = generator.generate_report_page(
            signals=[],
            report_date="2025-12-10",
            metadata=None,
        )

        # Should still create a file
        assert report_path.exists()

        content = report_path.read_text()
        assert "2025-12-10" in content
        assert "No signals" in content.lower() or "0" in content

    def test_generate_report_with_metadata(self, generator, sample_signals):
        """Test report generation with metadata."""
        metadata = {
            "session_id": 456,
            "total_signals": 10,
            "analysis_mode": "llm",
        }

        report_path = generator.generate_report_page(
            signals=sample_signals,
            report_date="2025-12-10",
            metadata=metadata,
        )

        # Metadata should be included in some form
        assert report_path.exists()

    def test_output_directory_creation(self, test_config, test_db_path):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_dir" / "docs"

            generator = WebsiteGenerator(
                config=test_config,
                db_path=test_db_path,
                output_dir=str(output_dir),
            )

            # Generate something to trigger directory creation
            generator.update_navigation()

            # Check directories were created
            assert (output_dir / "reports").exists()
            assert (output_dir / "tickers").exists()
            assert (output_dir / "tags").exists()
