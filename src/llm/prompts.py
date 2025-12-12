"""Prompt templates for LLM-based analysis agents."""


class PromptTemplates:
    """Collection of prompt templates for analysis agents."""

    TECHNICAL_SYSTEM = """You are a senior technical analyst with expertise in:
- Chart pattern recognition
- Technical indicators (moving averages, RSI, MACD, ATR)
- Support and resistance identification
- Trend analysis and momentum assessment
- Volume analysis

Your analysis should be data-driven and interpret multiple indicators holistically.
Provide clear, actionable technical insights with confidence levels."""

    TECHNICAL_TEMPLATE = """Perform technical analysis of {ticker} using these indicators:

Price Data:
- Current price: ${current_price}
- SMA 20: ${sma_20}
- SMA 50: ${sma_50}
- SMA 200: ${sma_200}

Momentum Indicators:
- RSI (14): {rsi}
- MACD: {macd_line} (Signal: {macd_signal}, Histogram: {macd_histogram})

Volatility:
- ATR: {atr}
- Beta: {beta}

Volume:
- Current: {volume:,}
- Average (20-day): {avg_volume:,}

Analyze:
1. Current trend (uptrend/downtrend/range-bound)
2. Trend strength (strong/moderate/weak)
3. Support and resistance levels
4. Key technical signals
5. Overall technical score (0-100)

Format response as JSON:
{{
  "trend": "uptrend/downtrend/range",
  "trend_strength": "strong/moderate/weak",
  "support_levels": [price1, price2, ...],
  "resistance_levels": [price1, price2, ...],
  "key_signals": ["signal1", "signal2", ...],
  "score": 0-100,
  "reasoning": "brief explanation"
}}"""

    FUNDAMENTAL_SYSTEM = """You are an experienced fundamental analyst expert in:
- Financial statement analysis
- Valuation metrics interpretation
- Industry benchmarking
- Business quality assessment
- Growth prospects evaluation

Analyze companies comprehensively considering financial health, growth, and valuation.
Provide reasoned assessments backed by specific metrics."""

    FUNDAMENTAL_TEMPLATE = """Analyze fundamentals of {ticker}:

Financial Metrics:
- Revenue (TTM): ${revenue:,.0f}M
- Revenue growth (YoY): {revenue_growth}%
- EPS (TTM): ${eps:.2f}
- EPS growth (YoY): {eps_growth}%
- Net profit margin: {net_margin}%
- Operating margin: {op_margin}%
- ROE: {roe}%

Valuation:
- P/E Ratio: {pe_ratio:.1f}x
- EV/EBITDA: {ev_ebitda:.1f}x
- P/B Ratio: {pb_ratio:.1f}x
- PEG Ratio: {peg_ratio:.1f}x
- Dividend yield: {div_yield}%

Financial Health:
- Debt/Equity: {debt_to_equity:.2f}
- Current ratio: {current_ratio:.2f}
- Free cash flow (TTM): ${fcf:,.0f}M
- FCF margin: {fcf_margin}%

Evaluate:
1. Business quality and competitive position
2. Growth prospects (short/medium/long-term)
3. Valuation attractiveness
4. Financial risks and concerns
5. Overall fundamental score (0-100)

Format response as JSON:
{{
  "business_quality": "excellent/good/fair/poor",
  "growth_prospects": "strong/moderate/weak",
  "valuation": "attractive/fair/expensive",
  "financial_health": "strong/stable/concerning/weak",
  "key_strengths": ["strength1", "strength2", ...],
  "key_risks": ["risk1", "risk2", ...],
  "score": 0-100,
  "reasoning": "detailed explanation"
}}"""

    SENTIMENT_SYSTEM = """You are a skilled sentiment analyst expert in:
- News analysis and categorization
- Event impact assessment
- Sentiment classification (positive/negative/neutral)
- Key catalyst identification
- Market reaction prediction

Analyze news and events objectively, assessing their potential market impact.
Provide quantified sentiment assessments."""

    SENTIMENT_TEMPLATE = """Analyze sentiment for {ticker}:

Recent News (last 7 days):
{news_items}

Analyze:
1. Overall sentiment (positive/negative/neutral)
2. Key events and catalysts
3. Event categories (earnings, product, regulatory, competitive, macro)
4. Potential market impact assessment
5. Analyst rating trend (if available)
6. Overall sentiment score (0-100)

Format response as JSON:
{{
  "overall_sentiment": "positive/negative/neutral",
  "sentiment_score": 0-100,
  "key_catalysts": [
    {{"event": "event name", "type": "category", "impact": "positive/negative/neutral"}},
    ...
  ],
  "analyst_trends": "improving/stable/deteriorating",
  "event_summary": "brief overview",
  "market_impact": "high/medium/low",
  "reasoning": "explanation of sentiment assessment"
}}"""

    SYNTHESIZER_SYSTEM = """You are a senior investment strategist responsible for synthesizing
multiple perspectives into coherent investment signals. You excel at:
- Balancing conflicting signals
- Identifying consensus and disagreement
- Assessing confidence levels
- Crafting clear investment narratives
- Risk-aware recommendation generation

Synthesize technical, fundamental, and sentiment analyses into actionable investment signals."""

    SYNTHESIZER_TEMPLATE = """Synthesize investment signal for {ticker}:

Technical Analysis:
{technical_analysis}

Fundamental Analysis:
{fundamental_analysis}

Sentiment Analysis:
{sentiment_analysis}

Synthesize into:
1. Combined investment score (weights: 35% fundamental, 35% technical, 30% sentiment)
2. Recommendation (Buy/Hold/Avoid)
3. Confidence level (0-100%)
4. Key investment thesis (2-3 sentences)
5. Main catalysts
6. Key risks
7. Time horizon
8. Expected return range

Format response as JSON:
{{
  "ticker": "{ticker}",
  "combined_score": 0-100,
  "recommendation": "Buy/Hold/Avoid",
  "confidence": 0-100,
  "thesis": "2-3 sentence investment case",
  "catalysts": ["catalyst1", "catalyst2", ...],
  "risks": ["risk1", "risk2", ...],
  "time_horizon_months": 1-36,
  "expected_return_min": float,
  "expected_return_max": float,
  "reasoning": "detailed explanation of signal",
  "factor_agreement": "high/medium/low"
}}"""

    @staticmethod
    def get_technical_prompt(ticker: str, data: dict) -> str:
        """Get technical analysis prompt with data.

        Args:
            ticker: Stock ticker symbol
            data: Technical data dictionary

        Returns:
            Formatted prompt
        """
        return PromptTemplates.TECHNICAL_TEMPLATE.format(
            ticker=ticker,
            current_price=data.get("current_price", "N/A"),
            sma_20=data.get("sma_20", "N/A"),
            sma_50=data.get("sma_50", "N/A"),
            sma_200=data.get("sma_200", "N/A"),
            rsi=data.get("rsi", "N/A"),
            macd_line=data.get("macd_line", "N/A"),
            macd_signal=data.get("macd_signal", "N/A"),
            macd_histogram=data.get("macd_histogram", "N/A"),
            atr=data.get("atr", "N/A"),
            beta=data.get("beta", "N/A"),
            volume=data.get("volume", 0),
            avg_volume=data.get("avg_volume", 0),
        )

    @staticmethod
    def get_fundamental_prompt(ticker: str, data: dict) -> str:
        """Get fundamental analysis prompt with data.

        Args:
            ticker: Stock ticker symbol
            data: Fundamental data dictionary

        Returns:
            Formatted prompt
        """
        return PromptTemplates.FUNDAMENTAL_TEMPLATE.format(
            ticker=ticker,
            revenue=data.get("revenue", 0),
            revenue_growth=data.get("revenue_growth", "N/A"),
            eps=data.get("eps", 0),
            eps_growth=data.get("eps_growth", "N/A"),
            net_margin=data.get("net_margin", "N/A"),
            op_margin=data.get("op_margin", "N/A"),
            roe=data.get("roe", "N/A"),
            pe_ratio=data.get("pe_ratio", "N/A"),
            ev_ebitda=data.get("ev_ebitda", "N/A"),
            pb_ratio=data.get("pb_ratio", "N/A"),
            peg_ratio=data.get("peg_ratio", "N/A"),
            div_yield=data.get("div_yield", "N/A"),
            debt_to_equity=data.get("debt_to_equity", 0),
            current_ratio=data.get("current_ratio", 0),
            fcf=data.get("fcf", 0),
            fcf_margin=data.get("fcf_margin", "N/A"),
        )

    @staticmethod
    def get_sentiment_prompt(ticker: str, data: dict) -> str:
        """Get sentiment analysis prompt with data.

        Args:
            ticker: Stock ticker symbol
            data: Sentiment data dictionary with news items

        Returns:
            Formatted prompt
        """
        news_items = "\n".join(
            [
                f"- {item.get('title', 'N/A')}: {item.get('summary', '')}"
                for item in data.get("news", [])
            ]
        )

        return PromptTemplates.SENTIMENT_TEMPLATE.format(
            ticker=ticker,
            news_items=news_items or "No recent news",
        )

    @staticmethod
    def get_synthesizer_prompt(
        ticker: str,
        technical_data: dict,
        fundamental_data: dict,
        sentiment_data: dict,
    ) -> str:
        """Get signal synthesis prompt with all analysis data.

        Args:
            ticker: Stock ticker symbol
            technical_data: Technical analysis results
            fundamental_data: Fundamental analysis results
            sentiment_data: Sentiment analysis results

        Returns:
            Formatted prompt
        """
        return PromptTemplates.SYNTHESIZER_TEMPLATE.format(
            ticker=ticker,
            technical_analysis=str(technical_data),
            fundamental_analysis=str(fundamental_data),
            sentiment_analysis=str(sentiment_data),
        )
