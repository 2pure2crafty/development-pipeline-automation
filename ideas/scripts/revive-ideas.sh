#!/bin/bash
# Revive the HDS-ideas session after a crash or reboot.
# Called by cron — runs the full startup sequence so the session
# is remotely accessible and self-identifies on start.

SESSION="HDS-ideas"
AGENT_DIR="/var/www/hdp/agents/ideas"
DATE=$(date +%Y-%m-%d)
WINDOW_NAME="HDS-ideas-${DATE}"

# Exit immediately if session is already running
tmux has-session -t "$SESSION" 2>/dev/null && exit 0

# Create session and start Claude
tmux new-session -d -s "$SESSION" -c "$AGENT_DIR"
tmux rename-window -t "${SESSION}:0" "$WINDOW_NAME"
tmux send-keys -t "$SESSION" "claude" Enter

echo "$(date): Started ${SESSION}. Waiting 60s for Claude to initialise..."
sleep 60

# Enable remote control
tmux send-keys -t "$SESSION" "/remote-control" Enter
sleep 5

# Prompt the agent to identify itself
tmux send-keys -t "$SESSION" "Read your CLAUDE.md and introduce yourself — say which agent you are and that you are ready." Enter

echo "$(date): ${SESSION} revived and ready."
