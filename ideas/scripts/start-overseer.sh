#!/bin/bash
# Start the overseer daemon and create the daemon-enabled flag.
# Called by the ideas agent when Patch wants to start an automation cycle.
# The daemon will not auto-revive after crashes unless this flag exists.

DAEMON_ENABLED_FLAG="/var/www/hdp/agents/overseer/daemon-enabled"
OVERSEER_PY="/var/www/hdp/agents/overseer/overseer.py"
LOG="/var/www/hdp/agents/overseer/overseer.log"

# Check if daemon is already running
if pgrep -f "python3.*overseer.py" > /dev/null; then
    echo "Overseer daemon is already running (PID: $(cat /var/www/hdp/agents/overseer/overseer.pid 2>/dev/null))"
    exit 0
fi

# Create the daemon-enabled flag (enables auto-revival via cron)
touch "$DAEMON_ENABLED_FLAG"
echo "daemon-enabled flag created."

# Start the daemon with the hdp group active so it can write to group-owned staging files.
# If sg fails (e.g. first login before group takes effect), this will error -- log out/in first.
sg hdp -c "python3 '$OVERSEER_PY' >> '$LOG' 2>&1 &"
sleep 1
DAEMON_PID=$(pgrep -f "python3.*overseer.py" | head -1)
echo "Overseer daemon started (PID: ${DAEMON_PID})."
echo "Log: tail -f $LOG"
