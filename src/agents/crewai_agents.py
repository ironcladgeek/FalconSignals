"""CrewAI-based intelligent agents for analysis."""

from typing import Any, Optional

from crewai import Agent, Task

from src.agents.output_models import (
    FundamentalAnalysisOutput,
    SentimentAnalysisOutput,
    SignalSynthesisOutput,
    TechnicalAnalysisOutput,
)
from src.config.llm import initialize_llm_client
from src.config.schemas import LLMConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CrewAIAgentFactory:
    """Factory for creating CrewAI-based agents."""

    # Explicit instruction to use correct tool format (prevents <function_calls> format)
    TOOL_FORMAT_INSTRUCTION = (
        "\n\nCRITICAL: When using tools, you MUST use the exact format:\n"
        "```\n"
        "Thought: your reasoning\n"
        "Action: tool name\n"
        'Action Input: {"param": "value"}\n'
        "```\n"
        "NEVER use <function_calls> tags or any other format. "
        "Wait for the Observation before continuing."
    )

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize the factory with LLM configuration.

        Args:
            llm_config: LLM configuration (uses default if not provided)
        """
        self.llm_config = llm_config or LLMConfig()
        self.llm_client = initialize_llm_client(self.llm_config)
        logger.info(f"Initialized CrewAI factory with {self.llm_config.provider} provider")

    def create_market_scanner_agent(self, tools: list = None) -> Agent:
        """Create market scanner agent.

        Args:
            tools: List of tools available to the agent

        Returns:
            Configured CrewAI Agent for market scanning
        """
        return Agent(
            role="Market Scanner Analyst",
            goal=(
                "Scan financial markets to identify instruments with significant price movements, "
                "unusual volume patterns, and anomalies that warrant deeper analysis"
            ),
            backstory=(
                "You are an expert market analyst with deep knowledge of technical patterns and "
                "market microstructure. You excel at detecting emerging trends, unusual volume "
                "patterns, and price movements that signal potential trading opportunities. "
                "Your keen eye for detail helps identify instruments that deserve deeper analysis. "
                "You consider both daily and weekly price movements, volume anomalies, and positions "
                "at technical extremes." + self.TOOL_FORMAT_INSTRUCTION
            ),
            tools=tools or [],
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )

    def create_technical_analysis_agent(self, tools: list = None) -> Agent:
        """Create technical analysis agent.

        Args:
            tools: List of tools available to the agent

        Returns:
            Configured CrewAI Agent for technical analysis
        """
        return Agent(
            role="Senior Technical Analyst",
            goal=(
                "Interpret pre-calculated technical indicators to provide insights on "
                "trend strength, momentum, support/resistance levels, and trading opportunities. "
                "Extract ALL available indicators including RSI, MACD (line/signal/histogram), "
                "Bollinger Bands (upper/middle/lower), ATR, SMA (20/50), EMA (12/26), WMA, "
                "ADX (with +DI/-DI), Stochastic (%K/%D), and Ichimoku Cloud components."
            ),
            backstory=(
                "You are a skilled technical analyst with expertise in interpreting "
                "chart patterns, moving averages, momentum indicators, and volume analysis. "
                "You receive pre-calculated technical indicators from the Calculate Technical Indicators tool "
                "and must extract ALL available indicator values into your structured output. "
                "The tool provides comprehensive data including: RSI, MACD (line, signal, histogram), "
                "Bollinger Bands (upper, middle, lower), ATR, moving averages (SMA 20/50, EMA 12/26, WMA 14), "
                "ADX with directional indicators (+DI, -DI), Stochastic Oscillator (%K, %D), "
                "and Ichimoku Cloud components (Tenkan, Kijun, Senkou A/B, Chikou). "
                "CRITICAL: You must populate ALL indicator fields in your output schema with the values "
                "from the tool - do not omit any available indicators. "
                "After extracting all values, interpret what these signals mean: "
                "identify trend strength, potential reversals, overbought/oversold conditions, "
                "and support/resistance levels. Your analysis incorporates multiple timeframes "
                "and helps traders make informed decisions based on price action."
                + self.TOOL_FORMAT_INSTRUCTION
            ),
            tools=tools or [],
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )

    def create_fundamental_analysis_agent(self, tools: list = None) -> Agent:
        """Create fundamental analysis agent.

        Args:
            tools: List of tools available to the agent

        Returns:
            Configured CrewAI Agent for fundamental analysis
        """
        return Agent(
            role="Fundamental Analyst",
            goal=(
                "Analyze financial statements and metrics to assess company health, growth "
                "prospects, and valuation. Provide investment-grade fundamental scores."
            ),
            backstory=(
                "You are an experienced fundamental analyst with deep expertise in financial "
                "statement analysis, ratio interpretation, and company valuation. "
                "You evaluate earnings growth, profit margins, cash flow quality, debt levels, "
                "and valuation metrics (P/E, EV/EBITDA, P/B, PEG). "
                "You can identify high-quality companies at reasonable valuations and weak "
                "companies even if they appear cheap. You understand industry dynamics and "
                "competitive positioning." + self.TOOL_FORMAT_INSTRUCTION
            ),
            tools=tools or [],
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )

    def create_sentiment_analysis_agent(self, tools: list = None) -> Agent:
        """Create sentiment analysis agent.

        Args:
            tools: List of tools available to the agent

        Returns:
            Configured CrewAI Agent for sentiment analysis
        """
        return Agent(
            role="Sentiment Analyst",
            goal=(
                "Analyze news article sentiment and identify how news events "
                "and market sentiment impact the investment thesis."
            ),
            backstory=(
                "You are a skilled sentiment analyst with expertise in natural language processing, "
                "news interpretation, and market psychology. "
                "You analyze news article titles and summaries to determine sentiment (positive/negative/neutral) "
                "and assign sentiment scores. You classify events by type (earnings, regulatory, product launches, "
                "competitive, macro) and assess their importance and potential market impact. "
                "You understand how different types of news affect company valuations and stock prices, "
                "and can identify whether sentiment represents rational analysis or emotional overreaction. "
                "You excel at identifying key themes, catalysts, and sentiment trends from news coverage."
                + self.TOOL_FORMAT_INSTRUCTION
            ),
            tools=tools or [],
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )

    def create_signal_synthesizer_agent(self) -> Agent:
        """Create signal synthesizer agent.

        Returns:
            Configured CrewAI Agent for signal synthesis
        """
        return Agent(
            role="Investment Signal Synthesizer",
            goal=(
                "Synthesize technical, fundamental, and sentiment analyses into comprehensive "
                "investment signals with clear reasoning and risk assessment"
            ),
            backstory=(
                "You are a senior investment strategist responsible for synthesizing insights "
                "from multiple analysis perspectives. "
                "You combine technical, fundamental, and sentiment signals into coherent "
                "investment theses. You weigh conflicting signals, identify consensus areas, "
                "and provide clear recommendation rationale. "
                "You assess confidence levels based on signal agreement and data quality. "
                "You generate human-readable investment narratives that explain the investment case. "
                "\n"
                "IMPORTANT: You do NOT have access to any tools. All necessary analysis data "
                "(technical indicators, fundamental metrics, sentiment analysis) will be provided "
                "directly in your task description. Your job is to synthesize this pre-computed data "
                "into a structured JSON investment signal. Do NOT attempt to fetch or calculate any data. "
                "Focus entirely on analyzing the provided results and generating the required JSON output."
            ),
            tools=[],  # No tools - synthesizer receives pre-computed results
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )


class CrewAITaskFactory:
    """Factory for creating structured CrewAI tasks."""

    @staticmethod
    def create_market_scan_task(
        agent: Agent,
        ticker: str,
        context: dict[str, Any],
    ) -> Task:
        """Create market scanning task.

        Args:
            agent: Market scanner agent
            ticker: Stock ticker symbol
            context: Additional context for the scan

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Scan {ticker} for market anomalies and trading signals.\n"
                f"Analyze the following data:\n"
                f"- Price movements (daily and weekly changes)\n"
                f"- Volume patterns and anomalies\n"
                f"- Technical extremes (30-day highs/lows)\n"
                f"\n"
                f"Identify:\n"
                f"1. Significant price movements (>5% daily, >15% weekly)\n"
                f"2. Unusual volume spikes (>1.5x average)\n"
                f"3. New 30-day highs or lows\n"
                f"4. Any other market anomalies\n"
                f"\n"
                f"Provide a clear assessment of whether {ticker} warrants deeper analysis."
            ),
            agent=agent,
            expected_output=(
                "List of anomalies found with explanations and recommendation to analyze further"
            ),
        )

    @staticmethod
    def create_technical_analysis_task(
        agent: Agent,
        ticker: str,
        context: dict[str, Any],
    ) -> Task:
        """Create technical analysis task.

        Args:
            agent: Technical analyst agent
            ticker: Stock ticker symbol
            context: Additional context including price data

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Extract and interpret the pre-calculated technical indicators for {ticker}.\n"
                f"\n"
                f"STEP 1: EXTRACT ALL INDICATOR VALUES\n"
                f"Use the 'Calculate Technical Indicators' tool with ticker='{ticker}' to get "
                f"comprehensive technical data. The tool returns ALL available indicators including:\n"
                f"- RSI (rsi)\n"
                f"- MACD components (macd_line, macd_signal, macd_histogram)\n"
                f"- Bollinger Bands (bbands_20_upper, bbands_20_middle, bbands_20_lower)\n"
                f"- ATR (atr_14)\n"
                f"- Moving Averages (sma_20, sma_50, ema_12, ema_26, wma_14)\n"
                f"- ADX with directional indicators (adx_14, adx_14_dmp, adx_14_dmn)\n"
                f"- Stochastic (stoch_14_3_k, stoch_14_3_d)\n"
                f"- Ichimoku Cloud (ichimoku_tenkan, ichimoku_kijun, ichimoku_senkou_a, ichimoku_senkou_b, ichimoku_chikou)\n"
                f"\n"
                f"CRITICAL: You MUST extract ALL indicator values from the tool output and populate "
                f"ALL corresponding fields in your TechnicalAnalysisOutput. Do not omit any indicators - "
                f"extract every value the tool provides.\n"
                f"\n"
                f"STEP 2: INTERPRET THE INDICATORS\n"
                f"After extracting all values, provide expert interpretation:\n"
                f"1. Analyze the trend (is the price above/below key moving averages?)\n"
                f"2. Assess momentum (what do RSI, MACD, and Stochastic values indicate?)\n"
                f"3. Identify overbought/oversold conditions (RSI > 70 or < 30? Stochastic levels?)\n"
                f"4. Evaluate Bollinger Band position (price near upper/lower band?)\n"
                f"5. Assess trend strength using ADX (>25 = strong trend)\n"
                f"6. Analyze Ichimoku Cloud signals (price vs cloud, cloud color)\n"
                f"7. Determine support/resistance levels from moving averages\n"
                f"8. Identify potential entry/exit points based on multiple indicators\n"
                f"9. Assess overall technical strength and provide a score (0-100)\n"
                f"\n"
                f"Do NOT calculate indicators yourself - they are pre-calculated. Your job is to "
                f"extract ALL values and then provide expert interpretation."
            ),
            agent=agent,
            expected_output=(
                "Complete TechnicalAnalysisOutput with ALL indicator fields populated (RSI, MACD components, "
                "Bollinger Bands, ATR, all moving averages, ADX components, Stochastic components, and "
                "Ichimoku Cloud components) plus trend assessment, momentum analysis, signal interpretation, "
                "and technical score (0-100)"
            ),
            output_pydantic=TechnicalAnalysisOutput,
        )

    @staticmethod
    def create_fundamental_analysis_task(
        agent: Agent,
        ticker: str,
        context: dict[str, Any],
    ) -> Task:
        """Create fundamental analysis task.

        Args:
            agent: Fundamental analyst agent
            ticker: Stock ticker symbol
            context: Additional context including financial data

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Analyze fundamentals of {ticker}.\n"
                f"\n"
                f"IMPORTANT: Use the 'Fetch Fundamental Data' tool with ticker='{ticker}' "
                f"to get real fundamental data from free tier APIs.\n"
                f"\n"
                f"This tool provides:\n"
                f"1. Analyst Consensus - Professional analyst recommendations (strong buy/buy/hold/sell/strong sell)\n"
                f"2. News Sentiment - Aggregated sentiment from news coverage (positive/negative/neutral %)\n"
                f"3. Price Momentum - 30-day price change and trend direction\n"
                f"4. Financial Metrics (from Yahoo Finance):\n"
                f"   - Valuation: trailing_pe, forward_pe, price_to_book, price_to_sales, peg_ratio, enterprise_to_ebitda\n"
                f"   - Profitability: gross_margin, operating_margin, profit_margin, return_on_equity, return_on_assets\n"
                f"   - Financial Health: debt_to_equity, current_ratio, quick_ratio, free_cashflow\n"
                f"   - Growth: revenue_growth, earnings_growth\n"
                f"\n"
                f"CRITICAL: Extract and include the financial metrics in your output:\n"
                f"- pe_ratio: Use trailing_pe from valuation metrics\n"
                f"- forward_pe: Use forward_pe from valuation metrics\n"
                f"- pb_ratio: Use price_to_book from valuation metrics\n"
                f"- ps_ratio: Use price_to_sales from valuation metrics\n"
                f"- peg_ratio: Use peg_ratio from valuation metrics\n"
                f"- ev_ebitda: Use enterprise_to_ebitda from valuation metrics\n"
                f"- profit_margin: Use profit_margin from profitability metrics\n"
                f"- operating_margin: Use operating_margin from profitability metrics\n"
                f"- gross_margin: Use gross_margin from profitability metrics\n"
                f"- roe: Use return_on_equity from profitability metrics\n"
                f"- roa: Use return_on_assets from profitability metrics\n"
                f"- debt_to_equity: Use debt_to_equity from financial_health metrics\n"
                f"- current_ratio: Use current_ratio from financial_health metrics\n"
                f"- revenue_growth: Use revenue_growth from growth metrics\n"
                f"- earnings_growth: Use earnings_growth from growth metrics\n"
                f"\n"
                f"Analyze this data to evaluate:\n"
                f"1. Valuation attractiveness (P/E, P/B, PEG - lower often better)\n"
                f"2. Profitability quality (high margins and ROE are positive)\n"
                f"3. Financial health (low debt, adequate liquidity)\n"
                f"4. Growth prospects (revenue and earnings growth trends)\n"
                f"5. Analyst confidence and consensus\n"
                f"6. Business quality and competitive position\n"
                f"7. Financial risks and concerns\n"
                f"\n"
                f"Do NOT make up or hallucinate financial metrics. Use ONLY the data from the tool.\n"
                f"If specific metrics are not available from the tool, set them to null in your output.\n"
                f"\n"
                f"Provide a fundamental score (0-100) based on the real data fetched."
            ),
            agent=agent,
            expected_output=(
                "Fundamental analysis with financial metrics (P/E, margins, ROE, debt ratios, growth), "
                "analyst consensus interpretation, valuation assessment, and fundamental score (0-100)"
            ),
            output_pydantic=FundamentalAnalysisOutput,
        )

    @staticmethod
    def create_sentiment_analysis_task(
        agent: Agent,
        ticker: str,
        context: dict[str, Any],
    ) -> Task:
        """Create sentiment analysis task.

        Args:
            agent: Sentiment analyst agent
            ticker: Stock ticker symbol
            context: Additional context including news data

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Analyze news sentiment for {ticker}.\n"
                f"\n"
                f"Use the 'Analyze Sentiment' tool with ticker='{ticker}' to fetch recent news articles.\n"
                f"\n"
                f"For each article, analyze the title and summary to:\n"
                f"1. Determine sentiment: positive, negative, or neutral\n"
                f"2. Assign a sentiment score (-1.0 to +1.0)\n"
                f"3. Classify the event type (earnings, product launch, partnership, regulatory, competitive, etc.)\n"
                f"4. Assess importance/impact (0-100)\n"
                f"\n"
                f"Then synthesize the analysis:\n"
                f"1. Calculate overall sentiment distribution (% positive/negative/neutral)\n"
                f"2. Identify major themes and patterns\n"
                f"3. Highlight key catalysts or events\n"
                f"4. Assess whether sentiment aligns with or contradicts fundamentals\n"
                f"5. Determine if there are any sentiment shifts or trends\n"
                f"6. Provide an overall sentiment score (0-100)\n"
                f"\n"
                f"Focus on quality analysis - sentiment classification requires understanding context, "
                f"not just keyword matching."
            ),
            agent=agent,
            expected_output=(
                "Sentiment analysis with article-level sentiment scores, key themes, event classification, "
                "overall sentiment distribution, and final sentiment score (0-100)"
            ),
            output_pydantic=SentimentAnalysisOutput,
        )

    @staticmethod
    def create_signal_synthesis_task(
        agent: Agent,
        ticker: str,
        technical_analysis: dict[str, Any],
        fundamental_analysis: dict[str, Any],
        sentiment_analysis: dict[str, Any],
    ) -> Task:
        """Create signal synthesis task.

        Args:
            agent: Signal synthesizer agent
            ticker: Stock ticker symbol
            technical_analysis: Technical analysis results
            fundamental_analysis: Fundamental analysis results
            sentiment_analysis: Sentiment analysis results

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Synthesize all analyses for {ticker} into a structured investment signal.\n"
                f"\n"
                f"CRITICAL RULES - FOLLOW EXACTLY:\n"
                f"✓ DO: Synthesize the analysis data provided below\n"
                f"✓ DO: Output ONLY a JSON object (no markdown, no text before or after)\n"
                f"✓ DO: Extract scores from the analysis results provided\n"
                f"✓ DO: Calculate final_score = (tech_score * 0.35) + (fundamental_score * 0.35) + (sentiment_score * 0.30)\n"
                f"✗ DO NOT: Attempt to fetch or retrieve any data\n"
                f"✗ DO NOT: Use any tools or make any function calls\n"
                f"✗ DO NOT: Ask for additional data\n"
                f"✗ DO NOT: Generate explanations, markdown, or any text other than the JSON\n"
                f"✗ DO NOT: Use <function_calls> or any code blocks\n"
                f"\n"
                f"ANALYSIS DATA TO SYNTHESIZE:\n"
                f"---BEGIN TECHNICAL ANALYSIS---\n"
                f"{technical_analysis}\n"
                f"---END TECHNICAL ANALYSIS---\n"
                f"\n"
                f"---BEGIN FUNDAMENTAL ANALYSIS---\n"
                f"{fundamental_analysis}\n"
                f"---END FUNDAMENTAL ANALYSIS---\n"
                f"\n"
                f"---BEGIN SENTIMENT ANALYSIS---\n"
                f"{sentiment_analysis}\n"
                f"---END SENTIMENT ANALYSIS---\n"
                f"\n"
                f"OUTPUT SPECIFICATION:\n"
                f"Generate ONLY a valid JSON object with this exact structure (start with '{{' and end with '}}'):\n"
                f"{{\n"
                f'  "ticker": "{ticker}",\n'
                f'  "name": "Company Name",\n'
                f'  "market": "Market Name",\n'
                f'  "sector": "Sector or null",\n'
                f'  "current_price": 123.45,\n'
                f'  "currency": "USD",\n'
                f'  "scores": {{\n'
                f'    "technical": 0-100,\n'
                f'    "fundamental": 0-100,\n'
                f'    "sentiment": 0-100\n'
                f"  }},\n"
                f'  "final_score": 0-100 (weighted: fundamental 35%, technical 35%, sentiment 30%),\n'
                f'  "recommendation": "strong_buy|buy|hold_bullish|hold|hold_bearish|sell|strong_sell",\n'
                f'  "confidence": 0-100,\n'
                f'  "time_horizon": "1W|1M|3M|6M|1Y",\n'
                f'  "expected_return_min": -100 to 500,\n'
                f'  "expected_return_max": -100 to 500,\n'
                f'  "key_reasons": ["reason1", "reason2", "reason3"],\n'
                f'  "risk": {{\n'
                f'    "level": "low|medium|high|very_high",\n'
                f'    "volatility": "low|normal|high",\n'
                f'    "volatility_pct": 0.0-100.0,\n'
                f'    "liquidity": "illiquid|normal|highly_liquid",\n'
                f'    "concentration_risk": true|false,\n'
                f'    "sector_risk": "sector-specific risks or null",\n'
                f'    "flags": ["risk_flag1", "risk_flag2"]\n'
                f"  }},\n"
                f'  "rationale": "Detailed investment thesis",\n'
                f'  "caveats": ["caveat1", "caveat2"]\n'
                f"}}\n"
                f"\n"
                f"Guidelines:\n"
                f"- Use scores from each analysis component\n"
                f"- Calculate final_score with weights: fundamental 35%, technical 35%, sentiment 30%\n"
                f"- Recommendation based on final_score: >80=strong_buy, 70-80=buy, 60-70=hold_bullish, "
                f"50-60=hold, 40-50=hold_bearish, 30-40=sell, <30=strong_sell\n"
                f"- Set confidence based on agreement between analyses\n"
                f"- Extract current_price from technical analysis\n"
                f"- Return ONLY the JSON object, nothing else\n"
            ),
            agent=agent,
            expected_output=(
                "Valid JSON object matching the InvestmentSignal schema with all required fields populated"
            ),
            output_pydantic=SignalSynthesisOutput,
        )
