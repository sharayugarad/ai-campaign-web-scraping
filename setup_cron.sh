#!/bin/bash
# Setup daily cron job for the web page change monitor
# Runs every day at 9:00 AM

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="${SCRIPT_DIR}/venv/bin/python3"
SCRAPER_PATH="${SCRIPT_DIR}/scraper.py"
LOG_PATH="${SCRIPT_DIR}/logs/cron.log"

# Cron expression: minute hour day month weekday
CRON_SCHEDULE="0 9 * * *"
CRON_CMD="${CRON_SCHEDULE} cd ${SCRIPT_DIR} && ${PYTHON_PATH} ${SCRAPER_PATH} >> ${LOG_PATH} 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -qF "$SCRAPER_PATH"; then
    echo "Cron job already exists. Updating..."
    # Remove existing entry
    crontab -l 2>/dev/null | grep -vF "$SCRAPER_PATH" | crontab -
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "Cron job installed successfully!"
echo "Schedule: Daily at 9:00 AM"
echo "Command: ${CRON_CMD}"
echo ""
echo "Verify with: crontab -l"
