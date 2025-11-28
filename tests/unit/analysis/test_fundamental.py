"""Tests for fundamental analysis module using free tier data."""

from src.analysis.fundamental import FundamentalAnalyzer


class TestFundamentalAnalyzer:
    """Test FundamentalAnalyzer class with free tier data sources."""

    def test_calculate_score_with_all_data(self):
        """Test scoring with complete data from all sources."""
        analyst_data = {
            "strong_buy": 5,
            "buy": 8,
            "hold": 3,
            "sell": 1,
            "strong_sell": 0,
            "total_analysts": 17,
        }
        price_context = {"change_percent": 0.08, "trend": "bullish"}
        sentiment_score = 75  # From News & Sentiment Agent

        result = FundamentalAnalyzer.calculate_score(analyst_data, price_context, sentiment_score)

        assert "overall_score" in result
        assert "analyst_score" in result
        assert "sentiment_score" in result
        assert "momentum_score" in result
        assert 0 <= result["overall_score"] <= 100
        assert result["sentiment_score"] == 75

    def test_calculate_score_no_data(self):
        """Test scoring with no data (all neutral)."""
        result = FundamentalAnalyzer.calculate_score(None, None, None)

        assert result["overall_score"] == 50  # Neutral score
        assert result["analyst_score"] == 50
        assert result["sentiment_score"] == 50
        assert result["momentum_score"] == 50

    def test_calculate_score_with_sentiment_from_agent(self):
        """Test scoring when sentiment comes from News & Sentiment Agent."""
        analyst_data = {
            "strong_buy": 10,
            "buy": 5,
            "hold": 2,
            "sell": 1,
            "strong_sell": 0,
            "total_analysts": 18,
        }
        price_context = {"change_percent": 0.05, "trend": "bullish"}
        sentiment_score = 65  # From CrewAI agent analysis

        result = FundamentalAnalyzer.calculate_score(analyst_data, price_context, sentiment_score)

        # Overall score is 50% analyst + 50% momentum (sentiment tracked separately)
        assert result["overall_score"] > 60
        assert result["sentiment_score"] == 65

    def test_score_analyst_consensus_bullish(self):
        """Test analyst consensus scoring with strong buy consensus."""
        analyst_data = {
            "strong_buy": 10,
            "buy": 5,
            "hold": 2,
            "sell": 1,
            "strong_sell": 0,
            "total_analysts": 18,
        }

        score = FundamentalAnalyzer._score_analyst_consensus(analyst_data)

        assert score > 70  # Strong bullish consensus

    def test_score_analyst_consensus_bearish(self):
        """Test analyst consensus scoring with bearish consensus."""
        analyst_data = {
            "strong_buy": 0,
            "buy": 2,
            "hold": 3,
            "sell": 8,
            "strong_sell": 5,
            "total_analysts": 18,
        }

        score = FundamentalAnalyzer._score_analyst_consensus(analyst_data)

        assert score < 30  # Bearish consensus

    def test_score_analyst_consensus_no_data(self):
        """Test analyst scoring with no data."""
        score = FundamentalAnalyzer._score_analyst_consensus(None)
        assert score == 50

    def test_score_momentum_bullish(self):
        """Test momentum scoring with bullish trend."""
        price_context = {"change_percent": 0.10, "trend": "bullish"}

        score = FundamentalAnalyzer._score_momentum(price_context)

        assert score > 60  # Bullish momentum

    def test_score_momentum_bearish(self):
        """Test momentum scoring with bearish trend."""
        price_context = {"change_percent": -0.10, "trend": "bearish"}

        score = FundamentalAnalyzer._score_momentum(price_context)

        assert score < 40  # Bearish momentum

    def test_score_momentum_neutral(self):
        """Test momentum scoring with neutral trend."""
        price_context = {"change_percent": 0.01, "trend": "neutral"}

        score = FundamentalAnalyzer._score_momentum(price_context)

        assert 45 < score < 55  # Close to neutral

    def test_score_momentum_no_data(self):
        """Test momentum scoring with no data."""
        score = FundamentalAnalyzer._score_momentum(None)
        assert score == 50

    def test_get_recommendation_strong_buy(self):
        """Test recommendation for high score."""
        recommendation = FundamentalAnalyzer.get_recommendation(80)
        assert recommendation == "strong_buy"

    def test_get_recommendation_buy(self):
        """Test recommendation for good score."""
        recommendation = FundamentalAnalyzer.get_recommendation(65)
        assert recommendation == "buy"

    def test_get_recommendation_hold(self):
        """Test recommendation for neutral score."""
        recommendation = FundamentalAnalyzer.get_recommendation(50)
        assert recommendation == "hold"

    def test_get_recommendation_sell(self):
        """Test recommendation for poor score."""
        recommendation = FundamentalAnalyzer.get_recommendation(30)
        assert recommendation == "sell"

    def test_get_recommendation_strong_sell(self):
        """Test recommendation for very poor score."""
        recommendation = FundamentalAnalyzer.get_recommendation(10)
        assert recommendation == "strong_sell"

    def test_score_bounds(self):
        """Test that all scores stay within 0-100 bounds."""
        # Extreme bullish
        bullish_analyst = {
            "strong_buy": 100,
            "buy": 0,
            "hold": 0,
            "sell": 0,
            "strong_sell": 0,
            "total_analysts": 100,
        }
        bullish_momentum = {"change_percent": 1.0, "trend": "bullish"}

        result = FundamentalAnalyzer.calculate_score(
            bullish_analyst, bullish_momentum, sentiment_score=100
        )
        assert result["overall_score"] <= 100
        assert result["analyst_score"] <= 100
        assert result["momentum_score"] <= 100

        # Extreme bearish
        bearish_analyst = {
            "strong_buy": 0,
            "buy": 0,
            "hold": 0,
            "sell": 0,
            "strong_sell": 100,
            "total_analysts": 100,
        }
        bearish_momentum = {"change_percent": -1.0, "trend": "bearish"}

        result = FundamentalAnalyzer.calculate_score(
            bearish_analyst, bearish_momentum, sentiment_score=0
        )
        assert result["overall_score"] >= 0
        assert result["analyst_score"] >= 0
        assert result["momentum_score"] >= 0

    def test_component_weighting(self):
        """Test that component weighting is applied (50%, 50%)."""
        # High analyst, neutral momentum
        analyst_data = {
            "strong_buy": 15,
            "buy": 0,
            "hold": 0,
            "sell": 0,
            "strong_sell": 0,
            "total_analysts": 15,
        }
        momentum = {"change_percent": 0.0, "trend": "neutral"}

        result = FundamentalAnalyzer.calculate_score(analyst_data, momentum, sentiment_score=50)

        # With high analyst (100), neutral momentum (50)
        # Overall = 100*0.50 + 50*0.50 = 75
        analyst_score = result["analyst_score"]
        momentum_score = result["momentum_score"]
        overall_score = result["overall_score"]

        # Overall should be average of analyst and momentum (50/50 weights)
        assert analyst_score > 95  # Strong buy consensus
        assert momentum_score == 50  # Neutral
        assert 70 < overall_score < 80  # Average between 100 and 50
