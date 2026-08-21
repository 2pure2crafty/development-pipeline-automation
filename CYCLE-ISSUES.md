# Cycle Issues Log

Issues encountered during live pipeline runs. Each entry records what broke,
what the root cause was, what the fix was, and whether it's been applied.

Status values: FIXED | OPEN | DEFERRED

---

## Cycle 001 -- 2026-08-20 to present

### Issue 001 -- Daemon declares cycle complete while features agent is active

**Status:** FIXED (deployed in commit fd17068)

**Symptom:** At 19:30 the daemon logged "Cycle cycle-001 complete" and escalated
to Patch, even though the features agent had been running for less than 60 seconds.

**Root cause:** The `product/COMPLETE` handler checks `next_queued_item()` to see
if there is more work. After `_start_feature()` updates the build-queue item from
QUEUED to ACTIVE, `next_queued_item()` returns None (it only looks for QUEUED items).
The handler then fell through to `_cycle_complete()` without checking whether any
items were already ACTIVE. A secondary cause: the product agent's final write to
pipeline-state.md landed after the daemon had already written `features / IN PROGRESS`,
resetting it to `product / COMPLETE` and causing the handler to re-run.

Also fixed in the same commit: `next_item['name']` KeyError (should be `next_item['feature']`)
in the success path of the same handler.

**Fix:** Before calling `_cycle_complete()`, check for ACTIVE items in the build queue.
If any exist, log and return -- the pipeline is still running.

**See also:** PITFALLS.md #12.

---

### Issue 002 -- Pipeline agents idle after /remote-control with no startup message

**Status:** FIXED (deployed in commit a643af5)

**Symptom:** The acceptance agent started at 20:00, received /remote-control, then
sat completely idle for 4 hours until the stuck-agent alarm fired.

**Root cause:** `start_agent()` sends `/remote-control` followed by a blank Enter.
The blank Enter is not a reliable trigger for Claude to read its CLAUDE.md and begin
work. Some agents start correctly (possibly timing-dependent), others do not.

**Fix:** After `/remote-control`, send an explicit message 5 seconds later:
"Read your startup-context.md and begin your work." This always triggers the agent.

**See also:** PITFALLS.md #13.

---

### Issue 003 -- Agent pipeline-state.md write fails silently; agent reports success

**Status:** OPEN

**Symptom:** The acceptance agent's tmux pane showed "Pipeline state set to COMPLETE"
at 04:55, but pipeline-state.md still showed `BLOCKED / WAITING FOR PATCH` from the
00:00 escalation. The daemon did not advance to dev. Overseer corrected it manually.

**Root cause (likely):** The acceptance agent attempted to update pipeline-state.md
using a Bash command (e.g. sed or echo) rather than the Edit tool. Its settings.json
allows `Write(/var/www/hdp/staging/docs/**)` but only allows specific Bash commands
(git, curl, find, grep, ls, cat, head, tail). A sed/echo write would be blocked by
the auto-mode classifier. The agent then reported success based on its CLAUDE.md
instruction text rather than a confirmed write result.

**Fix candidates:**
- Add `Bash(sed *)` and `Bash(python3 *)` to acceptance agent allow list (broad)
- Add explicit instructions in acceptance CLAUDE.md: "use the Edit tool, not Bash, to
  update pipeline-state.md" (targeted)
- Have the daemon own all pipeline-state.md writes; agents only write their own output
  files and set a simple flag file to signal COMPLETE (architectural)
- The daemon already monitors the output file existence (criteria doc); could infer
  COMPLETE from that rather than relying on agent self-reporting (resilient)

**Recommended fix:** Both the targeted CLAUDE.md instruction AND the daemon inferring
COMPLETE from output file existence as a fallback. Belt and braces.

**Action needed:** Update acceptance CLAUDE.md and relevant agent CLAUDE.mds;
investigate whether other agents have the same Bash restriction.

---

### Issue 004 -- Stuck-agent alarm fires but daemon marks pipeline BLOCKED, not monitored

**Status:** OPEN

**Symptom:** When the stuck-agent alarm fired at 00:00, the daemon wrote
`Stage Status: BLOCKED / Waiting For: PATCH` to pipeline-state.md. This is correct
for a genuine blockage, but in the case of Issue 002 (agent idle, not crashed), the
pipeline was not actually blocked -- it just needed a nudge. The state change also
meant the daemon's own heartbeat showed no cycle active, confusing the recovery picture.

**Root cause:** The escalation path always writes BLOCKED, regardless of whether the
agent is alive and idle vs. dead or genuinely stuck.

**Fix candidates:**
- Add a separate `Stage Status: NUDGE NEEDED` state that the overseer can resolve
  by sending a startup message (keeps the pipeline status accurate)
- Have the overseer check tmux session state before writing BLOCKED: if session is alive
  and /remote-control is active, send a startup nudge before escalating
- Keep BLOCKED but have the daemon continue monitoring so it picks up COMPLETE when
  the agent eventually finishes (rather than requiring manual state correction)

**Action needed:** Design decision needed before implementation.

---

### Issue 005 -- Silent pipeline-state.md write failure is systemic, not one-off

**Status:** OPEN (same root cause as Issue 003)

**Symptom:** testing-staging agent completed its run and wrote its kick-back report
to acceptance-fixes.md, but did not update pipeline-state.md to KICKED BACK. Overseer
corrected manually (pattern now established as recurring).

**Root cause:** Same as Issue 003. Agents are consistently failing to update
pipeline-state.md, likely because they use a Bash command the allow list blocks.
This has now happened in three stages: acceptance, dev (twice), testing-staging.

**Fix needed:** Issue 003 fix candidates still apply. Priority is increasing -- this
is happening every stage.

---

### Issue 006 -- Count-based changeset criteria cause false failures and poor diagnostics

**Status:** OPEN (process/design issue)

**Symptom:** AC-021 said "exactly 2 files changed." The dev agent's kick-back fix
for AC-016/017/018 required touching index.html, making it 3 files. AC-021 failed
again on the second testing-staging run, even though the 3-file changeset is correct.
The count criterion also gave the testing agent no way to identify WHICH file was
unexpected -- it could only report a number.

**Root cause:** The acceptance agent wrote count-based criteria ("exactly N files")
instead of name-based criteria ("only these files: X, Y"). Count-based criteria:
- Cannot distinguish a legitimate extra file from an unintended one
- Become invalid when a kick-back fix legitimately expands scope
- Give no diagnostic information ("3 files" vs. "unexpected file: index.html")

**Fix:** The acceptance agent's CLAUDE.md should instruct it to name specific files
in changeset criteria wherever possible, not just count them. Instead of:
  "Exactly two files changed, no other files."
Write:
  "Only `public_html/api/_helpers.php` and `public_html/assets/app.js` are modified.
   Any other changed file is unexpected and must be justified."

This gives testing agents (and the overseer) a clear basis for distinguishing a
legitimate scope expansion from an unintended change -- and flags when the expected
files themselves are named correctly.

**Action needed:** Update acceptance agent CLAUDE.md with this guidance. Apply
retrospectively by having the acceptance agent revise AC-021 before the next
testing-staging run.

---

## Improvements backlog (not bugs, but quality-of-life)

- **Daemon log deduplication:** The log file contains duplicate runs from multiple
  daemon restarts all appending to the same file. Consider rotating the log per
  daemon start, or adding a separator line with the PID on startup.

- **State write confirmation:** After any `write_state()` call, read back the file
  and verify the field was updated. Log a warning if not. This would have caught
  Issue 003 immediately.

- **Overseer should send startup nudge before stuck-alarm:** After 30 minutes of
  IN PROGRESS with no change, the overseer could check the tmux pane and send a
  startup message if the agent appears idle. The 4-hour alarm would remain as a
  last resort.
