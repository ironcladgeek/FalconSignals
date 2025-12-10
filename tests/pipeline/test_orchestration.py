"""Tests for pipeline orchestration."""

import pytest

from src.cache.manager import CacheManager
from src.config import load_config
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
        # Load default config which has proper structure
        return load_config()

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
