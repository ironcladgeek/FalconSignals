# Backtesting Framework Proposal

## Context

FalconSignals generates investment **recommendations** (buy/hold/sell), not algorithmic trading strategies. Users review these recommendations and make their own trading decisions.

**Backtesting goal**: Validate recommendation quality through historical analysis, not simulate portfolio returns.

## What We Already Have

✅ **Historical Analysis**
- `analyze --date 2024-06-01` generates recommendations using historical data
- Prevents look-ahead bias (uses only data available on that date)
- Works in both LLM and rule-based modes

✅ **Performance Tracking**
- `track-performance` fetches current prices for active recommendations
- Stores daily price snapshots in `price_tracking` table
- Calculates price changes, benchmark comparison

✅ **Performance Metrics**
- `performance-report` shows win rate, avg return, alpha, Sharpe ratio
- Confidence calibration analysis
- Filters by ticker, signal type, analysis mode

## What's Missing

### 1. Backtesting Orchestration

**Problem**: Manual iteration through dates is tedious and error-prone

```bash
# Currently need to run manually for each date
uv run python -m src.main analyze --ticker AAPL --date 2024-01-01
uv run python -m src.main analyze --ticker AAPL --date 2024-02-01
uv run python -m src.main analyze --ticker AAPL --date 2024-03-01
# ...repeat 50+ times
```

**Solution**: Create `backtest` command that automates date range iteration

```bash
# Proposed command
uv run python -m src.main backtest \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --frequency weekly \
  --ticker AAPL,MSFT \
  --mode rule_based
```

**Implementation**:
- `BacktestEngine` class in `src/backtesting/engine.py`
- Iterates through date range (daily/weekly/monthly)
- Calls existing `analyze` logic for each date
- Stores results in database (reuses existing tables)
- Handles failures gracefully (continue on error)

### 2. LLM Cost Estimation

**Problem**: Backtesting in LLM mode can be expensive (€0.50-0.80 per ticker)

**Solution**: Pre-calculate and display cost estimates before execution

```bash
uv run python -m src.main backtest \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --frequency weekly \
  --ticker AAPL,MSFT,GOOGL \
  --mode llm \
  --dry-run

# Output:
# 📊 Backtest Plan:
#   Date range: 2024-01-01 to 2024-12-31
#   Frequency: weekly (52 dates)
#   Tickers: 3
#   Total analyses: 156
#   Estimated cost (LLM): €78-125
#   Estimated duration: ~2 hours
#
# Continue? [y/N]
```

### 3. Backtest-Specific Reports

**Problem**: Current `performance-report` shows aggregated metrics, not backtest-specific insights

**Solution**: Enhanced backtest report with:

```markdown
# Backtest Report: 2024-01-01 to 2024-12-31

## Configuration
- Frequency: weekly (52 analysis dates)
- Tickers: AAPL, MSFT, GOOGL
- Mode: rule_based
- Total signals: 156 (72 buy, 54 hold, 30 sell)

## Performance by Signal Type
| Signal      | Count | Win Rate | Avg Return (30d) | Alpha vs SPY |
|-------------|-------|----------|------------------|--------------|
| strong_buy  | 12    | 75.0%    | +8.2%            | +3.1%        |
| buy         | 60    | 63.3%    | +4.5%            | +1.2%        |
| hold        | 54    | 51.9%    | +1.8%            | -0.5%        |
| sell        | 30    | 43.3%    | -2.1%            | -4.3%        |

## Confidence Calibration
| Confidence Range | Count | Actual Win Rate | Calibration Error |
|------------------|-------|-----------------|-------------------|
| 80-100%          | 23    | 78.3%           | -3.7%             |
| 60-80%           | 89    | 61.8%           | -8.2%             |
| 40-60%           | 44    | 52.3%           | +2.3%             |

## Mode Comparison (if both modes tested)
| Metric          | Rule-Based | LLM Mode | Winner     |
|-----------------|------------|----------|------------|
| Win Rate        | 58.2%      | 64.7%    | LLM (+6.5%)|
| Avg Return      | +3.1%      | +4.8%    | LLM (+1.7%)|
| Sharpe Ratio    | 0.82       | 1.05     | LLM        |
| Cost            | €0         | €95      | Rule-Based |

## Recommendations
- Strong buy signals show excellent performance (75% win rate)
- Confidence scores slightly underestimate (avg error: -3.2%)
- LLM mode provides better returns but at significant cost
- Consider LLM mode for high-conviction plays only
```

### 4. Configuration Management

**Problem**: No centralized backtest configuration

**Solution**: Add to `config/default.yaml`:

```yaml
backtesting:
  # Default backtest parameters
  default_frequency: "weekly"  # daily, weekly, monthly
  default_period_days: 90  # Track outcomes for X days after signal
  max_concurrent_analyses: 5  # Parallel execution limit

  # Cost controls
  llm_cost_limit_per_backtest: 100.0  # EUR
  require_confirmation: true  # Ask before running expensive backtests

  # Benchmarks
  default_benchmark: "SPY"
  alternative_benchmarks:
    - "QQQ"  # Tech-heavy
    - "IWM"  # Small-cap

  # Reporting
  report_formats:
    - markdown
    - json
    - csv  # For Excel analysis
  include_visualizations: true  # Generate charts
```

## Implementation Plan

### Phase 1: Core Backtesting Engine (Priority: High)

**Files to create**:
- `src/backtesting/engine.py` - BacktestEngine class
- `src/backtesting/config.py` - Backtest configuration schemas
- `src/cli/commands/backtest.py` - CLI command

**Implementation**:
```python
class BacktestEngine:
    """Orchestrates historical analysis across date ranges."""

    def __init__(self, config, provider_manager, repository):
        self.config = config
        self.provider_manager = provider_manager
        self.repository = repository

    def run(
        self,
        start_date: date,
        end_date: date,
        tickers: list[str],
        frequency: str = "weekly",
        analysis_mode: str = "rule_based",
        dry_run: bool = False
    ) -> BacktestResult:
        """Run backtest across date range."""

        # 1. Generate analysis dates
        dates = self._generate_dates(start_date, end_date, frequency)

        # 2. Estimate cost (for LLM mode)
        if analysis_mode == "llm" and not dry_run:
            cost_estimate = self._estimate_cost(len(dates), len(tickers))
            if not self._confirm_cost(cost_estimate):
                return None

        # 3. Run analyses (reuse existing analyze logic)
        results = []
        for analysis_date in dates:
            for ticker in tickers:
                result = self._run_analysis(ticker, analysis_date, analysis_mode)
                results.append(result)

        # 4. Return summary
        return BacktestResult(
            dates=dates,
            tickers=tickers,
            recommendations=results,
            total_cost=self._calculate_actual_cost(results)
        )

    def _run_analysis(self, ticker: str, analysis_date: date, mode: str):
        """Run analysis for single ticker/date (reuses existing code)."""
        # Call existing analyze logic from pipeline.py
        # This ensures consistency with regular analysis
        pass
```

**CLI Command**:
```bash
uv run python -m src.main backtest \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --frequency weekly \
  --ticker AAPL,MSFT \
  --mode rule_based \
  --dry-run  # Show plan without executing
```

### Phase 2: Enhanced Reporting (Priority: Medium)

**Files to create/modify**:
- `src/backtesting/report.py` - Backtest-specific report generation
- Extend `src/data/repository.py` with backtest queries

**Features**:
- Signal type comparison tables
- Confidence calibration analysis
- Mode comparison (LLM vs rule-based)
- Time-series performance charts
- CSV export for custom analysis

### Phase 3: Visualization & Analysis (Priority: Low)

**Optional enhancements**:
- Consider `quantstats` for enhanced visualizations
- Generate performance charts (cumulative returns, drawdown)
- Interactive HTML reports
- Confidence calibration plots

**Libraries to evaluate** (only if adding value):
- `quantstats` - For tearsheet-style reports
- `plotly` - For interactive charts
- `seaborn` - For statistical visualizations

**NOT needed**:
- Full backtesting frameworks (backtrader, zipline, bt, vectorbt)
- These are for algorithmic trading, not recommendation validation

## Benefits

1. **Validate effectiveness**: See how well recommendations would have performed historically
2. **Compare modes**: Determine when LLM mode is worth the cost
3. **Calibrate confidence**: Improve confidence score accuracy
4. **Build trust**: Data-driven evidence of system quality
5. **Optimize settings**: Find best configuration for your needs

## Success Metrics

- Run full-year backtest in < 30 minutes (rule-based mode)
- Accurate cost estimation (within 10% of actual)
- Clear visualization of signal quality over time
- Easy comparison of LLM vs rule-based modes
- Export capabilities for custom analysis

## Non-Goals

❌ Portfolio simulation (capital allocation, rebalancing)
❌ Order execution modeling (slippage, commissions)
❌ Multi-asset portfolio optimization
❌ Real-time trading strategy backtesting

## Open Questions

1. **Date frequency**: Should we default to weekly, or make daily an option?
   - Daily: More data points, but slow and expensive in LLM mode
   - Weekly: Good balance between coverage and cost
   - Monthly: Fast, but may miss short-term opportunities

2. **Parallel execution**: Should we run analyses in parallel?
   - Pros: Much faster (5x speedup possible)
   - Cons: More complex error handling, API rate limits

3. **Incremental backtesting**: Support resuming failed backtests?
   - Use case: LLM backtest fails at date 30/52
   - Solution: Store progress, allow `--resume` flag

4. **Visualization**: Which charts are most useful?
   - Cumulative returns by signal type?
   - Confidence calibration curves?
   - Mode comparison over time?

## Recommended Next Steps

1. **Clarify requirements**: Answer open questions above
2. **Design CLI interface**: Finalize command structure and options
3. **Implement Phase 1**: Core BacktestEngine
4. **Test with small backtest**: 1 ticker, 1 month, both modes
5. **Iterate on reports**: Add visualizations based on user feedback
6. **Document usage**: Add to CLI_GUIDE.md

## Example Workflows

### Workflow 1: Validate System Before Using

```bash
# Run 3-month backtest on diverse tickers (rule-based)
uv run python -m src.main backtest \
  --start-date 2024-09-01 \
  --end-date 2024-12-01 \
  --frequency weekly \
  --ticker AAPL,MSFT,NVDA,JPM,XOM \
  --mode rule_based

# Review results
uv run python -m src.main backtest-report --session-id 1

# If results look good, try LLM mode on subset
uv run python -m src.main backtest \
  --start-date 2024-11-01 \
  --end-date 2024-12-01 \
  --frequency weekly \
  --ticker NVDA \
  --mode llm

# Compare modes
uv run python -m src.main backtest-compare --session-id 1,2
```

### Workflow 2: Optimize Confidence Calibration

```bash
# Run full-year backtest
uv run python -m src.main backtest \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --frequency monthly \
  --group us_tech_software \
  --mode rule_based

# Analyze calibration
uv run python -m src.main backtest-report \
  --session-id 3 \
  --focus calibration

# Output shows:
# - 80%+ confidence signals only 65% accurate → overconfident
# - Adjust confidence calculation in signal_creator.py
```

### Workflow 3: Evaluate LLM ROI

```bash
# Run both modes on same data
uv run python -m src.main backtest \
  --start-date 2024-06-01 \
  --end-date 2024-12-01 \
  --frequency weekly \
  --ticker AAPL,MSFT,GOOGL,AMZN,META \
  --mode rule_based

uv run python -m src.main backtest \
  --start-date 2024-06-01 \
  --end-date 2024-12-01 \
  --frequency weekly \
  --ticker AAPL,MSFT,GOOGL,AMZN,META \
  --mode llm

# Compare cost vs performance
uv run python -m src.main backtest-compare \
  --session-id 4,5 \
  --format markdown \
  --save reports/llm_roi_analysis.md

# Decision: If LLM only adds 2% return but costs €80,
# use rule-based for daily scans, LLM for final validation
```
