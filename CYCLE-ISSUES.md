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

**Status:** FIXED (2026-08-21 -- pre-cycle-002 review)

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

**Fix applied:** Added explicit "use the Edit tool, not Bash" instructions to all
pipeline agent CLAUDE.mds (acceptance, dev, features, integration-testing, product,
reviewer, testing-staging, ux-ui). Each pipeline-state.md write call now annotated
with "(use Edit tool)" in the "How you are started" section.

---

### Issue 004 -- Stuck-agent alarm fires but daemon marks pipeline BLOCKED, not monitored

**Status:** FIXED (2026-08-21 -- pre-cycle-002 review)

**Symptom:** When the stuck-agent alarm fired at 00:00, the daemon wrote
`Stage Status: BLOCKED / Waiting For: PATCH` to pipeline-state.md. This is correct
for a genuine blockage, but in the case of Issue 002 (agent idle, not crashed), the
pipeline was not actually blocked -- it just needed a nudge. The state change also
meant the daemon's own heartbeat showed no cycle active, confusing the recovery picture.

**Root cause:** The escalation path always writes BLOCKED, regardless of whether the
agent is alive and idle vs. dead or genuinely stuck.

**Fix applied:** Added a NUDGE_THRESHOLD (30 minutes) before the STUCK_THRESHOLD
(4 hours). If an agent has been IN PROGRESS for more than 30 minutes with no state
change, the daemon sends a startup nudge message to its tmux session. Each (stage,
feature) pair is only nudged once per daemon session. The nudge is cleared when the
state advances. Only if the agent remains stuck after 4 hours total does the daemon
escalate to BLOCKED.

---

### Issue 005 -- Silent pipeline-state.md write failure is systemic, not one-off

**Status:** FIXED (2026-08-21 -- same fix as Issue 003)

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

**Status:** FIXED (2026-08-21 -- pre-cycle-002 review)

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

**Fix applied:** Added "Changeset criteria -- name files, never just count them"
section to acceptance/CLAUDE.md with a Bad/Good example.

---

### Issue 007 -- HDS-ideas cron revival missing /remote-control and startup message

**Status:** FIXED (2026-08-21)

**Symptom:** On a revival after crash or reboot, the HDS-ideas cron restarted Claude
but never sent `/remote-control` or a startup message. The session would be alive but
inaccessible and silent until manually intervened.

**Root cause:** The cron used inline tmux commands (start session, send `claude`, done).
The /remote-control + startup sequence that `start-planning.sh` implements correctly was
never added to the ideas revival path.

**Fix:** Created `scripts/revive-ideas.sh` following the same pattern as
`start-planning.sh`. Updated crontab to call the script instead of inline commands.

**See also:** PITFALLS.md #14.

---

### Issue 008 -- Manual tmux send-keys leaves Enter unregistered when session is transitional

**Status:** FIXED (workaround documented, 2026-08-21)

**Symptom:** When sending startup messages to HDS-features and HDS-overseer via
`tmux send-keys -t SESSION "message" Enter`, the text appeared in the input buffer
but Claude never responded. A second bare Enter was required to actually submit.

**Root cause:** The sessions were in a transitional state (just connected remote-control)
when the message was sent. The Enter keystroke did not register against the input field.
Confirmed via `tmux capture-pane`: message text visible at `❯` with no response below.

**Fix:** Send a bare `tmux send-keys -t SESSION "" Enter` to flush the buffer.
For scripts, use a `sleep 1` between the text send-keys and the Enter send-keys.

**See also:** PITFALLS.md #15.

---

## Improvements backlog (not bugs, but quality-of-life)

- **Daemon log deduplication:** The log file contains duplicate runs from multiple
  daemon restarts all appending to the same file. Consider rotating the log per
  daemon start, or adding a separator line with the PID on startup.

- **State write confirmation:** After any `write_state()` call, read back the file
  and verify the field was updated. Log a warning if not. This would have caught
  Issue 003 immediately.

- **Underseer should send startup nudge before stuck-alarm:** After 30 minutes of
  IN PROGRESS with no change, the underseer could check the tmux pane and send a
  startup message if the agent appears idle. The 4-hour alarm would remain as a
  last resort.

### Issue 008 -- UX/UI agent abandoned its role and corrupted the staging repo branch state

**Status:** FIXED (2026-08-21 -- pre-cycle-002 review)

**Symptom:** The UX/UI agent, instead of doing a visual review on staging, attempted
to run git branch operations and a merge into main. It switched the staging repo from
feature/staging-subdomain-routing to main, leaving docs/archive/ and docs/cycles/ as
untracked blocking files. All pipeline docs (pipeline-state.md, build-queue.md, etc.)
disappeared from the working tree. The merge it attempted also failed due to uncommitted
local changes. Required manual intervention: killed the agent, removed the blocking
untracked dirs, restored the cycle branch, stashed pipeline-state.md, did the merge
manually.

**Root cause:** The UX/UI agent's CLAUDE.md either gives insufficient guidance on
scope boundaries, or the agent hallucinated a responsibility to do the merge. The
merge step is the daemon's job. The UX/UI agent's only job is to look at the site
and confirm no visual regressions.

**Fix applied:**
- Removed the "Merge procedure" section from ux-ui/CLAUDE.md entirely. The daemon
  already handles the merge in `_merge_feature_to_cycle()` when it detects COMPLETE.
- Updated ux-ui "What you do", "Pass condition", and "How you are started" sections
  to remove all references to running git commands. When Patch gives go-ahead, the
  agent updates pipeline-state.md to COMPLETE (via Edit tool) and stops.
- Added "What you must never do" (git prohibition) to ALL pipeline agent CLAUDE.mds:
  acceptance, dev, features, integration-testing, product, reviewer, testing-staging,
  ux-ui. Dev's version permits feature branch operations but prohibits merges and
  checkout of cycle/main branches.

**See also:** Issue 005 (silent state write failure) -- the UX/UI agent also failed
to write pipeline-state.md, consistent with the systemic pattern. Both fixed.

---

- **Integration-testing notable: interest-type commune dispatch differs between
  app.js and index.html.** app.js loadCommune() sets HDS_COMMUNE for interest-type
  communes (cycling, camping, etc.) when accessed via subdomain, but index.html
  inline dispatch shows the national view for these types. Confirmed pre-existing
  intentional design, not a regression from this feature. Worth documenting
  explicitly in platform context so future agents don't flag it as a new finding.
