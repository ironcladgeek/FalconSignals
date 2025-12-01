# CI/CD Setup Guide

This document describes the GitHub Actions workflows that ensure code quality and test coverage for the NordInvest project.

## Overview

The CI/CD pipeline automatically validates all pull requests to the `main` branch by:

1. **Running pre-commit checks** - Code formatting, linting, and conventional commit validation
2. **Executing the full test suite** - Unit and integration tests with detailed reporting
3. **Measuring code coverage** - Tracking test coverage trends over time

## Workflows

### 1. PR Tests (`pr-tests.yml`)

**Triggers:** Pull requests to `main` branch

**Steps:**

1. **Checkout Code** - Clone the repository
2. **Setup Python** - Configure Python 3.12 environment
3. **Install uv** - Set up the UV package manager
4. **Cache Dependencies** - Cache `~/.cache/uv` for faster runs
5. **Sync Dependencies** - Install dependencies from `uv.lock`
6. **Run Pre-commit Checks** - Execute linting and formatting:
   - Trailing whitespace removal
   - EOF newline fixing
   - YAML/TOML validation
   - Debug statement detection
   - Ruff linting (import sorting, unused imports, formatting)
   - Black code formatting
   - Conventional commit validation
7. **Run Tests with Coverage** - Execute pytest with:
   - Verbose output and short tracebacks
   - Coverage measurement (XML + terminal report)
   - Missing line coverage details
8. **Check Coverage Threshold** - Enforce minimum coverage:
   - Fails if coverage drops below 50%
   - Continues with warning if already below threshold
9. **Upload Coverage** - Send results to Codecov for:
   - Historical trend tracking
   - PR annotations with coverage diff
10. **Publish Test Results** - Annotate PR with detailed test results

**Expected Output:**

- ✅ All pre-commit checks pass
- ✅ All tests pass (219 tests)
- ✅ Coverage meets 50% threshold
- Test results comment on PR showing:
  - Number of passed/failed/skipped tests
  - Duration of test run
  - Detailed failure information (if any)
- Coverage report on Codecov with:
  - Coverage percentage
  - Missing coverage by file
  - Coverage trends and diffs

### 2. Code Coverage (Integrated in PR Tests)

**Status:** Coverage checking is now integrated into the PR Tests workflow (`pr-tests.yml`)

Coverage is no longer run in a separate workflow. Instead, it's measured during the main PR Tests workflow to:
- Reduce CI/CD execution time
- Provide faster feedback on PRs
- Combine test and coverage results in one report

The standalone `coverage.yml` workflow is still available for optional scheduled runs or manual execution, but is not required for PR validation.

**Coverage Metrics Tracked:**

- Coverage percentage per module (target: 70%+)
- Missing line coverage details
- Coverage trends over time (via Codecov)
- Coverage diff vs. base branch

## Branch Protection Rules

To enforce the CI/CD pipeline, configure branch protection rules on `main`:

1. Go to **Settings** → **Branches** → **Branch protection rules**
2. Create rule for `main` branch:
   - ✅ Require status checks to pass before merging
     - Select "PR Tests / test" workflow
     - Select "Code Coverage / coverage" workflow
   - ✅ Require code reviews before merging (recommended: 1 reviewer)
   - ✅ Require status checks to pass before merging
   - ✅ Include administrators in restrictions (optional)
   - ✅ Restrict who can push to matching branches (optional)

## Metrics & Thresholds

Current baseline metrics (as of Phase 7+):

- **Test Count:** 219 tests
- **Skipped Tests:** 14 (expected - skipped for integration tests)
- **Pass Rate:** 100% (219/219)
- **Coverage Threshold:** 50% (enforced, blocks PRs if breached)
- **Execution Time:** ~10-12 seconds (with coverage)

### Coverage Threshold Strategy

The project uses a tiered approach to coverage:

1. **PR Gate (Hard Requirement):** 50% minimum coverage
   - Blocks PR merge if coverage drops below 50%
   - Prevents regressions in test coverage
   - Applied in `pr-tests.yml` workflow

2. **Target Coverage:** 70%+ recommended
   - Aim for higher coverage in new code
   - Review coverage diffs in Codecov comments
   - Not enforced (warning only)

3. **Future Enhancement:** 80%+ for core modules
   - Consider enforcing higher thresholds for critical code
   - Can be configured per module/package

### Adjusting Coverage Threshold

To change the coverage requirement, edit the `pr-tests.yml` workflow:

```yaml
- name: Check coverage threshold
  run: |
    # Adjust the value below (current: 50)
    uv run coverage report --fail-under=50
```

Recommended progression:
- Phase 7: 50% (current - establish baseline)
- Phase 8: 60% (mature codebase)
- Phase 9: 70% (stable features)

## Local Development

To run the same checks locally before pushing:

```bash
# Run pre-commit checks (formatting, linting, commit validation)
uv run poe pre-commit

# Run all tests
uv run pytest tests/ -q

# Run tests with coverage report
uv run pytest tests/ --cov=src --cov-report=term-missing

# Check if coverage meets threshold (50%)
uv run pytest tests/ --cov=src --cov-report=term-missing && uv run coverage report --fail-under=50

# Run exactly what CI/CD runs
uv run pytest tests/ -v --tb=short --junit-xml=test-results.xml --cov=src --cov-report=xml --cov-report=term-missing && uv run coverage report --fail-under=50
```

**Tip:** Run these commands before committing to catch issues locally:

```bash
# All-in-one: linting + tests + coverage (what CI/CD checks)
uv run poe pre-commit && uv run pytest tests/ --cov=src --cov-report=term-missing && uv run coverage report --fail-under=50
```

## Troubleshooting

### Workflow Fails with "Module not found"

**Cause:** Dependencies not synced correctly
**Fix:** Ensure `uv.lock` is committed and up-to-date

```bash
uv sync
git add uv.lock
git commit -m "chore: update dependencies"
```

### Pre-commit Checks Fail (Formatting/Linting)

**Cause:** Code doesn't match black/ruff formatting
**Fix:** Run linting locally and commit the fixes

```bash
uv run poe lint
git add .
git commit -m "style: apply formatting rules"
```

### Tests Fail in CI but Pass Locally

**Cause:** Different Python versions or environment differences
**Fix:**

1. Verify you're using Python 3.12:
   ```bash
   python --version
   ```
2. Ensure `uv.lock` matches CI environment:
   ```bash
   uv sync
   uv run pytest tests/
   ```

### Coverage Upload Fails

**Cause:** Codecov token not configured
**Fix:** Add Codecov token to GitHub repository secrets:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Create secret `CODECOV_TOKEN` (get from codecov.io)
3. Workflow will automatically use the token

### Coverage Threshold Check Fails

**Cause:** Test coverage dropped below 50% threshold
**Fix:**

Option 1 - Write more tests (recommended):
```bash
# See which lines/files lack coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Write tests for uncovered code
# Then verify coverage improves
uv run coverage report --fail-under=50
```

Option 2 - Temporarily lower threshold (not recommended):
```bash
# Only do this if coverage was legitimately lower before
# Edit .github/workflows/pr-tests.yml and change:
uv run coverage report --fail-under=40  # Lower from 50 to 40
```

**Best Practice:** Always improve coverage rather than lower thresholds. Better coverage = fewer bugs.

### Coverage Reports Not Generated Locally

**Cause:** `pytest-cov` not installed
**Fix:**
```bash
uv sync  # Ensures pytest-cov is installed
uv run pip list | grep pytest-cov  # Verify installation
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## Performance Optimization

The workflow uses several optimizations to keep execution time reasonable:

1. **Dependency Caching** - Reuses cached dependencies across runs
2. **Parallel Testing** - pytest runs all tests in parallel by default
3. **Fast Linting** - Ruff is extremely fast (< 1 second for this project)
4. **JIT Compilation** - Python 3.12 with optimizations
5. **Combined Coverage** - Coverage measured during test run (no extra step)

Current benchmark (Ubuntu runner) - PR Tests workflow:
- Checkout: ~2s
- Setup Python: ~5s
- Install uv: ~3s
- Sync dependencies: ~8s
- Pre-commit checks: ~3s
- Tests + Coverage: ~8s
- Coverage upload: ~2s

**Total:** ~30-35 seconds per PR workflow

**Note:** Coverage integration adds ~3-4 seconds vs. tests alone, but eliminates the need for a separate coverage workflow, resulting in net time savings.

## Future Enhancements

Potential improvements:

### Implemented Features ✅
- **Coverage Threshold** - Now enforces 50% minimum (Phase 7)
- **Test Result Publishing** - Annotates PRs with detailed results (Phase 7)
- **Codecov Integration** - Tracks coverage trends over time (Phase 7)

### Planned Enhancements
1. **Increase Coverage Threshold** - Gradually raise from 50% to 70%+ for mature modules
2. **Performance Benchmarks** - Track test execution time trends (detect regressions)
3. **Dependency Security Checks** - Run `safety` or `pip-audit` to catch vulnerabilities
4. **LLM API Key Validation** - Ensure secrets are not leaked in outputs
5. **Docker Build** - Build and test Docker image in CI for containerization
6. **Scheduled Runs** - Daily tests against main branch (nighttime builds)
7. **PR Size Checks** - Warn on large PRs to enforce small, focused commits
8. **Auto-merge** - Auto-merge PRs from dependabot if all checks pass
9. **Coverage Comment** - Post coverage diff summary directly on PRs
10. **Performance Regression Detection** - Alert if tests slow down significantly

## Maintenance

### Updating Workflows

When updating dependencies or Python version:

1. Update `pyproject.toml` (requires-python)
2. Update `.github/workflows/pr-tests.yml` (python-version)
3. Update `.github/workflows/coverage.yml` (python-version)
4. Test locally with new Python version
5. Commit and push to create PR
6. Verify workflows pass with new configuration

### Archiving Old Results

GitHub keeps workflow runs for 90 days by default. To reduce storage:

1. Go to **Actions**
2. Select workflow
3. Click "Delete workflow runs" for old runs

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pre-commit Framework](https://pre-commit.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.io/)
- [UV Package Manager](https://github.com/astral-sh/uv)
