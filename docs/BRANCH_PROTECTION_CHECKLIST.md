# Branch Protection Setup Checklist ✅

Quick reference for setting up branch protection on the `main` branch.

## Pre-Setup Requirements

- ✅ GitHub repository created
- ✅ CI/CD workflows configured (`.github/workflows/pr-tests.yml`)
- ✅ At least one successful workflow run (so status checks appear)

## Setup Steps

### 1. Navigate to Settings
- [ ] Open repository on GitHub
- [ ] Click **Settings** tab
- [ ] Click **Branches** in left sidebar
- [ ] Click **Add rule** button

### 2. Configure Branch Pattern
- [ ] Enter branch name: `main`
- [ ] Keep default pattern options

### 3. Require Pull Request Reviews
- [ ] ✅ Check: **Require a pull request before merging**
- [ ] ✅ Check: **Require approvals**
- [ ] Set number of approvals: **1**
- [ ] ✅ Check: **Dismiss stale pull request approvals when new commits are pushed**

### 4. Require Status Checks
- [ ] ✅ Check: **Require status checks to pass before merging**
- [ ] ✅ Check: **Require branches to be up to date before merging**

### 5. Select Status Checks to Require

Search for and select:
- [ ] `PR Tests / test` (Required - main workflow)
- [ ] `Code Coverage / coverage` (Optional - coverage workflow)

**Note:** Status checks appear in the dropdown only after first workflow run on the branch.

### 6. Additional Protection Options
- [ ] ✅ Check: **Include administrators**
  - Enforces rules for repository admins too
- [ ] ✅ Check: **Restrict who can push to matching branches** (Optional)
  - Useful for teams; less critical for solo development
- [ ] ✅ Check: **Require code owners review** (Optional)
  - Only if CODEOWNERS file exists
- [ ] ✅ Check: **Require conversation resolution before merging**
  - Ensures review comments are addressed

### 7. Save Configuration
- [ ] Click **Create** button (for new rule) or **Save changes** (for existing rule)

## Verification Checklist

After setup, verify the configuration:

### Settings are Correct
- [ ] Navigate to **Settings** → **Branches** → **main**
- [ ] Confirm all checkboxes are set as above
- [ ] Confirm status checks show `PR Tests / test`

### Test with a PR
- [ ] Create test branch: `git checkout -b test/verify-protection`
- [ ] Make a small change and commit: `git add . && git commit -m "test: verify branch protection"`
- [ ] Push branch: `git push origin test/verify-protection`
- [ ] Create Pull Request to `main`

### Verify Merge Blocking
- [ ] 🟡 CI/CD workflows should be running (yellow status)
- [ ] ❌ Merge button should be **disabled** with message:
  - "Merge blocked" or "Some checks were not successful"
  - "This branch is 1 commit ahead, 0 behind main"
- [ ] Try to merge → Should show error

### Verify All Checks Pass
- [ ] Wait for workflows to complete (~30-35 seconds)
- [ ] All checks should be ✅ green
- [ ] ❌ Merge button still disabled (no approval yet)
- [ ] Try to merge → Should show "Require approvals"

### Verify Review Requirement
- [ ] Get another user to approve PR (or use second account)
- [ ] After approval + all checks pass
- [ ] ✅ Merge button should be **enabled** (green)
- [ ] Merge the PR
- [ ] ✅ PR should merge successfully
- [ ] Delete the test branch

## Configuration Reference

### Required Settings Summary

```
Main Branch Protection Rule:
├── Branch pattern: main
├── Pull Request Reviews:
│   ├── Require pull request: ✅
│   ├── Require approvals: ✅ (1 approval)
│   └── Dismiss stale reviews: ✅
├── Status Checks:
│   ├── Require status checks: ✅
│   ├── Require up-to-date branch: ✅
│   └── Required checks:
│       ├── PR Tests / test
│       └── Code Coverage / coverage (optional)
└── Additional:
    ├── Include administrators: ✅
    └── Restrict push access: ⚪ (optional)
```

## Status Check Names

When selecting status checks in the dropdown, look for:

| Workflow File | Status Check Name | Required? |
|--------------|------------------|-----------|
| `.github/workflows/pr-tests.yml` | `PR Tests / test` | ✅ Yes |
| `.github/workflows/coverage.yml` | `Code Coverage / coverage` | ⚪ Optional |

If status checks don't appear in dropdown:
1. Workflow may not have run yet
2. Go back and create a test PR to trigger the workflow
3. Return to branch protection settings
4. Status checks should now appear in dropdown

## Result: What Gets Blocked/Allowed

### What Gets Blocked ❌
- Merging without passing all CI/CD checks
- Merging without at least 1 approval
- Merging with outdated branch (stale code)
- Direct pushes to main (users must use PRs)
- Merging with unresolved review comments

### What Gets Allowed ✅
- Creating PRs from any branch
- Pushing to feature branches
- Merging after all checks pass + approval
- Merging after stale reviews are dismissed (new commits refresh review)
- Force pushing to feature branches (not main)

## Troubleshooting

### Status Checks Not Appearing in Dropdown
**Solution:** Workflow must run first
1. Create a test PR from `test/setup-github-action` branch
2. Let `PR Tests / test` workflow complete
3. Return to branch protection settings
4. Status checks should now appear

### Can Still Push to Main (Rules Not Enforced)
**Solution:** Verify branch protection rule was saved
1. Go to **Settings** → **Branches**
2. Confirm rule exists for `main`
3. Click the rule to view/edit
4. Verify all settings are correct
5. Click **Save changes**

### Merge Button Disabled Even After All Checks Pass
**Possible Causes:**
1. No approvals yet → Get review approval
2. Branch is outdated → Click "Update branch" button
3. Status checks not re-run → Dismiss and re-request review or push new commit
4. Not all required status checks completed → Wait for slower checks

## Administrative Actions

### Temporarily Disabling Rules (Emergency Only)
1. Go to **Settings** → **Branches** → **main**
2. Click **Edit** on the rule
3. Uncheck problematic requirements
4. Click **Save changes**
5. ⚠️ **Important:** Re-enable immediately after
6. Document the reason in a team issue

### Dismissing Required Reviews
Admins can dismiss reviews and merge directly:
1. PR must have all status checks passing
2. Admin clicks "Dismiss" on the approval requirement
3. Merge is allowed
4. ⚠️ **Only use for emergency fixes**

## Documentation References

- Full guide: [`docs/branch_protection_guide.md`](./branch_protection_guide.md)
- CI/CD setup: [`docs/ci_cd_setup.md`](./ci_cd_setup.md)
- Workflow diagram: [`docs/ci_cd_workflow.mermaid`](./ci_cd_workflow.mermaid)

## Timeline

**After branch protection is enabled:**

1. **Immediately** - All PRs start requiring approval + passing checks
2. **First week** - Team adjusts to PR workflow
3. **Ongoing** - Rules prevent broken code in main
4. **As needed** - Adjust thresholds (coverage %, review count)

## Support

If you encounter issues:

1. Check troubleshooting section above
2. Review [`docs/branch_protection_guide.md`](./branch_protection_guide.md) for detailed help
3. Verify status checks are named correctly
4. Test with a dummy PR to verify behavior
