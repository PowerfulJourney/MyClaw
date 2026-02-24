#!/bin/bash
# Run ClawHub Monitor and send report via Telegram
# This script should be called from cron

WORK_DIR="/home/administrator/.openclaw/workspace/memory/clawhub-monitor"
REPORT_FILE="$WORK_DIR/daily_report.md"
LOG_FILE="$WORK_DIR/notify.log"

# Change to work directory
cd "$WORK_DIR" || exit 1

# Run monitor
echo "[$(date)] Running monitor..." >> "$LOG_FILE"
/usr/bin/python3 monitor.py >> "$LOG_FILE" 2>&1
MONITOR_EXIT=$?

echo "[$(date)] Monitor exit code: $MONITOR_EXIT" >> "$LOG_FILE"

# Check if report was generated
if [ -f "$REPORT_FILE" ]; then
    # For now, just log that report is ready
    # When Gateway is fixed, this can send to Telegram
    echo "[$(date)] Report ready: $REPORT_FILE" >> "$LOG_FILE"
    
    # Display report summary to stdout (for cron email if configured)
    echo "=== ClawHub Monitor Report ==="
    head -20 "$REPORT_FILE"
fi

echo "[$(date)] Done" >> "$LOG_FILE"
