#!/bin/bash
# Start the HDS-planning tmux session with Claude and /remote-control.
# Called by the ideas agent when Patch asks to spin up the planning agent.

SESSION="HDS-planning"
AGENT_DIR="/var/www/hdp/agents/planning"
DATE=$(date +%Y-%m-%d)
WINDOW_NAME="HDS-planning-${DATE}"

# Kill any existing session cleanly
tmux kill-session -t "$SESSION" 2>/dev/null

# Create new session
tmux new-session -d -s "$SESSION" -c "$AGENT_DIR"

# Rename the window to include today's date
tmux rename-window -t "${SESSION}:0" "$WINDOW_NAME"

# Launch Claude
tmux send-keys -t "$SESSION" "claude" Enter

echo "Started ${SESSION} (window: ${WINDOW_NAME}). Waiting 60 seconds for Claude to initialise..."
sleep 60

# Send /remote-control so the session is remotely accessible
tmux send-keys -t "$SESSION" "/remote-control" Enter

# Give remote-control a moment to activate, then prompt the agent to introduce itself
sleep 5
tmux send-keys -t "$SESSION" "Read your CLAUDE.md and introduce yourself." Enter

echo "Done. Attach with: tmux attach -t ${SESSION}"
