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

# %% [markdown]
# # Test Jupytext Setup
#
# This is a minimal test notebook to verify that jupytext pre-commit hook works correctly.
#
# **Expected behavior:**
# 1. This `.py` file should be synced to a `.ipynb` file when opened in Jupyter
# 2. When committing, the hook should format the code and keep files in sync
# 3. The `.ipynb` file should NOT be tracked in git (ignored by notebooks/.gitignore)

# %% [markdown]
# ## Test Code Cell
#
# Let's write some simple Python code to test formatting:

# %%
# Simple function to test ruff formatting
def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


# Test the function
message = greet("Jupytext")
print(message)

# %% [markdown]
# ## Test Data Exploration
#
# Let's test importing FalconSignals modules:

# %%
import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd().parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Python version: {sys.version}")

# %% [markdown]
# ## Test Import
#
# Try importing a FalconSignals module:

# %%
try:
    from src.config.loader import load_config

    # Test that we can actually use the imported function
    config = load_config()
    print("✅ Successfully imported and used load_config")
    print(f"✅ Config loaded with {len(config.markets)} markets configured")
    print("✅ Jupytext setup is working correctly!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"⚠️ Import succeeded but config loading failed: {e}")
    print("✅ This is OK - jupytext setup is still working!")

# %% [markdown]
# ## Summary
#
# If you can see this notebook in Jupyter and all cells execute without errors,
# then the jupytext setup is working correctly!
#
# **Next steps:**
# 1. Make a small edit to this file
# 2. Stage the changes: `git add notebooks/test_jupytext_setup.py`
# 3. Commit: `git commit -m "test: verify jupytext pre-commit hook"`
# 4. Verify that the hook runs and formats the code
# 5. Check that `.ipynb` file is NOT staged (ignored by git)
