# About NordInvest

NordInvest is an AI-powered financial analysis system that generates investment recommendations based on comprehensive market data analysis.

## Overview

NordInvest combines multiple data sources and analytical approaches to provide investment signals:

- **Technical Analysis**: Price patterns, volume trends, and momentum indicators
- **Fundamental Analysis**: Financial metrics, earnings data, and valuation ratios
- **Sentiment Analysis**: News sentiment and market perception
- **AI-Powered Insights**: LLM-based deep analysis using Claude/GPT models

## Analysis Modes

### Rule-Based Analysis
Traditional algorithmic approach using predefined rules and thresholds to evaluate investment opportunities.

### LLM-Powered Analysis
Advanced AI analysis using large language models to synthesize complex market data and generate nuanced investment recommendations.

## Signal Types

The system generates the following signal types:

- 🎯 **Strong Buy**: High confidence buy signals with strong fundamentals
- 📈 **Buy**: Moderate buy signals with positive outlook
- ⏸️ **Hold (Bullish)**: Maintain position with positive bias
- ⏸️ **Hold**: Maintain position, neutral outlook
- ⏸️ **Hold (Bearish)**: Maintain position with cautious outlook
- 📉 **Sell**: Moderate sell signals
- 🔴 **Strong Sell**: High confidence sell signals

## Key Features

- **Multi-Source Data Integration**: Combines price data, fundamentals, news, and sentiment
- **Confidence Scoring**: Each signal includes a confidence score (0-100%)
- **Risk Assessment**: Identifies risk factors and potential concerns
- **Deduplication**: Ensures only the best recommendation per ticker per day
- **Historical Analysis**: Supports backtesting with historical dates
- **Performance Tracking**: Monitors recommendation accuracy over time

## Data Sources

- Market data from multiple providers (yfinance, Alpha Vantage, etc.)
- Financial fundamentals and metrics
- News articles and sentiment analysis
- Analyst ratings and price targets

## Disclaimer

!!! warning "Investment Risk"
    This analysis is for informational purposes only and does not constitute investment advice. All investments carry risk, including potential loss of principal. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making investment decisions.

## Source Code

NordInvest is open source and available on [GitHub](https://github.com/ironcladgeek/NordInvest).

## License

Copyright © 2025 NordInvest. All rights reserved.
