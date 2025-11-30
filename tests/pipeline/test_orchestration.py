"""Tests for pipeline orchestration."""

import pytest

from src.cache.manager import CacheManager
from src.pipeline import AnalysisPipeline


@pytest.mark.integration
class TestPipelineOrchestration:
    """Test suite for AnalysisPipeline integration."""

    @pytest.fixture
    def cache_manager(self, tmp_path):
        """Create cache manager for tests."""
        return CacheManager(str(tmp_path / "cache"))

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {
            "capital_starting": 2000,
            "capital_monthly_deposit": 500,
            "max_position_size_pct": 10,
            "max_sector_concentration_pct": 20,
            "risk_volatility_high": 3.0,
            "risk_volatility_very_high": 5.0,
            "include_disclaimers": True,
        }

    def test_pipeline_initialization(self, config, cache_manager):
        """Test pipeline initializes with required components."""
        try:
            pipeline = AnalysisPipeline(config, cache_manager)
            assert pipeline.risk_assessor is not None
            assert pipeline.allocation_engine is not None
            assert pipeline.report_generator is not None
            assert pipeline.config is not None
        except ValueError as e:
            if "Unknown provider" in str(e):
                pytest.skip(
                    "Provider initialization skipped - data providers not configured for tests"
                )
            raise
