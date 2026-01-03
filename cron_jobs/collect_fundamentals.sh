#!/bin/bash

# FalconSignals Fundamental Data Collection Script
# Usage: ./collect_fundamentals.sh <group_name> [flags]
# Example: ./collect_fundamentals.sh us_tech_software --force
# Example: ./collect_fundamentals.sh us_ai_ml --date 2024-12-01

set -e  # Exit on error

# Dynamically resolve project directory (parent of script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
UV_BIN="$PROJECT_DIR/.venv/bin/uv"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Get group name from argument or default
GROUP="${1:-us_portfolio_balanced_moderate}"

# Build the command
CMD_ARGS=(
    "python" "-m" "src.main"
    "collect-fundamentals"
    "--group" "$GROUP"
)

# Check for additional flags
shift 1 2>/dev/null || shift $# 2>/dev/null  # Remove first arg if it exists
for arg in "$@"; do
    case "$arg" in
        --force|--dry-run)
            CMD_ARGS+=("$arg")
            ;;
        --date)
            CMD_ARGS+=("$arg")
            shift
            CMD_ARGS+=("$1")
            ;;
    esac
done

# Log file with timestamp
LOG_FILE="$LOG_DIR/collect_fundamentals_${GROUP}_$(date +%Y%m%d_%H%M%S).log"

echo "=== Starting fundamental data collection for $GROUP at $(date) ===" >> "$LOG_FILE"
echo "Command: uv run ${CMD_ARGS[*]}" >> "$LOG_FILE"

cd "$PROJECT_DIR"
"$UV_BIN" run "${CMD_ARGS[@]}" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "=== Completed successfully at $(date) ===" >> "$LOG_FILE"
else
    echo "=== Failed with exit code $EXIT_CODE at $(date) ===" >> "$LOG_FILE"
fi

exit $EXIT_CODE
