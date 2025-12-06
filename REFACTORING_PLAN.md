# Refactoring Plan: Unifying LLM and Rule-Based Analysis Modes

**Date**: December 6, 2025
**Objective**: Refactor the codebase to use a single source of truth for both LLM and rule-based analysis modes, following DRY principles.

---

## Current Architecture Issues

### 1. Duplicate Execution Paths

**LLM Mode Flow**:
```
src/main.py::_run_llm_analysis()
  → LLMAnalysisOrchestrator (src/llm/integration.py)
    → HybridAnalysisCrew (src/agents/hybrid.py)
      → CrewAI Agents (src/agents/crewai_agents.py)
        → Synthesis Task
          → _create_signal_from_llm_result() (src/main.py:287)
```

**Rule-Based Mode Flow**:
```
src/main.py::analyze()
  → AnalysisPipeline (src/pipeline.py)
    → Rule-Based Agents (src/agents/analysis.py, sentiment.py)
      → SignalSynthesisAgent
        → _create_investment_signal() (src/pipeline.py:313)
```

**Problem**: Two completely separate execution paths with duplicated logic.

### 2. Different Data Structures

**LLM Synthesis Output** (flat JSON from CrewAI):
```json
{
  "ticker": "AAPL",
  "scores": {"technical": 75, "fundamental": 80, "sentiment": 70},
  "final_score": 75,
  "recommendation": "buy",
  "confidence": 65,
  "risk": {...}
  // NO detailed technical indicators
  // NO detailed fundamental metrics
  // NO detailed analyst info
  // NO detailed sentiment breakdown
}
```

**Rule-Based Analysis Output** (nested structure):
```json
{
  "ticker": "AAPL",
  "final_score": 75,
  "analysis": {
    "technical": {
      "technical_score": 75,
      "indicators": {
        "rsi": 58.5,
        "macd": 2.3,
        "sma_20": 170.5,
        "sma_50": 165.2,
        // ... detailed metrics
      },
      "components": {...}
    },
    "fundamental": {
      "fundamental_score": 80,
      "metrics": {
        "pe_ratio": 28.5,
        "pb_ratio": 45.2,
        // ... detailed metrics
      }
    },
    "sentiment": {
      "sentiment_score": 70,
      "news_count": 15,
      "sentiment_score_value": 0.6,
      // ... detailed metrics
    }
  }
}
```

**Problem**: Metadata extractor expects nested structure, but LLM synthesis only provides flat JSON.

### 3. Duplicate Signal Creation Functions

- **`_create_signal_from_llm_result()`** (src/main.py:287-463)
  - Parses LLM JSON output
  - Fetches price from cache/provider (historical-aware)
  - Creates InvestmentSignal
  - Calls metadata extractor (but gets nothing due to data structure mismatch)

- **`_create_investment_signal()`** (src/pipeline.py:313-520)
  - Extracts data from nested analysis structure
  - Fetches price from cache/provider (historical-aware)
  - Creates InvestmentSignal
  - Calls metadata extractor (works correctly)

**Problem**: ~200 lines of duplicated code with same logic for price fetching, signal creation, and metadata extraction.

### 4. Metadata Extraction Failure in LLM Mode

**Root Cause**:
- `extract_analysis_metadata()` expects `analysis["analysis"]["technical"]["indicators"]`
- LLM synthesis output only has `analysis["scores"]["technical"]`
- Individual analysis tasks (technical, fundamental, sentiment) DO produce detailed metrics
- But synthesis task only receives/outputs aggregate scores

**Location of Issue**:
- Synthesis task template: `src/agents/crewai_agents.py:364-458`
- Only passes aggregate analysis results to synthesis
- Synthesis agent instructed to output minimal JSON (scores only, no detailed metrics)

### 5. Price Fetching Logic Duplication

Both functions implement the same historical-aware price fetching:
- Detect if `analysis_date < today` for historical mode
- Fetch historical price if needed via `provider_manager.get_stock_prices()`
- Fall back to cache for current prices
- Return `None` if no valid price found

**Lines**:
- LLM mode: src/main.py:399-416
- Rule-based mode: src/pipeline.py:341-444

---

## Proposed Unified Architecture

### Core Principle
**One unified pipeline with mode as a parameter, not two separate code paths.**

### Unified Flow Diagram

```
Configuration & CLI
    ↓
Unified AnalysisPipeline (mode: llm | rule_based)
    ↓
┌─────────────────────────────────────┐
│  1. Data Collection (shared)        │
│     - Price data                    │
│     - Fundamentals                  │
│     - News/sentiment                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. Agent Execution (mode-aware)    │
│                                     │
│  IF llm_mode:                       │
│    → HybridAnalysisAgent wrapper    │
│       → CrewAI Agent                │
│       → Fallback: Rule-based Agent  │
│  ELSE:                              │
│    → Rule-based Agent directly      │
│                                     │
│  Agents: Technical, Fundamental,    │
│          Sentiment                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Result Normalization (NEW!)     │
│     - Convert agent outputs to      │
│       UNIFIED data structure        │
│     - Detailed metrics preserved    │
│     - Works for both LLM & rule     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. Signal Synthesis (shared)       │
│     - Single synthesis function     │
│     - Receives normalized data      │
│     - Calculates weighted scores    │
│     - Generates recommendation      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  5. Signal Creation (SINGLE!)       │
│     - One create_signal() function  │
│     - Receives synthesis + details  │
│     - Price fetching (historical)   │
│     - Metadata extraction           │
│     - Returns InvestmentSignal      │
└─────────────────────────────────────┘
    ↓
Database Storage & Report Generation
```

### Key Design Decisions

1. **Unified Data Structure**: Define `AnalysisResult` Pydantic model that both modes populate
2. **Result Normalizer**: New component to convert agent outputs to unified structure
3. **Single Signal Creator**: Merge `_create_signal_from_llm_result` and `_create_investment_signal`
4. **Mode-Aware Agent Wrapper**: Existing `HybridAnalysisAgent` becomes the standard interface
5. **Enhanced Synthesis**: Synthesis receives detailed metrics, not just scores

---

## Detailed Implementation Plan

### Phase 1: Define Unified Data Models

**File**: `src/analysis/models.py`

**Add New Models**:

```python
class AnalysisComponentResult(BaseModel):
    """Unified result structure for any analysis component."""

    component: str  # "technical", "fundamental", "sentiment"
    score: float = Field(ge=0, le=100)

    # Detailed data (preserves all metrics)
    indicators: dict[str, Any] | None = None  # Technical indicators
    metrics: dict[str, Any] | None = None     # Fundamental metrics
    data: dict[str, Any] | None = None        # Raw component data

    # Structured metadata
    technical_indicators: TechnicalIndicators | None = None
    fundamental_metrics: FundamentalMetrics | None = None
    analyst_info: AnalystInfo | None = None
    sentiment_info: SentimentInfo | None = None

    reasoning: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=100)


class UnifiedAnalysisResult(BaseModel):
    """Unified analysis result structure for both LLM and rule-based modes."""

    ticker: str
    mode: str  # "llm" or "rule_based"

    # Component results with full detail
    technical: AnalysisComponentResult
    fundamental: AnalysisComponentResult
    sentiment: AnalysisComponentResult

    # Synthesis
    final_score: float = Field(ge=0, le=100)
    recommendation: str
    confidence: float = Field(ge=0, le=100)

    # Metadata for signal creation
    company_name: str | None = None
    market: str | None = None
    sector: str | None = None

    # Risk assessment
    risk_assessment: RiskAssessment | None = None

    # Reasoning
    key_reasons: list[str] = Field(default_factory=list)
    rationale: str | None = None
    caveats: list[str] = Field(default_factory=list)
```

**Files to Modify**:
- `src/analysis/models.py`: Add new models

---

### Phase 2: Create Result Normalizer

**New File**: `src/analysis/normalizer.py`

**Purpose**: Convert agent outputs (LLM or rule-based) to `UnifiedAnalysisResult`.

```python
class AnalysisResultNormalizer:
    """Normalizes agent outputs to unified structure."""

    @staticmethod
    def normalize_llm_result(
        ticker: str,
        technical_result: dict,
        fundamental_result: dict,
        sentiment_result: dict,
        synthesis_result: dict,
    ) -> UnifiedAnalysisResult:
        """Convert LLM agent outputs to unified structure."""
        # Extract detailed metrics from individual agent outputs
        # Not from synthesis (which only has scores)
        ...

    @staticmethod
    def normalize_rule_based_result(
        analysis: dict[str, Any]
    ) -> UnifiedAnalysisResult:
        """Convert rule-based analysis to unified structure."""
        # Extract from nested analysis["analysis"] structure
        ...

    @staticmethod
    def extract_technical_component(
        tech_result: dict, mode: str
    ) -> AnalysisComponentResult:
        """Extract technical analysis with all indicators."""
        ...

    # Similar methods for fundamental and sentiment
```

**Files to Create**:
- `src/analysis/normalizer.py`: New normalizer module

---

### Phase 3: Refactor Metadata Extractor

**File**: `src/analysis/metadata_extractor.py`

**Changes**: Update to work with `UnifiedAnalysisResult` instead of raw dict.

```python
def extract_analysis_metadata(
    result: UnifiedAnalysisResult
) -> AnalysisMetadata | None:
    """Extract metadata from unified analysis result."""

    return AnalysisMetadata(
        technical_indicators=result.technical.technical_indicators,
        fundamental_metrics=result.fundamental.fundamental_metrics,
        analyst_info=result.fundamental.analyst_info,
        sentiment_info=result.sentiment.sentiment_info,
    )
```

**Files to Modify**:
- `src/analysis/metadata_extractor.py`: Update function signatures

---

### Phase 4: Create Unified Signal Creator

**New File**: `src/analysis/signal_creator.py`

**Purpose**: Single function to create InvestmentSignal from UnifiedAnalysisResult.

```python
class SignalCreator:
    """Creates InvestmentSignal from unified analysis results."""

    def __init__(
        self,
        cache_manager,
        provider_manager,
        risk_assessor,
    ):
        self.cache_manager = cache_manager
        self.provider_manager = provider_manager
        self.risk_assessor = risk_assessor

    def create_signal(
        self,
        result: UnifiedAnalysisResult,
        portfolio_context: dict[str, Any],
        analysis_date: date | None = None,
    ) -> InvestmentSignal | None:
        """Create investment signal from unified analysis result.

        Handles:
        - Historical vs current price fetching
        - Metadata extraction
        - Risk assessment
        - Allocation calculation
        """
        # Unified price fetching logic (historical-aware)
        current_price = self._fetch_price(
            result.ticker,
            analysis_date
        )

        # Extract metadata
        metadata = extract_analysis_metadata(result)

        # Assess risks
        risk_assessment = self._assess_risk(result, portfolio_context)

        # Create signal
        return InvestmentSignal(
            ticker=result.ticker,
            name=result.company_name or result.ticker,
            market=result.market or "unknown",
            sector=result.sector,
            current_price=current_price,
            currency="USD",  # From price data
            scores=ComponentScores(
                technical=result.technical.score,
                fundamental=result.fundamental.score,
                sentiment=result.sentiment.score,
            ),
            final_score=result.final_score,
            recommendation=result.recommendation,
            confidence=result.confidence,
            time_horizon="3M",
            expected_return_min=self._calc_expected_return_min(result),
            expected_return_max=self._calc_expected_return_max(result),
            key_reasons=result.key_reasons,
            risk=risk_assessment,
            allocation=None,  # Calculated later
            generated_at=datetime.now(),
            analysis_date=analysis_date.strftime("%Y-%m-%d")
                if analysis_date else datetime.now().strftime("%Y-%m-%d"),
            rationale=result.rationale,
            caveats=result.caveats,
            metadata=metadata,
        )

    def _fetch_price(
        self, ticker: str, analysis_date: date | None
    ) -> float | None:
        """Fetch price (historical-aware)."""
        # Single implementation for both modes
        # Combines logic from both old functions
        ...
```

**Files to Create**:
- `src/analysis/signal_creator.py`: New signal creator module

---

### Phase 5: Refactor LLM Integration

**File**: `src/llm/integration.py`

**Changes**:
1. Store individual analysis results (with detailed metrics)
2. Pass detailed results to normalizer
3. Use SignalCreator instead of creating signal in main.py

```python
def analyze_instrument(
    self,
    ticker: str,
    context: dict[str, Any] = None,
    progress_callback: Optional[callable] = None,
) -> UnifiedAnalysisResult:  # ← Changed return type
    """Perform comprehensive analysis of a single instrument.

    Returns:
        UnifiedAnalysisResult with detailed metrics
    """
    # ... existing execution logic ...

    # Extract individual results (WITH detailed metrics)
    technical_results = analysis_results["results"]["technical_analysis"]["result"]
    fundamental_results = analysis_results["results"]["fundamental_analysis"]["result"]
    sentiment_results = analysis_results["results"]["sentiment_analysis"]["result"]

    # Get synthesis
    synthesis_results = self.synthesize_signal(...)

    # Normalize to unified structure
    unified_result = AnalysisResultNormalizer.normalize_llm_result(
        ticker=ticker,
        technical_result=technical_results,  # Full detail
        fundamental_result=fundamental_results,  # Full detail
        sentiment_result=sentiment_results,  # Full detail
        synthesis_result=synthesis_results,  # Scores & recommendation
    )

    return unified_result
```

**Files to Modify**:
- `src/llm/integration.py`: Update return types and add normalization

---

### Phase 6: Refactor AnalysisPipeline

**File**: `src/pipeline.py`

**Changes**:
1. Return `UnifiedAnalysisResult` instead of raw dict
2. Remove `_create_investment_signal()` (replaced by SignalCreator)
3. Add normalization step

```python
def analyze_ticker(
    self,
    ticker: str,
    context: dict[str, Any] = None,
) -> UnifiedAnalysisResult | None:  # ← Changed return type
    """Analyze a ticker using rule-based agents.

    Returns:
        UnifiedAnalysisResult with detailed metrics
    """
    # ... existing analysis logic ...

    # Normalize to unified structure
    unified_result = AnalysisResultNormalizer.normalize_rule_based_result(
        analysis_dict
    )

    return unified_result
```

**Files to Modify**:
- `src/pipeline.py`: Update analysis methods, remove old signal creation

---

### Phase 7: Update Main Entry Point

**File**: `src/main.py`

**Changes**:
1. Remove `_create_signal_from_llm_result()` (replaced by SignalCreator)
2. Remove `_run_llm_analysis()` (merge into unified flow)
3. Use SignalCreator for both modes

```python
# Initialize SignalCreator (shared by both modes)
signal_creator = SignalCreator(
    cache_manager=cache_manager,
    provider_manager=provider_manager,
    risk_assessor=pipeline.risk_assessor,
)

# Analyze tickers
for ticker in tickers:
    if use_llm:
        # LLM mode
        unified_result = orchestrator.analyze_instrument(ticker, context)
    else:
        # Rule-based mode
        unified_result = pipeline.analyze_ticker(ticker, context)

    if unified_result:
        # Create signal (SAME function for both modes)
        signal = signal_creator.create_signal(
            result=unified_result,
            portfolio_context=portfolio_context,
            analysis_date=historical_date,
        )

        if signal:
            signals.append(signal)

            # Store to DB
            if recommendations_repo:
                recommendations_repo.store_recommendation(
                    signal=signal,
                    run_session_id=run_session_id,
                    analysis_mode="llm" if use_llm else "rule_based",
                )
```

**Files to Modify**:
- `src/main.py`: Simplify analyze command, remove duplicate functions

---

### Phase 8: Update Synthesis Task (LLM Mode)

**File**: `src/agents/crewai_agents.py`

**Changes**: Synthesis task should receive and preserve detailed metrics.

**Current Problem**: Synthesis only receives stringified analysis results and outputs minimal JSON.

**Solution**:
- Keep synthesis lightweight (scores + recommendation only)
- Don't try to make LLM output detailed metrics (unreliable)
- Instead, extract detailed metrics from individual agent outputs in normalizer

**No changes needed** - normalizer handles this by extracting from individual agent outputs.

---

## Migration Strategy

### Step 1: Add New Code (No Breaking Changes)
1. Create `AnalysisComponentResult` and `UnifiedAnalysisResult` models
2. Create `AnalysisResultNormalizer` class
3. Create `SignalCreator` class
4. Add tests for new components

### Step 2: Integrate New Code Alongside Old
1. Update `LLMAnalysisOrchestrator` to return `UnifiedAnalysisResult`
2. Update `AnalysisPipeline` to return `UnifiedAnalysisResult`
3. Keep old signal creation functions temporarily

### Step 3: Switch Over
1. Update `src/main.py` to use `SignalCreator`
2. Verify both modes work with unified approach
3. Run integration tests

### Step 4: Clean Up
1. Remove `_create_signal_from_llm_result()` from `src/main.py`
2. Remove `_create_investment_signal()` from `src/pipeline.py`
3. Update metadata extractor to use `UnifiedAnalysisResult`
4. Remove old imports and dead code

---

## Testing Strategy

### Unit Tests
- `test_analysis_result_normalizer.py`: Test normalization from both modes
- `test_signal_creator.py`: Test signal creation with unified results
- `test_metadata_extractor.py`: Update for new input type

### Integration Tests
- Test LLM mode end-to-end with metadata
- Test rule-based mode end-to-end with metadata
- Verify identical signal structure from both modes

### Validation Tests
- Run analysis on same tickers with both modes
- Compare output structure (should be identical schema)
- Verify metadata appears in both modes

---

## Expected Benefits

### 1. Maintainability
- ✅ Single source of truth for signal creation
- ✅ Changes apply to both modes automatically
- ✅ Easier to add new features (e.g., new risk metrics)

### 2. Code Reduction
- ❌ Remove ~200 lines of duplicate code
- ❌ Remove two separate execution paths
- ❌ Consolidate price fetching logic

### 3. Consistency
- ✅ Both modes produce identical InvestmentSignal structure
- ✅ Metadata works in both modes
- ✅ Risk assessment consistent across modes

### 4. Debugging
- ✅ Single function to debug for signal creation issues
- ✅ Unified logging for both modes
- ✅ Easier to trace data flow

---

## Risks & Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**:
- Phased migration (add new code first, remove old last)
- Comprehensive integration tests before removing old code
- Keep both implementations running in parallel initially

### Risk 2: LLM Output Parsing Changes
**Mitigation**:
- Normalizer handles parsing differences
- Extensive testing with real LLM outputs
- Fallback to rule-based mode if normalization fails

### Risk 3: Performance Impact
**Mitigation**:
- Normalizer should be lightweight (data transformation only)
- No additional API calls or computations
- Benchmark before and after

---

## Success Criteria

1. ✅ Both modes use `SignalCreator` for signal creation
2. ✅ Both modes populate metadata correctly in reports
3. ✅ `_create_signal_from_llm_result` and `_create_investment_signal` removed
4. ✅ All tests pass (unit + integration)
5. ✅ Code coverage maintained or improved
6. ✅ No duplicate logic for price fetching, signal creation, or metadata extraction

---

## Timeline Estimate

- **Phase 1-2**: 2-3 hours (Models + Normalizer)
- **Phase 3-4**: 2 hours (Metadata + SignalCreator)
- **Phase 5-6**: 3-4 hours (LLM integration + Pipeline)
- **Phase 7-8**: 2 hours (Main entry point)
- **Testing**: 2-3 hours
- **Total**: ~12-15 hours of focused work

---

## Files Summary

### New Files (5)
- `src/analysis/normalizer.py`: Result normalization
- `src/analysis/signal_creator.py`: Unified signal creation

### Modified Files (8)
- `src/analysis/models.py`: Add UnifiedAnalysisResult
- `src/analysis/metadata_extractor.py`: Update for new input type
- `src/llm/integration.py`: Return UnifiedAnalysisResult
- `src/pipeline.py`: Return UnifiedAnalysisResult, remove old signal creation
- `src/main.py`: Use SignalCreator, remove duplicate functions
- `src/agents/hybrid.py`: Minor updates if needed

### Removed Code
- `src/main.py::_create_signal_from_llm_result` (~180 lines)
- `src/pipeline.py::_create_investment_signal` (~200 lines)

**Net Result**: -380 lines, +300 lines = **-80 lines total**

---

## Questions for User

Before starting implementation, please confirm:

1. **Scope**: Should we refactor just signal creation or the entire analysis flow?
2. **Timeline**: Is ~12-15 hours acceptable, or should we do a minimal version first?
3. **Backward Compatibility**: Do we need to support old signal formats, or can we migrate fully?
4. **Testing**: Should we test on production data before removing old code?
