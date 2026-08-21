#!/usr/bin/env python3
"""
HDS Pipeline Overseer Daemon

Polls pipeline-state.md every 60 seconds and drives the agent pipeline
based on the state machine defined in PIPELINE-LOGIC.md.

Run:  python3 /var/www/hdp/agents/overseer/overseer.py
Stop: Ctrl-C or kill the process (it writes a PID file)

The overseer Claude session (HDS-overseer tmux) is Patch's interface.
This script is the mechanical engine that runs underneath it.
"""

import os
import sys
import time
import subprocess
import datetime
import signal
import json
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

AGENT_ROOT    = Path("/var/www/hdp/agents")
STAGING_DOCS  = Path("/var/www/hdp/staging/docs")
PIPELINE_STATE   = STAGING_DOCS / "pipeline-state.md"
BUILD_QUEUE      = STAGING_DOCS / "build-queue.md"
PRODUCT_BACKLOG  = STAGING_DOCS / "product-backlog.md"
CYCLE_CONFIG     = AGENT_ROOT / "overseer" / "current-config.md"
ESCALATION       = AGENT_ROOT / "overseer" / "escalation.md"
DAEMON_LOG       = AGENT_ROOT / "overseer" / "overseer.log"
PID_FILE         = AGENT_ROOT / "overseer" / "overseer.pid"
RESTART_FILE     = AGENT_ROOT / "overseer" / "overseer-restart.md"
DAEMON_ENABLED   = AGENT_ROOT / "overseer" / "daemon-enabled"
SCRIPTS_DIR      = AGENT_ROOT / "overseer" / "scripts"

# How long (seconds) before sending a nudge to an idle agent
NUDGE_THRESHOLD = 30 * 60  # 30 minutes

# How long (seconds) to wait before flagging a stuck agent (after nudge)
STUCK_THRESHOLD = 4 * 60 * 60  # 4 hours

# Poll interval (seconds)
POLL_INTERVAL = 60

# How many polls between overseer session health checks (10 minutes at 60s/poll)
OVERSEER_SESSION_CHECK_INTERVAL = 10

# Track which (stage, feature) pairs have already been nudged this session.
# Keyed by "stage:feature", value is the timestamp the nudge was sent.
# Cleared when the state advances to a new stage.
_nudge_sent: dict = {}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(DAEMON_LOG, "a") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# Pipeline state parsing
# ---------------------------------------------------------------------------

def read_state() -> dict:
    """Parse pipeline-state.md into a dict of key: value pairs."""
    import re
    state = {}
    if not PIPELINE_STATE.exists():
        return state
    for line in PIPELINE_STATE.read_text().splitlines():
        # Handle bold markdown format: **Key:** value
        m = re.match(r'^\*\*(.+?):\*\*\s*(.*)', line)
        if m:
            state[m.group(1).strip().lower().replace(" ", "_")] = m.group(2).strip()
            continue
        # Handle plain format: Key: value
        if ":" in line and not line.startswith("|") and not line.startswith("#"):
            key, _, val = line.partition(":")
            state[key.strip().lower().replace(" ", "_")] = val.strip()
    return state


def write_state(updates: dict):
    """Overwrite specific fields in pipeline-state.md."""
    if not PIPELINE_STATE.exists():
        log("ERROR: pipeline-state.md not found")
        return
    lines = PIPELINE_STATE.read_text().splitlines()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Build a map of field label -> line index
    new_lines = []
    updated_fields = set()
    for line in lines:
        replaced = False
        for field, value in updates.items():
            # Match lines like "**Current cycle:** something"
            marker = f"**{field.replace('_', ' ').title()}:**"
            if line.strip().startswith(marker.replace("**", "").replace(":", "").strip()) or \
               marker.lower() in line.lower():
                new_lines.append(f"**{field.replace('_', ' ').title()}:** {value}")
                updated_fields.add(field)
                replaced = True
                break
        if not replaced:
            new_lines.append(line)

    # Update Last updated
    result = []
    for line in new_lines:
        if "last updated" in line.lower():
            result.append(f"**Last updated:** {now}")
        else:
            result.append(line)

    PIPELINE_STATE.write_text("\n".join(result) + "\n")


# ---------------------------------------------------------------------------
# Config parsing
# ---------------------------------------------------------------------------

def read_config() -> dict:
    """Parse current-config.md into a dict."""
    config = {}
    if not CYCLE_CONFIG.exists():
        return config
    for line in CYCLE_CONFIG.read_text().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            config[key.strip().lower().replace(" ", "_")] = val.strip()
    return config


# ---------------------------------------------------------------------------
# Build queue
# ---------------------------------------------------------------------------

def read_queue() -> list:
    """Parse build-queue.md table into a list of dicts."""
    items = []
    if not BUILD_QUEUE.exists():
        return items
    for line in BUILD_QUEUE.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ID") or line.startswith("|---"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 4:
            items.append({
                "id": cols[0],
                "feature": cols[1],
                "status": cols[2],
                "depends_on": cols[3],
            })
    return items


def next_queued_item(items: list) -> dict | None:
    """Return the first QUEUED item with no unresolved dependencies."""
    complete_ids = {i["id"] for i in items if i["status"] == "COMPLETE"}
    for item in items:
        if item["status"] != "QUEUED":
            continue
        dep = item["depends_on"].lower()
        if dep in ("none", "tbd", ""):
            return item
        # dep is an ID -- check if it's complete
        dep_id = dep.split()[0]  # "001 Feature name -- reason" -> "001"
        if dep_id in complete_ids:
            return item
    return None


def read_product_backlog() -> list:
    """Parse product-backlog.md table into a list of dicts."""
    items = []
    if not PRODUCT_BACKLOG.exists():
        return items
    for line in PRODUCT_BACKLOG.read_text().splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ID") or line.startswith("|---"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 5:
            items.append({
                "id":          cols[0],
                "description": cols[1],
                "status":      cols[2],
                "source":      cols[3],
                "added":       cols[4],
            })
    return items


def update_product_backlog_status(item_id: str, new_status: str):
    """Update the status column for a given ID in product-backlog.md."""
    if not PRODUCT_BACKLOG.exists():
        return
    lines = PRODUCT_BACKLOG.read_text().splitlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"| {item_id} "):
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 5:
                cols[2] = new_status
                line = "| " + " | ".join(cols) + " |"
        new_lines.append(line)
    PRODUCT_BACKLOG.write_text("\n".join(new_lines) + "\n")


def update_queue_status(feature_id: str, new_status: str):
    """Update the status column for a given feature ID in build-queue.md."""
    if not BUILD_QUEUE.exists():
        return
    lines = BUILD_QUEUE.read_text().splitlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"| {feature_id} "):
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 4:
                cols[2] = new_status
                line = "| " + " | ".join(cols) + " |"
        new_lines.append(line)
    BUILD_QUEUE.write_text("\n".join(new_lines) + "\n")


# ---------------------------------------------------------------------------
# Agent control
# ---------------------------------------------------------------------------

def write_startup_context(agent: str, feature: str, cycle_id: str,
                          cycle_branch: str, kickback_context: str = ""):
    """Write startup-context.md to the agent's directory.

    Each stage receives only the documents relevant to its role.
    Testing and review stages receive no kick-back history so they
    assess the feature with fresh eyes.
    """
    agent_dir = AGENT_ROOT / agent
    ctx_path = agent_dir / "startup-context.md"
    feature_safe = feature.lower().replace(" ", "-")

    spec_path       = "/var/www/hdp/staging/docs/dev-inbox/build-phase.md"
    criteria_path   = f"/var/www/hdp/staging/docs/acceptance/{feature_safe}-criteria.md"
    requirements_path = f"/var/www/hdp/staging/docs/product-requirements/{feature_safe}.md"
    staging_url     = "https://staging.hittadittsverige.se"

    # Stage-specific document pointers.
    # Kick-back context is only passed to agents that are fixing something
    # (dev, features). Testing and review agents receive no history so they
    # judge what is in front of them without bias.
    if agent == "features":
        docs = f"Requirements: {requirements_path}"
        kickback_section = (f"\n## Kick-back context\n\n{kickback_context}\n"
                            if kickback_context else "")
    elif agent == "acceptance":
        docs = (f"Spec:             {spec_path}\n"
                f"Write criteria to: {criteria_path}")
        kickback_section = ""
    elif agent == "dev":
        docs = (f"Spec:          {spec_path}\n"
                f"Criteria:      {criteria_path}\n"
                f"Feature branch: feature/{feature_safe}\n"
                f"Staging URL:   {staging_url}")
        kickback_section = (f"\n## Kick-back context\n\n{kickback_context}\n"
                            if kickback_context else "")
    elif agent == "testing-staging":
        docs = (f"Criteria (primary):  {criteria_path}\n"
                f"Spec (context only): {spec_path}\n"
                f"Staging URL:         {staging_url}")
        kickback_section = ""
    elif agent == "integration-testing":
        docs = (f"Spec:        {spec_path}\n"
                f"Criteria:    {criteria_path}\n"
                f"Staging URL: {staging_url}")
        kickback_section = ""
    elif agent == "reviewer":
        docs = (f"Requirements (primary): {requirements_path}\n"
                f"Spec (secondary):       {spec_path}\n"
                f"Staging URL:            {staging_url}")
        kickback_section = ""
    elif agent == "ux-ui":
        docs = (f"Spec:        {spec_path}\n"
                f"Staging URL: {staging_url}")
        kickback_section = ""
    else:
        docs = (f"Spec:     {spec_path}\n"
                f"Criteria: {criteria_path}")
        kickback_section = (f"\n## Kick-back context\n\n{kickback_context}\n"
                            if kickback_context else "")

    agent_display = agent.replace("-", " ").title()
    ctx = f"""# Startup Context

Agent:        HDS-{agent} ({agent_display} agent)
Feature:      {feature}
Cycle ID:     {cycle_id}
Cycle branch: {cycle_branch}
{docs}
{kickback_section}
Your first output must be a single identification line:
  "HDS-{agent} agent online. Feature: {feature}."

Then read your CLAUDE.md for full instructions and begin your work.
Update pipeline-state.md to IN PROGRESS as your second action.
"""
    ctx_path.write_text(ctx)
    log(f"Wrote startup context for {agent}: feature={feature}, cycle={cycle_id}")


def start_agent(agent: str) -> bool:
    """Start a tmux session for the named agent and launch Claude."""
    session = f"HDS-{agent}"
    agent_dir = str(AGENT_ROOT / agent)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    window_name = f"HDS-{agent}-{today}"

    # Kill any existing session cleanly
    subprocess.run(["tmux", "kill-session", "-t", session],
                   capture_output=True)
    time.sleep(1)

    # Create new session
    result = subprocess.run(
        ["tmux", "new-session", "-d", "-s", session, "-c", agent_dir],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log(f"ERROR: failed to create tmux session {session}: {result.stderr}")
        return False

    # Name the window so it's identifiable at a glance
    subprocess.run(["tmux", "rename-window", "-t", f"{session}:0", window_name],
                   capture_output=True)

    # Launch Claude in auto permission mode
    subprocess.run(["tmux", "send-keys", "-t", session,
                    "claude --permission-mode auto", "Enter"])

    # Startup sequence (runs in background, 60 s after launch):
    # 1. Send /remote-control to activate remote-control mode.
    # 2. Wait 5 s, then run ensure-auto-mode.sh: checks the pane for "auto mode"
    #    and cycles via shift-tab (BTab) until it lands there (max 4 attempts).
    #    Needed because /remote-control can leave the session in a non-auto mode.
    # 3. Wait 2 s, then send the explicit startup message so the agent begins work.
    ensure_script = str(SCRIPTS_DIR / "ensure-auto-mode.sh")
    subprocess.Popen(
        f"sleep 60 && tmux send-keys -t {session} '/remote-control' Enter"
        f" && sleep 5 && bash {ensure_script} {session}"
        f" && sleep 2 && tmux send-keys -t {session}"
        f" 'Read your startup-context.md and begin your work.' Enter",
        shell=True
    )

    log(f"Started agent {agent} in tmux session {session} (window: {window_name})")
    return True


def kill_agent(agent: str):
    """Kill the tmux session for the named agent."""
    session = f"HDS-{agent}"
    result = subprocess.run(["tmux", "kill-session", "-t", session],
                            capture_output=True, text=True)
    if result.returncode == 0:
        log(f"Killed agent {agent} (session {session})")
    else:
        log(f"Note: session {session} was not running (already gone)")


def agent_session_alive(agent: str) -> bool:
    """Return True if the agent's tmux session exists."""
    session = f"HDS-{agent}"
    result = subprocess.run(
        ["tmux", "has-session", "-t", session],
        capture_output=True
    )
    return result.returncode == 0


def tmux_session_alive(session_name: str) -> bool:
    """Return True if a tmux session with this exact name exists."""
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        capture_output=True
    )
    return result.returncode == 0


def ensure_overseer_session():
    """
    Ensure the HDS-overseer tmux session exists with Claude running and
    /remote-control active.
    - tmux session name: HDS-overseer (fixed, no date)
    - tmux window name:  HDS-overseer-YYYY-MM-DD (dated, for identification)
    Called on daemon startup and every OVERSEER_SESSION_CHECK_INTERVAL polls.
    """
    session = "HDS-overseer"
    if tmux_session_alive(session):
        return  # Already running, nothing to do

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    window_name = f"HDS-overseer-{date_str}"
    overseer_dir = str(AGENT_ROOT / "overseer")
    log(f"HDS-overseer session not found. Starting (window: {window_name}).")

    result = subprocess.run(
        ["tmux", "new-session", "-d", "-s", session, "-c", overseer_dir],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log(f"WARNING: could not create HDS-overseer: {result.stderr}")
        return

    # Rename the window to include today's date
    subprocess.run(["tmux", "rename-window", "-t", f"{session}:0", window_name])

    # Launch Claude in auto permission mode
    subprocess.run(["tmux", "send-keys", "-t", session,
                    "claude --permission-mode auto", "Enter"])

    # Wait for Claude to fully initialise before sending the remote-control command
    time.sleep(60)
    subprocess.run(["tmux", "send-keys", "-t", session, "/remote-control", "Enter"])
    subprocess.run(["tmux", "send-keys", "-t", session, "", "Enter"])

    log(f"HDS-overseer started (window: {window_name}) with /remote-control.")


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------

def escalate(reason: str, detail: str = ""):
    """Write an escalation notice and log it. Patch must intervene."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## Escalation -- {now}\n\n**Reason:** {reason}\n"
    if detail:
        entry += f"\n{detail}\n"
    entry += "\n**Status:** AWAITING PATCH\n"

    with open(ESCALATION, "a") as f:
        f.write(entry)

    write_state({
        "stage_status": "BLOCKED",
        "waiting_for": "PATCH",
    })
    log(f"ESCALATION: {reason}")


# ---------------------------------------------------------------------------
# Nudge helper
# ---------------------------------------------------------------------------

def _nudge_agent(stage: str, feature: str):
    """Send a startup nudge to an agent that appears idle."""
    key = f"{stage}:{feature}"
    if key in _nudge_sent:
        return  # already nudged this session; wait for stuck alarm
    session = f"HDS-{stage}"
    msg = "Read your startup-context.md and begin your work."
    result = subprocess.run(
        ["tmux", "send-keys", "-t", session, msg, "Enter"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        _nudge_sent[key] = time.time()
        log(f"NUDGE: sent startup message to {session} for feature '{feature}' "
            f"(IN PROGRESS for >{NUDGE_THRESHOLD//60} min with no state change)")
    else:
        log(f"NUDGE: failed to reach {session} -- session may not exist")


def _clear_nudge(stage: str, feature: str):
    """Clear nudge state when the pipeline advances past this stage."""
    _nudge_sent.pop(f"{stage}:{feature}", None)


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

# Stage order for the pipeline
PIPELINE_STAGES = [
    "features",
    "acceptance",
    "dev",
    "testing-staging",
    "integration-testing",
    "reviewer",
    "ux-ui",
]

# Which agents get kicked back to on a kick-back from each stage
KICKBACK_TARGET = {
    "testing-staging":    "dev",
    "integration-testing": "dev",
    "reviewer":           "features",
    "ux-ui":              "dev",
}


def next_stage(current_stage: str) -> str | None:
    """Return the stage that follows the current one, or None if ux-ui."""
    try:
        idx = PIPELINE_STAGES.index(current_stage)
        return PIPELINE_STAGES[idx + 1] if idx + 1 < len(PIPELINE_STAGES) else None
    except ValueError:
        return None


def handle_state(state: dict, config: dict, items: list,
                 last_state_change: float) -> float:
    """
    Core state machine. Reads state, decides action, returns updated
    last_state_change timestamp (reset when action taken).
    """
    stage   = state.get("current_stage", "none").strip()
    status  = state.get("stage_status", "idle").strip().upper()
    feature = state.get("current_feature", "").strip()
    cycle   = state.get("current_cycle", "").strip()
    branch  = state.get("current_branch", "").strip()
    level   = int(config.get("autonomy_level", "1"))
    kickbacks = int(state.get("kick-back_count", "0").split()[0]
                    if state.get("kick-back_count") else "0")

    # --- IDLE: start from build-queue if possible, then product-backlog (level 5) ---
    if status == "IDLE" or stage in ("none", ""):
        items = read_queue()
        next_item = next_queued_item(items)
        if next_item:
            _start_feature(next_item, cycle, config, level)
            return time.time()
        if level >= 5:
            pb_items = read_product_backlog()
            next_pb = next((i for i in pb_items if i["status"] == "QUEUED"), None)
            if next_pb:
                log(f"Level 5: build-queue empty, processing product-backlog item: {next_pb['description']}")
                _start_product_agent(next_pb, cycle, config)
                return time.time()
        return last_state_change

    # --- Level 5: product stage COMPLETE -- start dev pipeline on resulting queue items ---
    if stage == "product" and status == "COMPLETE":
        kill_agent("product")
        items = read_queue()
        next_item = next_queued_item(items)
        if next_item:
            log(f"Level 5: product agent complete. Starting pipeline for: {next_item['feature']}")
            _start_feature(next_item, cycle, config, level)
        else:
            # Before declaring cycle complete, check for features already active in the pipeline.
            # A race can occur where the product agent writes COMPLETE to pipeline-state.md after
            # the daemon has already called _start_feature for the item it produced -- the second
            # poll then sees product/COMPLETE again but the item is now ACTIVE, not QUEUED.
            active_items = [i for i in items if i["status"] == "ACTIVE"]
            if active_items:
                log(f"Level 5: product agent complete but features still active: "
                    f"{[i['feature'] for i in active_items]}. Monitoring.")
            else:
                log("Level 5: product agent complete but no QUEUED or ACTIVE items. Checking backlog.")
                pb_items = read_product_backlog()
                next_pb = next((i for i in pb_items if i["status"] == "QUEUED"), None)
                if next_pb:
                    _start_product_agent(next_pb, cycle, config)
                else:
                    _cycle_complete(cycle, config)
        return time.time()

    # --- Check for idle/stuck agent ---
    elapsed = time.time() - last_state_change
    if status == "IN PROGRESS":
        if elapsed > STUCK_THRESHOLD:
            escalate(
                f"Agent {stage} has been IN PROGRESS for {elapsed/3600:.1f} hours "
                f"with no state update.",
                f"Feature: {feature}\nSession: HDS-{stage}\n"
                f"Check the tmux session and investigate."
            )
            return time.time()
        elif elapsed > NUDGE_THRESHOLD:
            _nudge_agent(stage, feature)

    # --- COMPLETE: advance to next stage ---
    if status == "COMPLETE":
        nxt = next_stage(stage)

        if stage == "ux-ui":
            # Feature fully passed pipeline
            if level >= 4:
                _clear_nudge(stage, feature)
                log(f"Feature '{feature}' passed ux-ui. Merging into cycle branch.")
                _merge_feature_to_cycle(feature, branch, cycle)
                _housekeeping(feature, cycle, items)
                updated_items = read_queue()
                next_item = next_queued_item(updated_items)
                if next_item:
                    _start_feature(next_item, cycle, config, level)
                elif level >= 5:
                    pb_items = read_product_backlog()
                    next_pb = next((i for i in pb_items if i["status"] == "QUEUED"), None)
                    if next_pb:
                        log(f"Level 5: build-queue empty after feature. Processing next product-backlog item.")
                        _start_product_agent(next_pb, cycle, config)
                    else:
                        _cycle_complete(cycle, config)
                else:
                    _cycle_complete(cycle, config)
            else:
                # Level 3: report to Patch, wait
                escalate(
                    f"Feature '{feature}' has passed ux-ui and is ready to merge.",
                    "Merge the feature branch into the cycle branch and confirm "
                    "to continue, or stop the cycle."
                )
            return time.time()

        # Advance to next stage
        if level >= 3 or (level == 2):
            _clear_nudge(stage, feature)
            kill_agent(stage)
            log(f"Stage {stage} COMPLETE. Advancing to {nxt}.")
            write_startup_context(nxt, feature, cycle, branch)
            write_state({
                "current_stage": nxt,
                "stage_status": "IN PROGRESS",
                "waiting_for": nxt,
                "kick-back_count": "0",
            })
            start_agent(nxt)
            return time.time()

        elif level == 2:
            # Level 2: report to Patch and wait for go-ahead
            escalate(
                f"Stage {stage} complete for '{feature}'. "
                f"Next stage: {nxt}. Awaiting your go-ahead.",
            )
            return time.time()

    # --- KICKED BACK ---
    if status == "KICKED BACK":
        if kickbacks >= 2:
            # Double kick-back: quarantine
            log(f"Double kick-back on '{feature}' at stage {stage}. Quarantining.")
            update_queue_status(_feature_id(feature, items), "QUARANTINED")
            _mark_dependents_skipped(feature, items)
            _reset_cycle_branch_to_pre_feature(branch, cycle)
            escalate(
                f"Feature '{feature}' quarantined after double kick-back at stage {stage}.",
                f"The feature branch has been reset. Dependent features are marked SKIPPED.\n"
                f"Remaining eligible features will continue if any exist."
            )
            # Try to continue with other features
            updated_items = read_queue()
            next_item = next_queued_item(updated_items)
            if next_item and level >= 4:
                _start_feature(next_item, cycle, config, level)
            elif not next_item and level >= 5:
                pb_items = read_product_backlog()
                next_pb = next((i for i in pb_items if i["status"] == "QUEUED"), None)
                if next_pb:
                    log("Level 5: no eligible build-queue items after quarantine. Processing next product-backlog item.")
                    _start_product_agent(next_pb, cycle, config)
                else:
                    _cycle_complete(cycle, config)
            return time.time()

        # First or second kick-back: send to appropriate target agent
        target = KICKBACK_TARGET.get(stage)
        if target:
            _clear_nudge(stage, feature)
            kickback_file = _kickback_file_for(stage)
            kill_agent(stage)
            log(f"Kick-back from {stage}. Sending to {target}. Count: {kickbacks}")
            write_startup_context(target, feature, cycle, branch,
                                  kickback_context=f"Kick-back from {stage}.\n"
                                  f"See: {kickback_file}\nKick-back count: {kickbacks}")
            write_state({
                "current_stage": target,
                "stage_status": "IN PROGRESS",
                "waiting_for": target,
            })
            start_agent(target)
        else:
            escalate(f"Kick-back from {stage} but no target agent defined.",
                     f"Feature: {feature}")
        return time.time()

    return last_state_change


# ---------------------------------------------------------------------------
# Helper actions
# ---------------------------------------------------------------------------

def _feature_id(feature_name: str, items: list) -> str:
    for item in items:
        if item["feature"].lower() == feature_name.lower():
            return item["id"]
    return ""


def _kickback_file_for(stage: str) -> str:
    mapping = {
        "testing-staging":    "/var/www/hdp/staging/docs/dev-inbox/acceptance-fixes.md",
        "integration-testing": "/var/www/hdp/staging/docs/dev-inbox/integration-fixes.md",
        "reviewer":           "/var/www/hdp/staging/docs/dev-inbox/reviewer-feedback.md",
        "ux-ui":              "/var/www/hdp/staging/docs/dev-inbox/ux-fixes.md",
    }
    return mapping.get(stage, "see agent output")


def _start_product_agent(pb_item: dict, cycle: str, config: dict):
    """Mark a product-backlog item ACTIVE and start the product agent (level 5)."""
    update_product_backlog_status(pb_item["id"], "ACTIVE")
    write_state({
        "current_stage":   "product",
        "stage_status":    "IN PROGRESS",
        "waiting_for":     "product",
        "kick-back_count": "0",
    })
    # Write startup context for the product agent
    agent_dir = AGENT_ROOT / "product"
    ctx = f"""# Startup Context -- Level 5 Product Agent Run

Product backlog item ID: {pb_item["id"]}
Description: {pb_item["description"]}
Source: {pb_item["source"]}

Your task:
1. Read the description above
2. Read /var/www/hdp/staging/docs/product-backlog.md for any additional context
3. Produce a clear product requirement (what, why, success criteria, out of scope)
4. Write the requirement as a row in /var/www/hdp/staging/docs/build-queue.md
   Status: QUEUED, Depends-on: none
5. Mark this product-backlog item COMPLETE in product-backlog.md
6. Update pipeline-state.md: Stage status = COMPLETE

Read your CLAUDE.md for full instructions.
"""
    (agent_dir / "startup-context.md").write_text(ctx)
    start_agent("product")
    log(f"Level 5: started product agent for: {pb_item['description']}")


def shutdown_daemon():
    """
    Cleanly shut down the overseer daemon and remove the daemon-enabled flag.
    Called by the overseer Claude session when a cycle completes successfully.
    Run this via: python3 -c "from overseer import shutdown_daemon; shutdown_daemon()"
    Or simply: kill $(cat /var/www/hdp/agents/overseer/overseer.pid)
              rm /var/www/hdp/agents/overseer/daemon-enabled
    """
    DAEMON_ENABLED.unlink(missing_ok=True)
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            log(f"Daemon shutdown requested (PID {pid}). daemon-enabled flag removed.")
        except ProcessLookupError:
            log("Daemon was not running. daemon-enabled flag removed.")
    else:
        log("No PID file found. daemon-enabled flag removed.")


def _start_feature(item: dict, cycle: str, config: dict, level: int):
    """Mark an item ACTIVE and kick off the features agent."""
    feature = item["feature"]
    feature_safe = feature.lower().replace(" ", "-")
    branch = f"feature/{feature_safe}"
    update_queue_status(item["id"], "ACTIVE")
    write_state({
        "current_feature": feature,
        "current_branch":  branch,
        "current_stage":   "features",
        "stage_status":    "IN PROGRESS",
        "waiting_for":     "features",
        "kick-back_count": "0",
    })
    write_startup_context("features", feature, cycle, branch)
    start_agent("features")
    log(f"Started feature '{feature}' (ID: {item['id']}) at cycle {cycle}")


def _merge_feature_to_cycle(feature: str, branch: str, cycle: str):
    """Merge the feature branch into the cycle branch."""
    cycle_branch = f"autonomous/{cycle}"
    staging = "/var/www/hdp/staging"
    cmds = [
        ["sudo", "-u", "hdp", "git", "-C", staging, "checkout", cycle_branch],
        ["sudo", "-u", "hdp", "git", "-C", staging, "merge", branch,
         "--no-ff", "-m", f"Merge {branch} into {cycle_branch}"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            escalate(f"Git merge failed: {' '.join(cmd)}",
                     result.stderr)
            return
    log(f"Merged {branch} into {cycle_branch}")


def _housekeeping(feature: str, cycle: str, items: list):
    """Mark feature COMPLETE in queue and update cycle doc."""
    fid = _feature_id(feature, items)
    if fid:
        update_queue_status(fid, "COMPLETE")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    cycle_doc = STAGING_DOCS / "cycles" / f"{cycle}-active.md"
    if cycle_doc.exists():
        with open(cycle_doc, "a") as f:
            f.write(f"\n- [{now}] COMPLETE: {feature}\n")
    log(f"Housekeeping complete for feature '{feature}'")


def _mark_dependents_skipped(quarantined_feature: str, items: list):
    """Mark any features that depend on the quarantined feature as SKIPPED."""
    fid = _feature_id(quarantined_feature, items)
    if not fid:
        return
    for item in items:
        dep = item["depends_on"].split()[0] if item["depends_on"] else ""
        if dep == fid and item["status"] == "QUEUED":
            update_queue_status(item["id"], "SKIPPED")
            log(f"Skipped feature '{item['feature']}' (depends on quarantined {fid})")


def _reset_cycle_branch_to_pre_feature(branch: str, cycle: str):
    """Remove the quarantined feature branch. Cycle branch is unaffected."""
    staging = "/var/www/hdp/staging"
    cycle_branch = f"autonomous/{cycle}"
    cmds = [
        ["sudo", "-u", "hdp", "git", "-C", staging, "checkout", cycle_branch],
        ["sudo", "-u", "hdp", "git", "-C", staging, "branch", "-D", branch],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"Warning: git command failed: {' '.join(cmd)}: {result.stderr}")
    log(f"Reset: deleted branch {branch}, back on {cycle_branch}")


def _cycle_complete(cycle: str, config: dict):
    """Build queue is empty. Report to Patch."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    cycle_doc = STAGING_DOCS / "cycles" / f"{cycle}-active.md"
    if cycle_doc.exists():
        with open(cycle_doc, "a") as f:
            f.write(f"\n## Cycle complete\n\nCompleted: {now}\n"
                    f"All queued features built and passed the pipeline.\n"
                    f"Awaiting Patch review and merge into staging main.\n")
    write_state({
        "stage_status": "IDLE",
        "waiting_for":  "PATCH",
        "current_stage": "none",
    })
    escalate(
        f"Cycle {cycle} complete. All features built and passed the pipeline.",
        "Awaiting your review. Merge the cycle branch into staging main when ready."
    )
    log(f"Cycle {cycle} complete.")


# ---------------------------------------------------------------------------
# Heartbeat -- crash recovery snapshot
# ---------------------------------------------------------------------------

def write_heartbeat(state: dict, config: dict):
    """
    Write overseer-restart.md every poll. After a server crash, any Claude
    session can read this file to understand exactly what was happening and
    what to do to resume.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pid = os.getpid()

    stage   = state.get("current_stage", "none")
    status  = state.get("stage_status", "IDLE")
    feature = state.get("current_feature", "none")
    cycle   = state.get("current_cycle", "none")
    branch  = state.get("current_branch", "none")
    level   = config.get("autonomy_level", "not set")
    stop    = config.get("stop_condition", "not set")

    no_cycle = stage in ("none", "") or status.upper() == "IDLE"

    if no_cycle:
        active_section = "**No active cycle.** The pipeline is idle.\n"
        recovery_steps = (
            "No cycle was running when the daemon stopped.\n"
            "Simply start the daemon and it will wait for your instruction:\n\n"
            "  python3 /var/www/hdp/agents/overseer/overseer.py &\n"
        )
    else:
        # Check if the pipeline agent session is alive
        session = f"HDS-{stage}"
        alive = agent_session_alive(stage)
        session_status = "ALIVE" if alive else "DEAD (session not found)"

        active_section = f"""**Active cycle detected.**

Cycle ID:        {cycle}
Autonomy level:  {level}
Stop condition:  {stop}
Cycle branch:    {branch}

Current feature: {feature}
Current stage:   {stage}
Stage status:    {status}
Agent session:   {session} -- {session_status}
"""
        if alive:
            recovery_steps = (
                f"The agent session {session} is still alive. The agent may still\n"
                f"be working. Start the daemon and it will resume monitoring:\n\n"
                f"  python3 /var/www/hdp/agents/overseer/overseer.py &\n\n"
                f"Tail the log to confirm:\n"
                f"  tail -f /var/www/hdp/agents/overseer/overseer.log\n"
            )
        else:
            recovery_steps = (
                f"The agent session {session} is NOT running. The agent's session\n"
                f"died without updating pipeline-state.md (crash or token exhaustion).\n\n"
                f"This is an error scenario. Read ERROR-HANDLING.md scenario #1.\n\n"
                f"Short version:\n"
                f"  1. Check {stage} agent workspace for partial output\n"
                f"  2. Check /var/www/hdp/staging/docs/dev-inbox/ for partial writes\n"
                f"  3. Decide: restart the agent from scratch, or recover manually\n"
                f"  4. If restarting from scratch: update pipeline-state.md to reflect\n"
                f"     where you want to restart from\n"
                f"  5. Start the daemon: python3 /var/www/hdp/agents/overseer/overseer.py &\n"
            )

    content = f"""# Overseer State -- Last Heartbeat

**Written:** {now}
**Daemon PID:** {pid}
**This file is overwritten every 60 seconds by the daemon.**

---

## Current State

{active_section}
---

## Recovery Instructions

If you are reading this after a server crash, daemon crash, or unexpected stop:

{recovery_steps}
---

## Key files to check

  /var/www/hdp/staging/docs/pipeline-state.md   (current pipeline state)
  /var/www/hdp/agents/overseer/current-config.md (cycle configuration)
  /var/www/hdp/agents/overseer/escalation.md     (any pending escalations)
  /var/www/hdp/agents/overseer/overseer.log      (daemon activity log)
  /var/www/hdp/staging/docs/build-queue.md       (feature queue)

---

## Daemon commands

Start:  python3 /var/www/hdp/agents/overseer/overseer.py &
Stop:   kill $(cat /var/www/hdp/agents/overseer/overseer.pid)
Status: ps aux | grep overseer.py
Log:    tail -f /var/www/hdp/agents/overseer/overseer.log
"""
    RESTART_FILE.write_text(content)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    # Write PID file
    PID_FILE.write_text(str(os.getpid()))
    log("Overseer daemon started.")

    # Handle clean shutdown
    def shutdown(sig, frame):
        log("Overseer daemon stopping.")
        PID_FILE.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    last_state_change = time.time()
    poll_count = 0

    # Ensure the overseer Claude session exists immediately on startup
    ensure_overseer_session()

    while True:
        try:
            state  = read_state()
            config = read_config()
            items  = read_queue()

            write_heartbeat(state, config)

            last_state_change = handle_state(
                state, config, items, last_state_change
            )

            # Periodically ensure the overseer Claude session is still alive
            poll_count += 1
            if poll_count % OVERSEER_SESSION_CHECK_INTERVAL == 0:
                ensure_overseer_session()

        except Exception as e:
            tb = traceback.format_exc()
            log(f"ERROR in main loop: {e}\n{tb}")
            escalate("Overseer daemon encountered an unhandled exception.",
                     f"{e}\n\n{tb}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
