"""Pydantic schemas for configuration validation."""

from pydantic import BaseModel, Field, field_validator


class CapitalConfig(BaseModel):
    """Capital settings for portfolio management."""

    starting_capital_eur: float = Field(gt=0, description="Initial capital in EUR")
    monthly_deposit_eur: float = Field(default=0, ge=0, description="Monthly deposit amount in EUR")


class RiskConfig(BaseModel):
    """Risk tolerance and position sizing settings."""

    tolerance: str = Field(
        default="moderate",
        description="Risk tolerance level: conservative, moderate, or aggressive",
    )
    max_position_size_percent: float = Field(
        default=10, ge=1, le=100, description="Maximum position size as % of capital"
    )
    max_sector_concentration_percent: float = Field(
        default=20, ge=1, le=100, description="Max sector concentration as % of capital"
    )

    @field_validator("tolerance")
    @classmethod
    def validate_tolerance(cls, v: str) -> str:
        """Validate risk tolerance is one of allowed values."""
        allowed = {"conservative", "moderate", "aggressive"}
        if v.lower() not in allowed:
            raise ValueError(f"Risk tolerance must be one of {allowed}")
        return v.lower()


class MarketsConfig(BaseModel):
    """Market and instrument preferences."""

    included: list[str] = Field(
        default=["nordic", "eu"], description="Included markets: nordic, eu, us"
    )
    excluded_markets: list[str] = Field(default=[], description="Explicitly excluded markets")
    included_instruments: list[str] = Field(
        default=["stocks", "etfs"], description="Instrument types: stocks, etfs, funds"
    )
    exclude_penny_stocks: bool = Field(default=True, description="Filter out penny stocks")
    min_liquidity_usd: float = Field(
        default=1000000, ge=0, description="Minimum daily trading volume in USD"
    )

    @field_validator("included", "included_instruments")
    @classmethod
    def validate_lists_not_empty(cls, v: list[str]) -> list[str]:
        """Ensure lists are not empty."""
        if not v:
            raise ValueError("List cannot be empty")
        return v


class IndicatorConfig(BaseModel):
    """Configuration for a single technical indicator."""

    name: str = Field(description="Indicator name (must match pandas-ta function name)")
    params: dict = Field(default_factory=dict, description="Parameters for the indicator")
    enabled: bool = Field(default=True, description="Whether the indicator is enabled")


class TechnicalIndicatorsConfig(BaseModel):
    """Configuration for technical analysis indicators."""

    indicators: list[IndicatorConfig] = Field(
        default_factory=lambda: [
            IndicatorConfig(name="rsi", params={"length": 14}, enabled=True),
            IndicatorConfig(
                name="macd", params={"fast": 12, "slow": 26, "signal": 9}, enabled=True
            ),
            IndicatorConfig(name="bbands", params={"length": 20, "std": 2.0}, enabled=True),
            IndicatorConfig(name="atr", params={"length": 14}, enabled=True),
            IndicatorConfig(name="sma", params={"length": 20}, enabled=True),
            IndicatorConfig(name="sma", params={"length": 50}, enabled=True),
            IndicatorConfig(name="sma", params={"length": 200}, enabled=True),
            IndicatorConfig(name="ema", params={"length": 12}, enabled=False),
            IndicatorConfig(name="ema", params={"length": 26}, enabled=False),
            IndicatorConfig(name="adx", params={"length": 14}, enabled=False),
            IndicatorConfig(name="stoch", params={"k": 14, "d": 3}, enabled=False),
        ],
        description="List of technical indicators to calculate",
    )
    min_periods_required: int = Field(
        default=200,
        ge=14,
        description="Minimum periods of price data required for analysis",
    )
    use_pandas_ta: bool = Field(
        default=True,
        description="Use pandas-ta library for calculations (recommended)",
    )


class AnalysisConfig(BaseModel):
    """Analysis and scoring preferences."""

    weight_fundamental: float = Field(
        default=0.35, ge=0, le=1, description="Weight for fundamental score"
    )
    weight_technical: float = Field(
        default=0.35, ge=0, le=1, description="Weight for technical score"
    )
    weight_sentiment: float = Field(
        default=0.30, ge=0, le=1, description="Weight for sentiment score"
    )
    buy_threshold: float = Field(
        default=70, ge=0, le=100, description="Minimum score for Buy recommendation"
    )
    buy_confidence_threshold: float = Field(
        default=0.60, ge=0, le=1, description="Minimum confidence for Buy"
    )
    hold_lower_threshold: float = Field(
        default=40, ge=0, le=100, description="Lower bound for Hold recommendation"
    )
    hold_upper_threshold: float = Field(
        default=70, ge=0, le=100, description="Upper bound for Hold recommendation"
    )
    time_horizon_months: int = Field(
        default=3, ge=1, le=60, description="Time horizon for predictions in months"
    )
    historical_data_lookback_days: int = Field(
        default=730,
        ge=30,
        le=1825,
        description="Days of historical price data to fetch (30-1825, ~2 years default)",
    )
    technical_indicators: TechnicalIndicatorsConfig = Field(
        default_factory=TechnicalIndicatorsConfig,
        description="Technical analysis indicator configuration",
    )

    @field_validator("weight_sentiment", mode="after")
    @classmethod
    def validate_weights_sum(cls, v: float, info) -> float:
        """Validate that weights sum to approximately 1.0."""
        data = info.data
        if "weight_fundamental" in data and "weight_technical" in data:
            total = data["weight_fundamental"] + data["weight_technical"] + v
            if not (0.99 <= total <= 1.01):
                raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class OutputConfig(BaseModel):
    """Output formatting preferences."""

    max_recommendations: int = Field(
        default=10, ge=1, le=100, description="Maximum number of recommendations"
    )
    report_format: str = Field(
        default="markdown", description="Report format: markdown, html, or json"
    )
    include_confidence_scores: bool = Field(
        default=True, description="Include confidence scores in reports"
    )
    include_risk_assessment: bool = Field(
        default=True, description="Include risk assessment in reports"
    )

    @field_validator("report_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate report format."""
        allowed = {"markdown", "html", "json"}
        if v.lower() not in allowed:
            raise ValueError(f"Report format must be one of {allowed}")
        return v.lower()


class CacheTTLConfig(BaseModel):
    """Cache time-to-live settings."""

    price_data_market_hours: int = Field(
        default=1, ge=1, description="Price data TTL during market hours (hours)"
    )
    price_data_overnight: int = Field(
        default=24, ge=1, description="Price data TTL overnight (hours)"
    )
    news: int = Field(default=4, ge=1, description="News cache TTL (hours)")
    fundamentals: int = Field(default=24, ge=1, description="Fundamentals cache TTL (hours)")
    financial_statements: int = Field(
        default=168, ge=1, description="Financial statements cache TTL (hours)"
    )


class NewsSourceConfig(BaseModel):
    """Configuration for a single news source."""

    name: str = Field(description="Provider name (e.g., 'alpha_vantage', 'finnhub')")
    priority: int = Field(default=1, ge=1, le=10, description="Priority order (lower = higher)")
    enabled: bool = Field(default=True, description="Whether this source is enabled")
    max_articles: int = Field(default=50, ge=1, le=200, description="Max articles from this source")


class NewsConfig(BaseModel):
    """News fetching configuration."""

    max_articles: int = Field(
        default=50, ge=1, le=200, description="Maximum number of articles to fetch per ticker"
    )
    target_article_count: int = Field(
        default=50, ge=1, le=200, description="Target number of articles for analysis"
    )
    max_age_days: int = Field(
        default=30, ge=1, le=352, description="Maximum age of articles in days"
    )
    sources: list[NewsSourceConfig] = Field(
        default_factory=lambda: [
            NewsSourceConfig(name="alpha_vantage", priority=1, max_articles=50),
            NewsSourceConfig(name="finnhub", priority=2, max_articles=50),
        ],
        description="News sources in priority order",
    )
    use_unified_aggregator: bool = Field(
        default=True, description="Use unified news aggregator with deduplication"
    )


class LocalSentimentModelConfig(BaseModel):
    """Configuration for local sentiment model."""

    name: str = Field(default="ProsusAI/finbert", description="Hugging Face model name")
    device: str = Field(default="auto", description="Device: 'auto', 'cpu', 'cuda', 'mps'")
    batch_size: int = Field(default=32, ge=1, le=128, description="Batch size for processing")
    max_length: int = Field(default=512, ge=64, le=1024, description="Maximum token length")


class SentimentConfig(BaseModel):
    """Sentiment analysis configuration."""

    scoring_method: str = Field(
        default="api",
        description="Scoring method: 'local' (FinBERT), 'llm', 'api' (provider-based), 'hybrid'",
    )
    local_model: LocalSentimentModelConfig = Field(
        default_factory=LocalSentimentModelConfig,
        description="Local FinBERT model configuration",
    )
    llm_fallback: bool = Field(
        default=True, description="Use LLM if local model fails or is unavailable"
    )
    use_local_for_theme_extraction: bool = Field(
        default=False,
        description="If True, use local model for scoring but LLM for theme extraction",
    )

    @field_validator("scoring_method")
    @classmethod
    def validate_scoring_method(cls, v: str) -> str:
        """Validate scoring method."""
        allowed = {"local", "llm", "api", "hybrid"}
        if v.lower() not in allowed:
            raise ValueError(f"Scoring method must be one of {allowed}")
        return v.lower()


class DataConfig(BaseModel):
    """Data fetching and caching configuration."""

    cache_ttl: CacheTTLConfig = Field(
        default_factory=CacheTTLConfig, description="Cache expiration times"
    )
    news: NewsConfig = Field(default_factory=NewsConfig, description="News fetching settings")
    sentiment: SentimentConfig = Field(
        default_factory=SentimentConfig, description="Sentiment analysis configuration"
    )
    primary_provider: str = Field(default="yahoo_finance", description="Primary data provider")
    backup_providers: list[str] = Field(
        default=["alpha_vantage", "finnhub"], description="Backup data providers"
    )


class APIConfig(BaseModel):
    """API settings and credentials."""

    max_retries: int = Field(default=3, ge=1, description="Maximum retry attempts")
    retry_backoff_factor: float = Field(
        default=2.0, ge=1.0, description="Exponential backoff factor"
    )
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(
        default="INFO",
        description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    format: str = Field(default="json", description="Log format: json or text")
    log_file: str = Field(default="logs/nordinvest.log", description="Log file path")
    max_log_size_mb: int = Field(default=10, ge=1, description="Maximum log file size in MB")
    backup_count: int = Field(default=5, ge=1, description="Number of backup log files to keep")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()


class LLMConfig(BaseModel):
    """LLM provider and model configuration."""

    provider: str = Field(
        default="anthropic",
        description="LLM provider: anthropic, openai, or local",
    )
    model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model identifier (e.g., claude-sonnet-4-20250514, gpt-4, etc.)",
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Temperature for generation (0.0-2.0)"
    )
    max_tokens: int = Field(
        default=2000, ge=100, le=8000, description="Maximum tokens per response"
    )
    top_p: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Top-p (nucleus) sampling parameter"
    )
    timeout_seconds: int = Field(
        default=60, ge=10, le=300, description="Request timeout in seconds"
    )
    enable_fallback: bool = Field(
        default=True, description="Fall back to rule-based analysis on LLM failure"
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        allowed = {"anthropic", "openai", "local"}
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v.lower()


class TokenTrackerConfig(BaseModel):
    """Token usage tracking and cost monitoring configuration."""

    enabled: bool = Field(default=True, description="Enable token tracking")
    daily_limit: int = Field(default=100000, ge=1000, description="Daily token usage limit")
    monthly_limit: int = Field(default=1000000, ge=10000, description="Monthly token usage limit")
    cost_per_1k_input_tokens: float = Field(
        default=0.003, ge=0.0, description="Cost per 1k input tokens in EUR"
    )
    cost_per_1k_output_tokens: float = Field(
        default=0.015, ge=0.0, description="Cost per 1k output tokens in EUR"
    )
    warn_on_daily_usage_percent: float = Field(
        default=0.8, ge=0.1, le=1.0, description="Warn when daily usage reaches X%"
    )


class DeploymentConfig(BaseModel):
    """Deployment and scheduling settings."""

    run_time: str = Field(default="08:00", description="Daily run time in UTC (HH:MM format)")
    timezone: str = Field(default="Europe/Stockholm", description="Timezone for scheduling")
    cost_limit_eur_per_month: float = Field(
        default=100, gt=0, description="Monthly cost limit in EUR"
    )
    cost_check_interval: str = Field(
        default="daily", description="Cost check frequency: daily or weekly"
    )


class TestModeConfig(BaseModel):
    """Test mode configuration for zero-cost testing."""

    enabled: bool = Field(default=False, description="Enable test mode (fixtures instead of APIs)")
    fixture_name: str = Field(
        default="test_ticker_minimal", description="Name of fixture to use (in data/fixtures/)"
    )
    fixture_path: str | None = Field(default=None, description="Full path to fixture directory")
    use_mock_llm: bool = Field(
        default=True, description="Use MockLLMClient instead of real LLM (zero cost)"
    )
    validate_expected: bool = Field(
        default=True, description="Validate that results match expected ranges from fixture"
    )


class DatabaseConfig(BaseModel):
    """Database configuration for historical data storage."""

    enabled: bool = Field(default=True, description="Enable database storage of historical data")
    db_path: str = Field(default="data/nordinvest.db", description="Path to SQLite database file")
    auto_persist_analyst_ratings: bool = Field(
        default=True, description="Automatically store analyst ratings when fetched from APIs"
    )
    check_db_first: bool = Field(
        default=True, description="Check database first before calling APIs for historical dates"
    )
    auto_cleanup_old_data: bool = Field(
        default=False, description="Automatically delete analyst ratings older than retention_days"
    )
    retention_days: int = Field(
        default=730, ge=30, description="Keep analyst ratings for this many days (default: 2 years)"
    )


class FilterStrategyConfig(BaseModel):
    """Configuration for individual filtering strategies."""

    daily_change_threshold: float = Field(
        default=5.0, ge=0.1, description="Daily price change % threshold (anomaly strategy)"
    )
    weekly_change_threshold: float = Field(
        default=15.0, ge=0.1, description="Weekly price change % threshold (anomaly strategy)"
    )
    volume_spike_multiplier: float = Field(
        default=1.5, ge=1.0, description="Volume spike multiplier (anomaly strategy)"
    )
    lookback_days_high_low: int = Field(
        default=30, ge=5, description="Days to check for price highs/lows (anomaly strategy)"
    )
    min_volume_ratio: float = Field(
        default=1.2, ge=1.0, description="Minimum volume ratio vs average (volume strategy)"
    )
    volume_trend_days: int = Field(
        default=10, ge=5, description="Days to calculate volume trend (volume strategy)"
    )
    min_trend_slope: float = Field(
        default=10.0, ge=0.0, description="Minimum trend slope % to trigger (volume strategy)"
    )


class FilteringConfig(BaseModel):
    """Filtering configuration for ticker pre-selection."""

    default_strategy: str = Field(
        default="anomaly",
        description="Default filtering strategy: anomaly, volume, or all",
    )
    strategies: dict[str, FilterStrategyConfig] = Field(
        default_factory=lambda: {
            "anomaly": FilterStrategyConfig(),
            "volume": FilterStrategyConfig(),
        },
        description="Strategy-specific configuration",
    )

    @field_validator("default_strategy")
    @classmethod
    def validate_default_strategy(cls, v: str) -> str:
        """Validate default strategy is one of allowed values."""
        allowed = {"anomaly", "volume", "all"}
        if v.lower() not in allowed:
            raise ValueError(f"Default filtering strategy must be one of {allowed}")
        return v.lower()


class Config(BaseModel):
    """Root configuration schema."""

    capital: CapitalConfig = Field(default_factory=CapitalConfig, description="Capital settings")
    risk: RiskConfig = Field(default_factory=RiskConfig, description="Risk tolerance settings")
    markets: MarketsConfig = Field(default_factory=MarketsConfig, description="Market preferences")
    analysis: AnalysisConfig = Field(
        default_factory=AnalysisConfig, description="Analysis preferences"
    )
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output settings")
    data: DataConfig = Field(default_factory=DataConfig, description="Data and caching settings")
    api: APIConfig = Field(default_factory=APIConfig, description="API settings")
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )
    llm: LLMConfig = Field(
        default_factory=LLMConfig, description="LLM provider and model configuration"
    )
    token_tracker: TokenTrackerConfig = Field(
        default_factory=TokenTrackerConfig, description="Token tracking and cost monitoring"
    )
    deployment: DeploymentConfig = Field(
        default_factory=DeploymentConfig, description="Deployment settings"
    )
    test_mode: TestModeConfig = Field(
        default_factory=TestModeConfig, description="Test mode configuration"
    )
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig, description="Database configuration"
    )
    filtering: FilteringConfig = Field(
        default_factory=FilteringConfig,
        description="Filtering configuration for ticker pre-selection",
    )
