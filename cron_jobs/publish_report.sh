#!/bin/bash

# NordInvest Publish/Report Script
# Usage: ./publish_report.sh <command>
# Example: ./publish_report.sh publish
#          ./publish_report.sh report

set -e  # Exit on error

# Dynamically resolve project directory (parent of script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
UV_BIN="$PROJECT_DIR/.venv/bin/uv"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Get command from argument
COMMAND="${1}"

# Validate command
if [[ "$COMMAND" != "publish" && "$COMMAND" != "report" ]]; then
    echo "Error: Command must be either 'publish' or 'report'"
    echo "Usage: $0 <publish|report>"
    exit 1
fi

# Get today's date in YYYY-MM-DD format
TODAY=$(date +%Y-%m-%d)

# Log file with timestamp
LOG_FILE="$LOG_DIR/${COMMAND}_$(date +%Y%m%d_%H%M%S).log"

echo "=== Starting $COMMAND for $TODAY at $(date) ===" >> "$LOG_FILE"
echo "Command: uv run python -m src.main $COMMAND --date $TODAY" >> "$LOG_FILE"

cd "$PROJECT_DIR"
"$UV_BIN" run python -m src.main \
    "$COMMAND" \
    --date "$TODAY" \
    >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "=== Completed successfully at $(date) ===" >> "$LOG_FILE"
else
    echo "=== Failed with exit code $EXIT_CODE at $(date) ===" >> "$LOG_FILE"
fi

exit $EXIT_CODE
