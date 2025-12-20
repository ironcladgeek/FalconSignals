#!/usr/bin/env bash
#
# Deploy FalconSignals website to GitHub Pages
#
# Usage:
#   ./scripts/deploy_website.sh [--force] [--no-build]
#
# Options:
#   --force     Force deployment even if there are uncommitted changes
#   --no-build  Skip the build step and deploy existing site/ directory
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEBSITE_DIR="$PROJECT_ROOT/website"

# Parse arguments
FORCE=false
NO_BUILD=false

for arg in "$@"; do
    case $arg in
        --force)
            FORCE=true
            shift
            ;;
        --no-build)
            NO_BUILD=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--force] [--no-build]"
            echo ""
            echo "Deploy FalconSignals website to GitHub Pages"
            echo ""
            echo "Options:"
            echo "  --force     Force deployment even if there are uncommitted changes"
            echo "  --no-build  Skip the build step and deploy existing site/ directory"
            echo "  --help, -h  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 FalconSignals Website Deployment${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Check for uncommitted changes (unless --force)
if [ "$FORCE" = false ]; then
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
        echo "   Commit your changes or use --force to deploy anyway"
        exit 1
    fi
fi

# Check if mkdocs is installed
if ! command -v mkdocs &> /dev/null; then
    echo -e "${RED}❌ Error: mkdocs is not installed${NC}"
    echo "   Install with: uv pip install mkdocs mkdocs-material mkdocs-awesome-pages-plugin"
    exit 1
fi

# Change to website directory
cd "$WEBSITE_DIR"

# Build site if not skipped
if [ "$NO_BUILD" = false ]; then
    echo -e "${BLUE}🔨 Building website...${NC}"
    mkdocs build --clean

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Build failed${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Build successful${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping build step${NC}"

    # Check if site directory exists
    if [ ! -d "site" ]; then
        echo -e "${RED}❌ Error: site/ directory not found${NC}"
        echo "   Run without --no-build to build the site first"
        exit 1
    fi
fi

# Deploy to GitHub Pages
echo -e "${BLUE}🌐 Deploying to GitHub Pages...${NC}"
mkdocs gh-deploy --force --clean

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""
echo -e "${BLUE}🌐 Your website will be available at:${NC}"
echo "   https://ironcladgeek.github.io/FalconSignals/"
echo ""
echo -e "${YELLOW}Note: It may take a few minutes for changes to appear${NC}"
