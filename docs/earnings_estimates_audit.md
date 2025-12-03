# Earnings Estimates Look-Ahead Bias Audit

## Executive Summary

**CRITICAL ISSUE FOUND**: The `get_earnings_estimates()` method in `AlphaVantageProvider` is vulnerable to look-ahead bias in historical analysis. The method only fetches CURRENT/LATEST earnings estimates, which are forward-looking data that would not have been available during historical backtesting.

**Severity**: HIGH - This can significantly skew fundamental analysis during backtesting.

---

## The Problem

### Current Implementation Issues

**Location**: `src/data/alpha_vantage.py:470-532`

The `get_earnings_estimates()` method:
1. **Takes only `ticker` parameter** - No `as_of_date` parameter
2. **Fetches latest estimates only** - Returns current earnings estimates for upcoming quarters/years
3. **No date filtering** - Cannot restrict to estimates that existed on a specific historical date
4. **Inherently forward-looking** - Estimates predict earnings for future quarters

### Example of Look-Ahead Bias

**Scenario**: Backtesting on June 1, 2024

```python
# What happens with current code:
estimates = provider.get_earnings_estimates("AAPL")
# Returns (TODAY's estimates for):
# - Q3 2024 (ends Sept 30) - FUTURE relative to June 1
# - FY2024 (ends Dec 31) - FUTURE relative to June 1

# What SHOULD happen:
estimates = provider.get_earnings_estimates("AAPL", as_of_date=datetime(2024, 6, 1))
# Should return estimates that existed on June 1, 2024
# These estimates might have different values and might be for different quarters
```

### Why This Is Different from Other Data Types

| Data Type | Characteristic | Solution |
|-----------|-----------------|----------|
| **Price Data** | Historical fact | Filter by date of data point |
| **News Articles** | Published on specific date | Filter by publish date |
| **Fundamentals** | Report date is historical fact | Filter by report date |
| **Analyst Ratings** | Rating issued on specific date | Filter by rating date |
| **Earnings Estimates** | Forward-looking, revised constantly | Need estimate snapshot from that date |

**Key difference**: Earnings estimates don't have a "publish date" in the API - they represent the CURRENT consensus view, which changes daily.

---

## API Analysis

### Alpha Vantage EARNINGS_ESTIMATES Endpoint

**Current API Call**:
```python
data = self._api_call({
    "function": "EARNINGS_ESTIMATES",
    "symbol": ticker
})
```

**API Parameters** (from documentation):
- `function`: Required ("EARNINGS_ESTIMATES")
- `symbol`: Required (ticker)
- `interval`: Optional (for time series data)
- **Missing**: No `from_date` or `as_of_date` parameter

**Limitation**: The API does NOT support fetching historical estimate snapshots from specific dates. It only returns the current latest estimates.

---

## Technical Implications

### What We Cannot Do
1. **Real-time historical snapshots** - Cannot fetch what analysts estimated on June 1, 2024
2. **Revision tracking** - Cannot track how estimates changed over time
3. **Historical context filtering** - Cannot properly answer "what did we know on this date?"

### What We Can Do
1. **Cache-based approach** - Store estimate snapshots with analysis dates
2. **Conditional usage** - Use estimates only for current analysis, disable for historical
3. **Data labeling** - Mark estimates as "snapshot date" when cached
4. **Graceful degradation** - Return None for historical estimates, warn users

---

## Proposed Solution: Cache-Based Historical Snapshots

### Implementation Strategy

**Step 1**: Add `as_of_date` parameter to interface

```python
def get_earnings_estimates(
    self,
    ticker: str,
    as_of_date: datetime | None = None
) -> Optional[dict]:
    """Fetch earnings estimates.

    For historical analysis (as_of_date in past):
    - Attempts to retrieve cached estimate snapshot from that date
    - Falls back to empty dict with warning
    - Uses cache_key with date: "earnings_estimates:<ticker>:<as_of_date>"

    For current analysis (as_of_date=None):
    - Fetches latest estimates from API
    - Caches with current timestamp

    Args:
        ticker: Stock ticker
        as_of_date: Historical date for snapshot (None = current)
    """
```

**Step 2**: Implement cache-based retrieval for historical dates

```python
# For historical requests (as_of_date is in the past):
if as_of_date and as_of_date.date() < datetime.now().date():
    # Try to retrieve from cache using historical date
    cache_key = f"earnings_estimates:{ticker}:{as_of_date.date()}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    # No cached snapshot available - cannot create synthetic historical data
    logger.warning(
        f"No earnings estimate snapshot in cache for {ticker} on {as_of_date.date()}. "
        f"Estimates are forward-looking and require caching on analysis date."
    )
    return None  # Return None rather than future data
```

**Step 3**: Add HistoricalContext field

```python
class HistoricalContext(BaseModel):
    # ... existing fields ...
    earnings_estimates: Optional[dict] = Field(
        default=None,
        description="Earnings estimate snapshot (None if not in cache for historical date)"
    )
    earnings_estimates_warning: str | None = Field(
        default=None,
        description="Warning about earnings estimate availability/accuracy"
    )
```

**Step 4**: Update HistoricalDataFetcher

```python
def fetch_as_of_date(self, ticker: str, as_of_date, lookback_days: int = 365):
    # ... existing price, fundamentals, news fetching ...

    # Fetch earnings estimates (if available in cache for this date)
    try:
        if hasattr(self.provider, 'get_earnings_estimates'):
            estimates = self.provider.get_earnings_estimates(ticker, as_of_date=as_of_datetime)
            if estimates:
                context.earnings_estimates = estimates
            else:
                context.earnings_estimates_warning = (
                    "Earnings estimates not available in historical cache. "
                    "Estimates are forward-looking and require snapshot caching."
                )
    except Exception as e:
        logger.warning(f"Error fetching earnings estimates: {e}")
        context.earnings_estimates_warning = f"Fetch error: {str(e)}"
```

---

## Trade-offs and Limitations

### This Approach
- ✅ Prevents look-ahead bias by refusing future data
- ✅ Gracefully degrades when snapshots unavailable
- ✅ Can accumulate historical snapshots over time
- ❌ Requires explicit caching during current analysis
- ❌ Cannot retroactively create historical snapshots
- ❌ Limits usefulness of earnings estimates in backtesting

### Alternative Approaches

**Option A: Disable for Historical**
- Simply return None for all historical estimate requests
- **Pros**: Simple, eliminates look-ahead bias entirely
- **Cons**: Cannot use earnings data in historical analysis at all

**Option B: Real-time Simulation**
- Would require external database of historical estimate snapshots (not feasible)
- **Pros**: Complete historical accuracy
- **Cons**: Requires expensive third-party data, out of scope

**Option C: Fiscal Date Filtering**
- Only include estimates for quarters that have already ended
- **Example**: On June 1, 2024, only include estimates for Q1 2024 (already ended)
- **Pros**: Prevents some future data
- **Cons**: Still uses current latest estimates, different from what was actually known on the date

---

## Implementation Priority

### Phase 1: Safety (Immediate)
1. Add `as_of_date` parameter to `get_earnings_estimates()`
2. Return None/warning for historical dates (unless cached)
3. Add earnings_estimates to HistoricalContext
4. Update HistoricalDataFetcher

### Phase 2: Enhancement (Future)
1. Implement cache storage for estimate snapshots
2. Accumulate historical snapshots over time
3. Improve cache retrieval logic

### Phase 3: Analysis Improvement (Future)
1. Consider fiscal date filtering for estimates
2. Add estimate revision tracking if data becomes available
3. Document limitations in reports

---

## Testing Strategy

```python
def test_earnings_estimates_historical_safety():
    """Verify earnings estimates return None for historical dates without cache."""

def test_earnings_estimates_current_analysis():
    """Verify earnings estimates work normally for current analysis."""

def test_earnings_estimates_cache_retrieval():
    """Verify cached snapshots are retrieved for historical dates."""

def test_historical_context_earnings_estimates_field():
    """Verify HistoricalContext properly handles earnings_estimates."""
```

---

## Code Changes Required

### Files to Modify
1. `src/data/alpha_vantage.py` - Add `as_of_date` parameter
2. `src/data/models.py` - Add fields to HistoricalContext
3. `src/data/historical.py` - Fetch earnings estimates with date
4. `src/data/providers.py` - Update base class if needed (optional)
5. `tests/unit/data/test_historical.py` - Add earnings estimates tests

### Backward Compatibility
- ✅ Making `as_of_date` optional maintains existing API
- ✅ Only affects historical analysis code path
- ✅ Current analysis unaffected (as_of_date=None)

---

## Documentation Updates

- Add section to `docs/historical_analysis.md` about earnings estimates limitations
- Document cache requirements for historical accuracy
- Add troubleshooting section for "missing earnings estimates in backtest"

---

## Risk Assessment

| Risk | Probability | Severity | Mitigation |
|------|-------------|----------|-----------|
| Using future estimates in backtest | HIGH | HIGH | This fix prevents it |
| Cache misses in historical analysis | MEDIUM | MEDIUM | Return None + warning |
| Confusion about estimate staleness | MEDIUM | MEDIUM | Document clearly |
| Performance impact from cache checks | LOW | LOW | Minimal additional overhead |

---

## Conclusion

The `get_earnings_estimates()` method has a **critical look-ahead bias vulnerability**. Forward-looking earnings estimates cannot be properly contextualized to a historical date without explicit caching of snapshots. The proposed cache-based solution with graceful degradation prevents future data leakage while acknowledging API limitations.
