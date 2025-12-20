#!/bin/bash

# FalconSignals Price Download Script
# Usage: ./download_prices.sh <group_name>

set -e  # Exit on error

# Dynamically resolve project directory (parent of script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
UV_BIN="$PROJECT_DIR/.venv/bin/uv"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Get group name from argument or default
GROUP="${1:-us_biotech_genomics}"

# Log file with timestamp
LOG_FILE="$LOG_DIR/price_download_${GROUP}_$(date +%Y%m%d_%H%M%S).log"

echo "=== Starting price download for $GROUP at $(date) ===" >> "$LOG_FILE"

cd "$PROJECT_DIR"
"$UV_BIN" run python -m src.main \
    download-prices \
    --group "$GROUP" \
    --force-refresh \
    >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "=== Completed successfully at $(date) ===" >> "$LOG_FILE"
else
    echo "=== Failed with exit code $EXIT_CODE at $(date) ===" >> "$LOG_FILE"
fi

exit $EXIT_CODE
