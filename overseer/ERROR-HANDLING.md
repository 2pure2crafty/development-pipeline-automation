# Error Handling -- Overseer Reference

Scenarios the overseer daemon and Claude session need to handle gracefully.

---

## 1. Agent session crash (tmux session dies without updating state)

**Symptom:** pipeline-state.md still shows IN PROGRESS but the tmux session
for that agent no longer exists. The daemon detects this via the stuck-agent
check (4 hours, no state change) OR via tmux has-session returning false.

**Detection:** overseer.py checks agent_session_alive() on each poll when
status is IN PROGRESS. If session is gone and status has not changed:

**Action:**
  - Write escalation.md: "Agent [stage] session died for feature [name]."
  - Set stage_status = BLOCKED, waiting_for = PATCH
  - Do NOT automatically restart: the agent may have partially written files
    and a restart could cause inconsistent state

**Patch action required:**
  - Open the tmux session manually and inspect what happened
  - Check if pipeline-state.md was partially updated
  - Check dev-inbox for any partial output
  - Decide: restart the agent from scratch, or recover manually
  - Restart the daemon after resolving

---

## 2. Token exhaustion (Claude session hits its 5-hour limit mid-task)

**Symptom:** Same as agent session crash -- session ends without a state
update. Indistinguishable from a crash at the overseer level.

**Detection:** Same stuck-agent mechanism (4-hour threshold).

**Action:** Same as #1 above. Patch inspects and restarts.

**Prevention:** The overseer Claude session itself can monitor agent session
age. If an agent session has been running for more than 4 hours, the daemon
writes a WARNING (not escalation) to overseer.log so Patch is aware before
the session actually dies.

---

## 3. Overseer daemon crash or server reboot

**Symptom:** overseer.pid exists but the process is dead. Pipeline stalls.
Agents may finish their work but nothing acts on the state change.

**Detection and auto-restart** -- cron jobs to add (sudo crontab -e):

```bash
# --- Overseer daemon: only revives if daemon-enabled flag exists ---
# Every 5 minutes: restart if dead and flag exists
*/5 * * * * [ -f /var/www/hdp/agents/overseer/daemon-enabled ] && pgrep -f overseer.py > /dev/null || ([ -f /var/www/hdp/agents/overseer/daemon-enabled ] && python3 /var/www/hdp/agents/overseer/overseer.py >> /var/www/hdp/agents/overseer/overseer.log 2>&1 &)

# On reboot: restart daemon only if flag exists (flag persists across reboots)
@reboot sleep 30 && [ -f /var/www/hdp/agents/overseer/daemon-enabled ] && python3 /var/www/hdp/agents/overseer/overseer.py >> /var/www/hdp/agents/overseer/overseer.log 2>&1 &

# --- Ideas agent: always revives, no flag check ---
# Every 5 minutes: restart HDS-ideas session if dead
*/5 * * * * tmux has-session -t HDS-ideas 2>/dev/null || (tmux new-session -d -s HDS-ideas -c /var/www/hdp/agents/ideas/ && tmux rename-window -t HDS-ideas:0 "HDS-ideas-$(date +\%Y-\%m-\%d)" && tmux send-keys -t HDS-ideas "claude" Enter)

# On reboot: always start ideas agent
@reboot sleep 45 && tmux new-session -d -s HDS-ideas -c /var/www/hdp/agents/ideas/ && tmux rename-window -t HDS-ideas:0 "HDS-ideas-$(date +\%Y-\%m-\%d)" && tmux send-keys -t HDS-ideas "claude" Enter
```

Note: the ideas agent revival uses a longer sleep (45s) so it starts after the daemon (30s).

**Recovery:**
  - Daemon reads current pipeline-state.md on startup and resumes from
    wherever it left off. No state is lost: pipeline-state.md is the source
    of truth.
  - Read overseer-restart.md for the state snapshot at the time of the crash.
    It tells you whether an agent session was alive and what to do.

**If Patch needs to manually resume after a reboot:**
  1. Read /var/www/hdp/agents/overseer/overseer-restart.md
  2. Follow the recovery instructions in that file
  3. Start the daemon if it has not auto-restarted

---

## 4. Git operation failure

**Symptom:** merge or branch creation fails (conflict, permissions, network).

**Detection:** overseer.py wraps all git commands in subprocess calls and
checks returncode. On non-zero return: escalate immediately.

**Action:**
  - Write escalation.md with the exact command that failed and stderr output
  - Set stage_status = BLOCKED, waiting_for = PATCH
  - Do not retry git operations automatically (risk of repeated bad state)

**Patch action required:**
  - Resolve the git issue manually
  - Update pipeline-state.md to COMPLETE for the last successful stage
  - Restart the daemon

---

## 5. BLOCKED state (agent-declared)

An agent sets stage_status = BLOCKED when it cannot proceed and the problem
is not a kick-back (e.g. missing external service, infrastructure gap,
ambiguous spec that is not resolvable by the agent).

**Action:** Escalate immediately regardless of autonomy level. Do not retry.

**Patch action required:**
  - Read the agent's output (check dev-inbox or agent workspace)
  - Resolve the blocking issue
  - Set stage_status back to IN PROGRESS (or a specific stage to restart from)
  - Restart the daemon

---

## 6. Build queue is empty at cycle start

**Detection:** read_queue() returns no QUEUED items with resolved dependencies
when the cycle is supposed to start.

**Action:** Do not start. Write to escalation.md: "Build queue has no eligible
QUEUED items. Add features via the overseer Claude session before starting."

---

## 7. Dependency chain broken (quarantine cascades)

When a feature is quarantined, all features with depends_on = that feature's ID
are marked SKIPPED. If SKIPPING those features leaves the queue empty (all
remaining items are COMPLETE, QUARANTINED, or SKIPPED): cycle completes early.

**Action:** Standard cycle-complete procedure (Rule 6 in PIPELINE-LOGIC.md).
The escalation message notes which features were quarantined and skipped.

---

## 8. Partial write to pipeline-state.md

**Symptom:** pipeline-state.md is malformed or contains a partial write
(e.g. power cut during a write).

**Detection:** read_state() returns missing or empty fields.

**Action:**
  - Log the parse error
  - Write escalation.md: "pipeline-state.md appears malformed. Manual
    inspection required."
  - Stop the daemon loop (do not act on incomplete state)

---

## 9. Startup-context.md not found by agent

**Symptom:** An agent starts but has no startup-context.md to read. It
will not know what feature to work on.

**Prevention:** overseer.py always writes startup-context.md BEFORE calling
start_agent(). If write_startup_context() fails, start_agent() is not called.

**If it happens anyway:** the agent's CLAUDE.md tells it to halt and report
if startup-context.md is missing. It sets stage_status = BLOCKED.

---

## Recovery procedure (general)

When Patch resolves any escalation:

1. Fix the underlying issue (code, config, git state, etc.)
2. Verify pipeline-state.md reflects the correct current state
3. Clear or archive the entry in escalation.md
4. Restart the daemon: python3 /var/www/hdp/agents/overseer/overseer.py &
5. Tail the log to confirm it resumes correctly:
     tail -f /var/www/hdp/agents/overseer/overseer.log
