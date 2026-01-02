# FalconSignals Notebooks

This directory contains Jupyter notebooks for exploring, testing, and understanding the FalconSignals analysis workflow.

## 📋 Purpose

These notebooks provide:
- ✅ Transparent, step-by-step exploration of the analysis workflow
- ✅ Sanity checking of data fetching, caching, and analysis logic
- ✅ Debugging and understanding of edge cases
- ✅ Interactive documentation for developers
- ✅ Quick experimentation without running full CLI commands

## 🛠️ Setup

### 1. Install Dependencies

```bash
# Install all dependencies (including jupytext and notebook)
uv sync

# Verify jupytext is installed
uv run jupytext --version
```

### 2. Open Notebooks

You can open notebooks in multiple ways:

**Option A: Jupyter Lab (Recommended)**
```bash
uv run jupyter lab
```

**Option B: VS Code**
- Install the Jupyter extension in VS Code
- Open any `.py` or `.ipynb` file
- VS Code will automatically detect it as a notebook

**Option C: Jupyter Notebook (Classic)**
```bash
uv run jupyter notebook
```

### 3. Sync .py and .ipynb Files

Notebooks are stored in **jupytext percent format** (`.py` files). The `.ipynb` files are generated locally but **not tracked in git**.

**Manual Sync:**
```bash
# Sync a single notebook (creates/updates .ipynb)
uv run jupytext --sync notebooks/01_data_fetching_and_caching.py

# Sync all notebooks
uv run jupytext --sync notebooks/*.py
```

**Automatic Sync in IDEs:**
- VS Code with Jupyter extension syncs automatically
- Jupyter Lab/Notebook syncs when you save

**Note:** Only `.py` files are tracked in git. The `.ipynb` files are ignored (see [.gitignore](.gitignore)).

## 📓 Available Notebooks

### 1. Data Fetching and Caching
**File:** [01_data_fetching_and_caching.py](01_data_fetching_and_caching.py)

**Purpose:**
- Explore `ProviderManager` and `CacheManager`
- Inspect cache directory structure
- Test cache TTL and expiration logic
- Compare fresh fetch vs cached data

**Key Topics:**
- Data providers (Yahoo Finance, Alpha Vantage, Finnhub)
- Cache file structure and organization
- TTL configuration for different data types
- Batch fetching for multiple tickers

---

### 2. Historical Analysis Exploration
**File:** [02_historical_analysis_exploration.py](02_historical_analysis_exploration.py)

**Purpose:**
- Test historical analysis with `--date` flag
- Verify historical price fetching (no future information leakage)
- Inspect `SignalCreator._fetch_historical_price()` logic
- Validate database storage of historical recommendations

**Key Topics:**
- Historical vs current price fetching
- Bug fixes (current_price=0, future leakage)
- Database verification
- Date handling in analysis

---

### 3. Current Analysis Exploration
**File:** [03_current_analysis_exploration.py](03_current_analysis_exploration.py)

**Purpose:**
- Test current date analysis (no `--date` flag)
- Inspect latest price fetching
- Explore session tracking in database
- Compare rule-based vs LLM workflows

**Key Topics:**
- Latest price retrieval
- Analysis session management
- Database storage and metadata
- Current vs historical analysis differences

---

### 4. LLM vs Rule-Based Comparison
**File:** [04_llm_vs_rule_based_comparison.py](04_llm_vs_rule_based_comparison.py)

**Purpose:**
- Compare LLM and rule-based analysis modes
- Analyze differences in signals and confidence
- Compare execution time and costs
- Understand strengths and weaknesses of each mode

**Key Topics:**
- Architecture comparison
- Signal distribution analysis
- Confidence calibration
- Cost/performance tradeoffs
- Use case recommendations

---

### 5. Performance Tracking Exploration
**File:** [05_performance_tracking_exploration.py](05_performance_tracking_exploration.py)

**Purpose:**
- Explore `PriceDataManager` and performance tracking
- Calculate returns, alpha, and Sharpe ratio
- Compare against benchmarks (SPY, QQQ)
- Analyze confidence calibration

**Key Topics:**
- Price tracking workflow
- Return calculation
- Benchmark comparison
- Risk-adjusted metrics
- Win rate and confidence analysis

---

### 6. Signal Creation Deep Dive
**File:** [06_signal_creation_deep_dive.py](06_signal_creation_deep_dive.py)

**Purpose:**
- Deep dive into signal creation and scoring logic
- Understand fundamental, technical, sentiment scoring
- Analyze weighted combination (35/35/30)
- Test edge cases and validation rules

**Key Topics:**
- Scoring methodology breakdown
- Confidence calculation
- Signal thresholds (buy/hold/avoid)
- Edge case handling
- Validation rules

---

## 🚀 Usage Examples

### Running a Complete Notebook

1. Open Jupyter Lab:
   ```bash
   uv run jupyter lab
   ```

2. Navigate to the notebook you want to run (e.g., `01_data_fetching_and_caching.py`)

3. Run all cells: `Run > Run All Cells`

4. Review outputs and explore interactively

### Experimenting with Code

You can modify and experiment with any code cells:

```python
# Example: Try different tickers
ticker = "NVDA"  # Change to any ticker

# Example: Try different date ranges
from_date = datetime(2025, 6, 1)  # Modify dates
to_date = datetime(2025, 9, 30)
```

### Saving Your Work

When you save a notebook in Jupyter:
- The `.ipynb` file is saved locally (not tracked in git)
- Run `jupytext --sync notebook.py` to update the `.py` file
- Commit only the `.py` file to git

## 📝 Best Practices

### 1. Keep Notebooks Up-to-Date

When you make changes to the codebase, review and update notebooks if needed.

### 2. Test Before Committing

Run notebooks to ensure they execute without errors before committing changes.

### 3. Clear Outputs Before Committing

The `.py` format doesn't store outputs, so you don't need to clear them manually. Just commit the `.py` file.

### 4. Add New Notebooks

To add a new notebook:

1. Create a `.py` file with jupytext header:
   ```python
   # ---
   # jupyter:
   #   jupytext:
   #     formats: ipynb,py:percent
   #     text_representation:
   #       extension: .py
   #       format_name: percent
   #       format_version: '1.3'
   #       jupytext_version: 1.18.1
   #   kernelspec:
   #     display_name: Python 3
   #     language: python
   #     name: python3
   # ---
   ```

2. Add your cells using `# %%` for code cells and `# %% [markdown]` for markdown cells

3. Sync to create `.ipynb`: `uv run jupytext --sync notebooks/your_notebook.py`

4. Commit only the `.py` file

### 5. Use Descriptive Names

Name notebooks with a number prefix and descriptive name:
- `01_descriptive_name.py`
- `02_another_topic.py`

## 🐛 Troubleshooting

### Issue: Can't open .py file as notebook

**Solution:** Make sure the jupytext header is present at the top of the file and the `formats` field includes `ipynb`.

### Issue: Changes to .py file not reflected in .ipynb

**Solution:** Run `jupytext --sync notebook.py` to update the `.ipynb` file.

### Issue: Import errors when running notebooks

**Solution:** Make sure you've added the project root to `sys.path`:
```python
import sys
from pathlib import Path

project_root = Path.cwd().parent
sys.path.insert(0, str(project_root))
```

### Issue: Cache or database not found

**Solution:** Ensure you're running notebooks from the `notebooks/` directory, and the project structure is intact.

## 🔗 Related Documentation

- **CLAUDE.md**: Full project documentation
- **docs/roadmap.md**: Implementation roadmap
- **docs/llm_cli_guide.md**: LLM mode usage guide
- **README.md**: Project overview

## 📚 Additional Resources

- [Jupytext Documentation](https://jupytext.readthedocs.io/)
- [Jupyter Lab Documentation](https://jupyterlab.readthedocs.io/)
- [FalconSignals Architecture](../docs/architecture.mermaid)

---

**Questions or Issues?**
- Check the troubleshooting section above
- Review the test notebook: [test_jupytext_setup.py](test_jupytext_setup.py)
- Refer to the main project documentation in `CLAUDE.md`
