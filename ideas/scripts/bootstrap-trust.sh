#!/bin/bash
# One-time setup: pre-initialise each agent directory so Claude Code doesn't
# show a "trust this folder?" prompt when the pipeline starts sessions automatically.
#
# Run this once manually from your terminal:
#   bash /var/www/hdp/agents/ideas/scripts/bootstrap-trust.sh

AGENT_DIRS=(
  /var/www/hdp/agents/overseer
  /var/www/hdp/agents/product
  /var/www/hdp/agents/planning
  /var/www/hdp/agents/features
  /var/www/hdp/agents/acceptance
  /var/www/hdp/agents/dev
  /var/www/hdp/agents/testing-staging
  /var/www/hdp/agents/integration-testing
  /var/www/hdp/agents/reviewer
  /var/www/hdp/agents/ux-ui
  /var/www/hdp/agents/deploy
)

echo "Bootstrapping Claude trust for all agent directories..."
echo ""

for dir in "${AGENT_DIRS[@]}"; do
  echo -n "  $dir ... "
  cd "$dir" || { echo "SKIP (directory not found)"; continue; }
  claude --print "ready" > /dev/null 2>&1
  echo "done"
done

echo ""
echo "All directories initialised. The pipeline can now start sessions without prompts."
