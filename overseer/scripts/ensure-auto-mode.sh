#!/bin/bash
# Ensure a Claude Code tmux session is in auto permission mode.
# Usage: ensure-auto-mode.sh <session-name>
#
# After /remote-control activates, cycle through permission modes (shift-tab)
# until "auto mode" appears in the pane. Gives up after 4 attempts so it can
# never get stuck in a loop.

SESSION="$1"

for i in 1 2 3 4; do
    PANE=$(tmux capture-pane -t "$SESSION" -p 2>/dev/null)
    if echo "$PANE" | grep -qi "auto mode"; then
        exit 0
    fi
    tmux send-keys -t "$SESSION" BTab ""
    sleep 1
done
