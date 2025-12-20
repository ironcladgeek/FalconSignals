#!/bin/bash

# FalconSignals Analysis Script
# Usage: ./run_analysis.sh <group_name> [strategy] [flags]
# Example: ./run_analysis.sh us_biotech_genomics momentum --llm

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

# Get strategy from second argument or default
STRATEGY="${2:-momentum}"

# Build the command
CMD_ARGS=(
    "python" "-m" "src.main"
    "analyze"
    "--group" "$GROUP"
    "--strategy" "$STRATEGY"
)

# Check for additional flags
shift 2 2>/dev/null || shift $# 2>/dev/null  # Remove first two args if they exist
for arg in "$@"; do
    case "$arg" in
        --llm|--debug-llm)
            CMD_ARGS+=("$arg")
            ;;
    esac
done

# Log file with timestamp
LOG_FILE="$LOG_DIR/analysis_${GROUP}_$(date +%Y%m%d_%H%M%S).log"

echo "=== Starting analysis for $GROUP with strategy $STRATEGY at $(date) ===" >> "$LOG_FILE"
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
