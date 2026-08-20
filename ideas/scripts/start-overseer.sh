#!/bin/bash
# Start the overseer daemon and create the daemon-enabled flag.
# Called by the ideas agent when Patch wants to start an automation cycle.
# The daemon will not auto-revive after crashes unless this flag exists.

DAEMON_ENABLED_FLAG="/var/www/hdp/agents/overseer/daemon-enabled"
OVERSEER_PY="/var/www/hdp/agents/overseer/overseer.py"
LOG="/var/www/hdp/agents/overseer/overseer.log"

# Check if daemon is already running
if pgrep -f overseer.py > /dev/null; then
    echo "Overseer daemon is already running (PID: $(cat /var/www/hdp/agents/overseer/overseer.pid 2>/dev/null))"
    exit 0
fi

# Create the daemon-enabled flag (enables auto-revival via cron)
touch "$DAEMON_ENABLED_FLAG"
echo "daemon-enabled flag created."

# Start the daemon
python3 "$OVERSEER_PY" >> "$LOG" 2>&1 &
echo "Overseer daemon started (PID: $!)."
echo "Log: tail -f $LOG"
