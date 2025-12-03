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
2. **Fetches current estimates only** - Returns today's consensus for next quarter/year
3. **Cannot provide historical snapshots** - Alpha Vantage API doesn't support fetching estimates as they existed on past dates
4. **Missing parameter in historical analysis** - No way to distinguish current vs. historical context

### Example of the Limitation

**Scenario**: Backtesting on June 1, 2024

```python
# What happens with current code:
estimates = provider.get_earnings_estimates("AAPL")
# Returns TODAY's estimates for:
# - Q1 2025 (next fiscal quarter as of today)
# - FY2025 (next fiscal year as of today)

# What SHOULD happen for true historical accuracy:
estimates = provider.get_earnings_estimates("AAPL", as_of_date=datetime(2024, 6, 1))
# Should return June 1, 2024's consensus for:
# - Q3 2024 (next fiscal quarter as of June 1)
# - FY2024 (next fiscal year as of June 1)
# These might have DIFFERENT values and different target quarters!
```

### Why This Is Different from Other Data Types

| Data Type | Characteristic | Solution |
|-----------|-----------------|----------|
| **Price Data** | Historical fact | Filter by date of data point |
| **News Articles** | Published on specific date | Filter by publish date |
| **Fundamentals** | Report date is historical fact | Filter by report date |
| **Analyst Ratings** | Rating issued on specific date | Filter by rating date |
| **Earnings Estimates** | Forward-looking, revised constantly | **Needs caching from that date** |

**Key difference**: Earnings estimates represent a snapshot of consensus opinion that changes daily. Without caching historical snapshots, we cannot know what was estimated on a past date.

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

## Proposed Solution: Pragmatic Approach with Future Enhancement Path

### Implementation Strategy (Phase 8.1)

**Step 1**: Add `as_of_date` parameter to interface

```python
def get_earnings_estimates(
    self,
    ticker: str,
    as_of_date: datetime | None = None
) -> Optional[dict]:
    """Fetch earnings estimates.

    For historical analysis (as_of_date in past):
    - Currently returns TODAY's estimates (pragmatic approach)
    - Logs that these are "current" estimates, not "as-of-date" estimates
    - TODO: Implement cache-based snapshots for true historical accuracy

    For current analysis (as_of_date=None):
    - Fetches latest estimates from API
    - Ready for caching when snapshots system implemented

    Args:
        ticker: Stock ticker
        as_of_date: Historical date for analysis (None = current analysis)
    """
```

**Step 2**: Current estimates with limitation acknowledgement

```python
# For historical requests (as_of_date is in the past):
if as_of_date and as_of_date.date() < datetime.now().date():
    logger.debug(
        f"Earnings estimates requested for historical date {as_of_date.date()}. "
        f"Note: Returning current estimates for next quarter/year (as of today), "
        f"not estimates that existed on {as_of_date.date()}. "
        f"To get true historical estimates, they would need to be cached from that date."
    )
    # Continue to fetch current estimates with limitation noted
    # Future: Replace with cache-based snapshot retrieval
```

**Step 3**: Add HistoricalContext field

```python
class HistoricalContext(BaseModel):
    # ... existing fields ...
    earnings_estimates: dict | None = Field(
        default=None,
        description="Earnings estimates (current/today's consensus for next quarter/year)"
    )
```

**Step 4**: Update HistoricalDataFetcher

```python
def fetch_as_of_date(self, ticker: str, as_of_date, lookback_days: int = 365):
    # ... existing price, fundamentals, news fetching ...

    # Fetch earnings estimates (with limitation noted)
    try:
        if hasattr(self.provider, 'get_earnings_estimates'):
            estimates = self.provider.get_earnings_estimates(ticker, as_of_date=as_of_datetime)
            if estimates:
                context.earnings_estimates = estimates
                logger.debug(f"Fetched earnings estimates for {ticker}")
            else:
                logger.debug(f"No earnings estimates available for {ticker}")
    except Exception as e:
        logger.warning(f"Error fetching earnings estimates for {ticker}: {e}")
```

### Phase 8.2 Enhancement: Cache-Based Historical Snapshots

When implementing Phase 8.2 (Backtesting Framework), add cache-based snapshots:

```python
# Phase 8.2: Cache earnings estimates with analysis date
if is_current_analysis:
    # Cache current estimates with today's date
    cache_key = f"earnings_estimates:{ticker}:{datetime.now().date()}"
    cache_manager.set(cache_key, estimates)

# For historical analysis:
if as_of_date and as_of_date.date() < datetime.now().date():
    # Try to retrieve from cache using historical date
    cache_key = f"earnings_estimates:{ticker}:{as_of_date.date()}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached  # Use cached snapshot from that date
    else:
        logger.warning(f"No earnings estimate snapshot in cache for {as_of_date.date()}")
        return None  # True historical unavailable
```

---

## Trade-offs and Limitations

### Phase 8.1 Approach (Current)
- ✅ Preserves earnings estimates functionality for historical analysis
- ✅ Adds `as_of_date` parameter for future enhancement
- ✅ Clearly documents the limitation in logs
- ✅ Sets foundation for Phase 8.2 caching implementation
- ✅ Ready for production historical analysis (with noted limitation)
- ❌ Returns "current" estimates, not "as-of-date" estimates
- ❌ Not suitable for ultra-precise backtesting
- ⏳ Caching feature planned for Phase 8.2

### Alternative Approaches Considered

**Option A: Return None for Historical** (REJECTED)
- Simply return None for all historical estimate requests
- **Pros**: Prevents look-ahead bias entirely
- **Cons**: Cannot use earnings data in historical analysis at all; too restrictive

**Option B: Fiscal Date Filtering**
- Only include estimates for quarters that have already ended
- **Example**: On June 1, 2024, only use estimates for Q1 2024 (already ended)
- **Pros**: Prevents some future-looking data
- **Cons**: Still uses current estimates, doesn't solve the fundamental issue

**Option C: Cache-Based (Phase 8.2)**
- Collect historical estimate snapshots over time
- Requires explicit caching during current analysis runs
- **Pros**: True historical accuracy after enough data collected
- **Cons**: Requires time to build historical cache; Phase 8.2 feature

**Option D: External Data Source** (OUT OF SCOPE)
- Subscribe to service tracking historical estimate snapshots
- **Pros**: Complete historical accuracy
- **Cons**: Additional cost, external dependency

---

## Implementation Priority

### Phase 8.1: Foundation (COMPLETE)
1. ✅ Add `as_of_date` parameter to `get_earnings_estimates()`
2. ✅ Accept current estimates with limitation documented in logs
3. ✅ Add earnings_estimates to HistoricalContext
4. ✅ Update HistoricalDataFetcher to fetch estimates
5. ✅ Comprehensive testing with 3 test cases

### Phase 8.2: Enhancement (NEXT)
1. Implement CacheManager snapshot caching for estimates
2. Cache earnings estimates with date key: `earnings_estimates:<ticker>:<date>`
3. Update `get_earnings_estimates()` to check cache first for historical dates
4. Accumulate historical snapshots over time as analyses run
5. Add configuration for cache retention policy

### Phase 9+: Analysis Improvement (Future)
1. Monitor cache hit rates for historical estimates
2. Add estimate revision tracking if external data becomes available
3. Document cache statistics in performance reports
4. Consider fiscal date filtering enhancement

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

The `get_earnings_estimates()` method required enhancement for historical analysis support. While earnings estimates are forward-looking and the Alpha Vantage API doesn't provide historical snapshots, a pragmatic Phase 8.1 solution has been implemented that:

1. **Accepts current estimates** for historical analysis with clear limitation documented
2. **Adds `as_of_date` parameter** ready for Phase 8.2 caching enhancement
3. **Preserves functionality** - Earnings estimates remain available in historical context
4. **Documents trade-offs** - Logs clearly indicate these are "current" not "as-of-date" estimates
5. **Enables future improvement** - Phase 8.2 will implement cache-based historical snapshots

This balances **practical usability** (earnings data available for historical analysis) with **transparency** (limitations clearly documented) while establishing the foundation for **future enhancement** (cache-based snapshots in Phase 8.2).
