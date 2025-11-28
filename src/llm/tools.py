"""CrewAI tool adapters for analysis functions."""

import json
from datetime import date, datetime

from crewai.tools import tool

from src.tools.analysis import TechnicalIndicatorTool
from src.tools.fetchers import FinancialDataFetcherTool, NewsFetcherTool, PriceFetcherTool
from src.utils.logging import get_logger

logger = get_logger(__name__)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code.

    Args:
        obj: Object to serialize

    Returns:
        Serialized representation
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class CrewAIToolAdapter:
    """Adapts existing tools for use with CrewAI agents."""

    def __init__(self):
        """Initialize tool adapters."""
        self.price_fetcher = PriceFetcherTool()
        self.technical_tool = TechnicalIndicatorTool()
        self.news_fetcher = NewsFetcherTool()
        self.fundamental_fetcher = FinancialDataFetcherTool()
        # Cache to store data between tool calls
        self._data_cache = {}
        # Initialize tools once
        self._tools = self._create_tools()

    def _create_tools(self) -> list:
        """Create CrewAI-compatible tools.

        Returns:
            List of CrewAI tool instances
        """

        @tool("Fetch Price Data")
        def fetch_price_data(ticker: str, days_back: int = 60) -> str:
            """Fetch historical and current price data for an instrument.

            Args:
                ticker: Stock ticker symbol
                days_back: Number of days of history to fetch

            Returns:
                JSON string with summary of price data (full data cached for other tools)
            """
            try:
                result = self.price_fetcher.run(ticker, days_back=days_back)
                if "error" in result:
                    return json.dumps({"error": result["error"]})

                # Store full data in cache for technical analysis
                cache_key = f"prices_{ticker}"
                self._data_cache[cache_key] = result.get("prices", [])

                # Return only summary to avoid truncation
                summary = {
                    "ticker": result.get("ticker"),
                    "count": result.get("count", 0),
                    "start_date": result.get("start_date"),
                    "end_date": result.get("end_date"),
                    "latest_price": result.get("latest_price"),
                    "cache_key": cache_key,
                    "message": f"Fetched {result.get('count', 0)} price data points. Use cache_key '{cache_key}' for technical analysis.",
                }

                return json.dumps(summary, default=json_serial)
            except Exception as e:
                logger.error(f"Error fetching price data for {ticker}: {e}")
                return json.dumps({"error": str(e)})

        @tool("Calculate Technical Indicators")
        def calculate_technical_indicators(ticker: str) -> str:
            """Calculate technical indicators and return pre-computed analysis.

            This tool performs the mathematical calculations directly (rule-based)
            and returns the results for LLM interpretation.

            Args:
                ticker: Stock ticker symbol

            Returns:
                JSON string with calculated indicators and automated technical analysis
            """
            try:
                # Use cached price data
                cache_key = f"prices_{ticker}"
                if cache_key not in self._data_cache:
                    return json.dumps(
                        {
                            "error": f"No price data cached for {ticker}. Call fetch_price_data first."
                        }
                    )

                prices = self._data_cache[cache_key]
                if not prices:
                    return json.dumps({"error": "No price data available"})

                # Perform rule-based technical analysis calculations
                result = self.technical_tool.run(prices)
                if "error" in result:
                    return json.dumps({"error": result["error"]})

                # Add interpretation hints for the LLM (but calculations are done)
                result["analysis_type"] = "rule_based_calculations"
                result["note"] = (
                    "Technical indicators calculated using mathematical formulas. LLM should interpret these signals."
                )

                return json.dumps(result, default=json_serial)
            except Exception as e:
                logger.error(f"Error calculating technical indicators: {e}")
                return json.dumps({"error": str(e)})

        @tool("Analyze Sentiment")
        def analyze_sentiment(ticker: str, max_articles: int = 50, max_age_hours: int = 168) -> str:
            """Fetch news and perform LLM-based sentiment analysis.

            This tool fetches news articles and uses LLM to analyze sentiment
            (since providers often don't include sentiment data).

            Args:
                ticker: Stock ticker symbol
                max_articles: Maximum number of articles to fetch
                max_age_hours: Maximum age of articles in hours

            Returns:
                JSON string with news articles for LLM sentiment analysis
            """
            try:
                # Fetch news articles
                news_result = self.news_fetcher.run(
                    ticker, limit=max_articles, max_age_hours=max_age_hours
                )
                if "error" in news_result:
                    return json.dumps({"error": news_result["error"]})

                articles = news_result.get("articles", [])

                if not articles:
                    return json.dumps(
                        {
                            "ticker": ticker,
                            "articles": [],
                            "count": 0,
                            "note": "No news articles found for analysis",
                        }
                    )

                # Prepare articles for LLM analysis (limit fields to avoid truncation)
                articles_for_analysis = [
                    {
                        "title": a.get("title", ""),
                        "summary": (
                            a.get("summary", "")[:200] if a.get("summary") else ""
                        ),  # Limit summary length
                        "source": a.get("source", ""),
                        "published_date": a.get("published_date"),
                    }
                    for a in articles[:20]  # Limit to 20 most recent to avoid truncation
                ]

                result = {
                    "ticker": ticker,
                    "articles": articles_for_analysis,
                    "total_articles": len(articles),
                    "analysis_type": "llm_sentiment_analysis_required",
                    "note": (
                        "Articles fetched successfully. LLM should analyze each article's title and summary "
                        "to determine sentiment (positive/negative/neutral), score each article, identify "
                        "key themes and events, and provide an overall sentiment assessment."
                    ),
                }

                return json.dumps(result, default=json_serial)
            except Exception as e:
                logger.error(f"Error analyzing sentiment for {ticker}: {e}")
                return json.dumps({"error": str(e)})

        @tool("Fetch Fundamental Data")
        def fetch_fundamental_data(ticker: str) -> str:
            """Fetch fundamental data using free tier APIs.

            This tool fetches real fundamental data from free tier endpoints:
            - Analyst recommendations (Finnhub free tier)
            - News sentiment scores (Finnhub free tier)
            - Price momentum context (Yahoo Finance free tier)

            Args:
                ticker: Stock ticker symbol

            Returns:
                JSON string with analyst consensus, sentiment, and momentum data
            """
            try:
                # Fetch fundamental data using the tool
                fundamental_result = self.fundamental_fetcher.run(ticker)

                if "error" in fundamental_result:
                    return json.dumps({"error": fundamental_result["error"]})

                # Extract data components
                analyst_data = fundamental_result.get("analyst_data", {})
                sentiment = fundamental_result.get("sentiment", {})
                price_context = fundamental_result.get("price_context", {})
                data_availability = fundamental_result.get("data_availability", "unknown")

                # Check if we have any real data
                has_analyst_data = analyst_data and analyst_data.get("total_analysts", 0) > 0
                has_sentiment_data = sentiment and (
                    sentiment.get("positive", 0) + sentiment.get("negative", 0) > 0
                )
                has_price_data = price_context and price_context.get("change_percent") is not None

                # Format for LLM analysis
                result = {
                    "ticker": ticker,
                    "data_availability": data_availability,
                    "analyst_consensus": {
                        "available": has_analyst_data,
                        "strong_buy": analyst_data.get("strong_buy", 0),
                        "buy": analyst_data.get("buy", 0),
                        "hold": analyst_data.get("hold", 0),
                        "sell": analyst_data.get("sell", 0),
                        "strong_sell": analyst_data.get("strong_sell", 0),
                        "total_analysts": analyst_data.get("total_analysts", 0),
                        "period": analyst_data.get("period", "latest"),
                    },
                    "news_sentiment": {
                        "available": has_sentiment_data,
                        "positive": sentiment.get("positive", 0),
                        "negative": sentiment.get("negative", 0),
                        "neutral": sentiment.get("neutral", 0),
                        "note": (
                            "Sentiment from news coverage analysis"
                            if has_sentiment_data
                            else "No sentiment data available"
                        ),
                    },
                    "price_momentum": {
                        "available": has_price_data,
                        "change_percent": price_context.get("change_percent", 0),
                        "trend": price_context.get("trend", "neutral"),
                        "latest_price": price_context.get("latest_price"),
                        "period_days": price_context.get("period_days", 30),
                    },
                    "data_sources": "Free tier APIs only (Finnhub + Yahoo Finance)",
                    "note": (
                        "Real fundamental data from free tier endpoints. "
                        "Use analyst consensus, sentiment distribution, and momentum "
                        "to assess fundamental strength. "
                        f"Data available: {data_availability}. "
                        "If data is limited, acknowledge the limitation and focus on available information."
                    ),
                }

                return json.dumps(result, default=json_serial)
            except Exception as e:
                logger.error(f"Error fetching fundamental data for {ticker}: {e}")
                return json.dumps({"error": str(e)})

        return [
            fetch_price_data,
            calculate_technical_indicators,
            analyze_sentiment,
            fetch_fundamental_data,
        ]

    def get_crewai_tools(self) -> list:
        """Get all tools as CrewAI-compatible tool list.

        Returns:
            List of CrewAI tool instances
        """
        return self._tools
