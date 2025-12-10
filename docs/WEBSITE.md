># Website Publishing Guide

This document explains how to publish NordInvest analysis results to a static website using MkDocs, Material theme, and GitHub Pages.

## Overview

The website publishing feature allows you to:
- Generate public-facing web pages from analysis data
- Filter content by ticker, signal type, and date using tags
- Automatically build and deploy to GitHub Pages
- Share analysis results without exposing private portfolio data

## Architecture

### Components

1. **WebsiteGenerator** (`src/website/generator.py`)
   - Generates markdown pages from database signals
   - Creates report pages, ticker pages, index, and tag pages
   - Sanitizes content to remove private information

2. **Content Sanitizer** (`src/website/sanitizer.py`)
   - Removes portfolio allocations
   - Removes watchlist additions/removals
   - Removes portfolio alerts
   - Ensures only public-safe data is published

3. **MkDocs Configuration** (`website/mkdocs.yml`)
   - Material theme with dark/light mode
   - Navigation structure
   - Markdown extensions for rich formatting

4. **CLI Command** (`publish` in `src/main.py`)
   - User-friendly interface for content generation
   - Options for building and deploying

## Quick Start

### Prerequisites

Ensure you have the required dependencies installed:

```bash
uv pip install mkdocs mkdocs-material mkdocs-awesome-pages-plugin
```

### Basic Usage

#### Publish from a Session

```bash
# Publish and deploy
nordinvest publish --session-id 123

# Generate content only (no build)
nordinvest publish --session-id 123 --no-build

# Build but don't deploy
nordinvest publish --session-id 123 --build-only
```

#### Publish from a Date

```bash
# Publish all signals from a specific date
nordinvest publish --date 2025-12-10
```

#### Publish Specific Ticker

```bash
# Generate page for one ticker
nordinvest publish --ticker NVDA --date 2025-12-10
```

## Content Structure

The website is organized as follows:

```
website/docs/
├── index.md                 # Homepage with recent reports
├── about.md                 # About page
├── reports/                 # Daily analysis reports
│   ├── 2025-12-10.md
│   └── 2025-12-09.md
├── tickers/                 # Individual ticker pages
│   ├── AAPL.md
│   ├── NVDA.md
│   └── MSFT.md
└── tags/                    # Tag pages for filtering
    ├── AAPL.md              # All AAPL analysis
    ├── buy.md               # All buy signals
    └── 2025-12-10.md        # All signals from date
```

## Generated Content

### Report Pages

Report pages (`reports/YYYY-MM-DD.md`) contain:
- Date and metadata
- Signals grouped by strength (Strong Buy, Buy, Hold Bullish)
- Ticker links for detailed history
- Tags for filtering (ticker, signal type, date)
- **Excludes:** Portfolio allocations, watchlist, personal alerts

### Ticker Pages

Ticker pages (`tickers/SYMBOL.md`) contain:
- Complete recommendation history
- Table with date, recommendation, confidence, price, mode
- Chronological view of analysis evolution

### Tag Pages

Tag pages (`tags/*.md`) enable filtering:
- **Ticker tags** (e.g., `AAPL.md`): All analysis for that ticker
- **Signal type tags** (e.g., `buy.md`): All signals of that type
- **Date tags** (e.g., `2025-12-10.md`): All signals from that date

### Index Page

Homepage (`index.md`) shows:
- Welcome message
- Recent analysis runs table
- Links to reports and features
- Last updated timestamp

## Deployment

### GitHub Pages Setup

1. **Enable GitHub Pages in Repository Settings:**
   - Go to Settings → Pages
   - Source: Deploy from branch
   - Branch: `gh-pages`
   - Folder: `/ (root)`

2. **Configure Custom Domain (Optional):**
   - Add CNAME file: `echo "yourdomain.com" > website/docs/CNAME`
   - Update DNS records at your domain provider (e.g., GoDaddy)
   - Add CNAME record pointing to `ironcladgeek.github.io`

### Automated Deployment

The GitHub Actions workflow (`.github/workflows/publish-website.yml`) automatically deploys when:
- Code is pushed to `main` branch
- Files in `website/` or `src/website/` are changed
- Workflow is manually triggered

### Manual Deployment

#### Using the Script

```bash
# Deploy with build
./scripts/deploy_website.sh

# Deploy without rebuild (use existing site/)
./scripts/deploy_website.sh --no-build

# Force deploy with uncommitted changes
./scripts/deploy_website.sh --force
```

#### Using MkDocs Directly

```bash
cd website

# Build site
mkdocs build

# Build and deploy
mkdocs gh-deploy --force --clean
```

## Content Privacy

### What Gets Published

✅ **Included:**
- Ticker symbols
- Recommendations (buy, sell, hold, etc.)
- Confidence scores
- Analysis dates
- Price at analysis
- Fundamental/technical/sentiment scores
- Risk assessments
- Reasoning and key factors

❌ **Excluded:**
- Portfolio allocations
- Watchlist additions/removals
- Portfolio alerts
- Personal investment amounts
- Transaction history

### Sanitization

All content passes through `sanitize_report_for_web()` which:
1. Creates a deep copy to avoid modifying originals
2. Removes `allocation_suggestion`
3. Removes `watchlist_additions` and `watchlist_removals`
4. Removes `portfolio_alerts`
5. Preserves all public analysis data

## Customization

### Update Site Metadata

Edit `website/mkdocs.yml`:

```yaml
site_name: NordInvest Analysis
site_description: AI-powered financial analysis
site_url: https://yourdomain.com
repo_url: https://github.com/ironcladgeek/NordInvest
```

### Customize Theme

Change colors, fonts, features in `theme` section:

```yaml
theme:
  name: material
  palette:
    primary: indigo
    accent: indigo
```

### Add Custom Pages

Create markdown files in `website/docs/`:

```bash
echo "# Custom Page" > website/docs/custom.md
```

Update `nav` in `mkdocs.yml`:

```yaml
nav:
  - Custom: custom.md
```

## Development

### Local Preview

```bash
cd website
mkdocs serve
```

Visit `http://127.0.0.1:8000` to preview changes.

### Generate Test Content

```bash
# Generate content from latest session without building
nordinvest publish --session-id 123 --no-build

# Preview
cd website && mkdocs serve
```

## Troubleshooting

### Build Fails

**Issue:** `mkdocs build` fails with errors

**Solutions:**
1. Check YAML syntax in `mkdocs.yml`
2. Ensure all linked pages exist
3. Verify markdown formatting in generated files
4. Check for broken links

### Deployment Fails

**Issue:** `mkdocs gh-deploy` fails

**Solutions:**
1. Ensure you have write permissions to repository
2. Check that git is configured (`git config user.name/email`)
3. Try with `--force` flag
4. Verify you're on the correct branch

### Missing Content

**Issue:** Generated pages don't appear on site

**Solutions:**
1. Run `nordinvest publish` to regenerate content
2. Check database has signals: `SELECT COUNT(*) FROM recommendations;`
3. Verify navigation files (`.pages`) exist
4. Rebuild site: `cd website && mkdocs build --clean`

### Tags Not Working

**Issue:** Tag pages don't show content

**Solutions:**
1. Ensure tags directory exists: `mkdir -p website/docs/tags`
2. Regenerate tag pages: `publish` command creates them automatically
3. Update navigation: `update_navigation()` creates `.pages` files

## API Reference

### WebsiteGenerator

```python
from src.website.generator import WebsiteGenerator

generator = WebsiteGenerator(
    config=config,
    db_path="data/nordinvest.db",
    output_dir="website/docs/"
)

# Generate report page
report_path = generator.generate_report_page(
    signals=signals,
    report_date="2025-12-10",
    metadata={"session_id": 123}
)

# Generate ticker page
ticker_path = generator.generate_ticker_page("AAPL")

# Generate all tag pages
tag_pages = generator.generate_tag_pages()

# Generate index
index_path = generator.generate_index_page()

# Update navigation
generator.update_navigation()
```

### Content Sanitizer

```python
from src.website.sanitizer import sanitize_report_for_web

# Remove private data from report
public_report = sanitize_report_for_web(report)

# Get safe signal summary
summary = get_safe_signal_summary(signal)
```

## Best Practices

1. **Regular Publishing:**
   - Publish after each analysis run to keep site current
   - Use `--build-only` during testing to avoid deploying incomplete content

2. **Content Review:**
   - Review generated markdown before deploying
   - Check that no personal/private information leaked
   - Verify links work correctly

3. **Version Control:**
   - Commit website configuration changes
   - Don't commit `website/site/` (build output)
   - Track `.pages` files for navigation

4. **Performance:**
   - Limit recent reports on index page (default: 10)
   - Consider archiving old reports after 6-12 months
   - Use MkDocs search for large sites

## Future Enhancements

Potential improvements:
- [ ] RSS feed for new reports
- [ ] Email notifications for strong signals
- [ ] Historical performance charts
- [ ] Sector analysis pages
- [ ] Comparison views (e.g., compare tickers)
- [ ] Export to PDF
- [ ] API endpoint for programmatic access

## Support

For issues or questions:
- Check logs: `logs/nordinvest.log`
- Review test suite: `tests/unit/website/`
- GitHub Issues: https://github.com/ironcladgeek/NordInvest/issues
