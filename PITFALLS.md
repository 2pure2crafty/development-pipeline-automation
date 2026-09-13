# DPA Pitfalls and Setup Notes

Things that bit us during the initial setup of the HDS Development Pipeline
Automation. Read this before spinning up the DPA on a new project.

---

## 1. File ownership and the daemon user

**Problem:** The underseer daemon writes to files in two different places:
- Its own working files (PID file, log, daemon-enabled flag) in `agents/overseer/`
- Shared staging docs (pipeline-state.md, build-queue.md, etc.) in `staging/docs/`

If those two locations are owned by different users, the daemon can only run
cleanly as one of them — and whichever you pick breaks the other.

A second constraint: the daemon creates tmux sessions. tmux sessions are
per-user — if the daemon runs as user A, it creates sessions in A's tmux
server, and user B cannot attach to them.

**Fix:** Run the daemon as the same user who owns the tmux sessions (the
human operator). Give that user write access to staging docs via group
membership.

```bash
sudo usermod -a -G hdp patch          # add operator to the file-owning group
sudo chmod -R g+w /var/www/hdp/staging/docs/   # make docs group-writable
```

Log out and back in for group membership to take effect. The daemon then
runs as `patch` and can write everything, and all tmux sessions appear in
the right server.

**Generalising:** In any new project, make sure the operator user and the
file-owning service user share a group, and that the shared workspace is
group-writable before starting the daemon.

---

## 2. Claude Code directory trust

**Problem:** Claude Code asks "do you trust this folder?" the first time it
opens a directory containing a CLAUDE.md. In automated tmux sessions, nobody
is there to answer. The session blocks silently and never becomes interactive.

**Fix:** Run this once on any new installation before the first pipeline cycle:

```bash
bash /var/www/hdp/agents/ideas/scripts/bootstrap-trust.sh
```

This runs `claude --print "ready"` non-interactively in each agent directory,
which pre-initialises the directory in Claude Code's project registry so the
trust prompt never appears in automation.

If you add a new agent directory later, add it to `bootstrap-trust.sh` and
run it again, or run manually:

```bash
cd /path/to/new/agent && claude --print "ready"
```

---

## 3. pgrep matching its own caller

**Problem:** `pgrep -f underseer.py` in a cron job (or a bash command run by
a tool) will match any bash process whose command line contains the string
"underseer.py" — including the cron line itself, or a tool evaluation string.
This causes the cron to think the daemon is running when it isn't.

**Fix:** Use a more specific pattern: `pgrep -f "python3.*underseer.py"`.
This only matches an actual python3 process running underseer.py.

---

## 4. SSL wildcard certificates require manual DNS renewal

**Problem:** Wildcard SSL certs (e.g. `*.staging.hittadittsverige.se`) cannot
use HTTP challenge — they require DNS-01 challenge, which means manual TXT
record entry at the DNS provider. Certbot issues the cert but marks it as
manual, so it will NOT auto-renew.

**Fix:** Set a calendar reminder before the expiry date and repeat the
certbot command:

```bash
sudo certbot certonly --manual --preferred-challenges dns \
  -d staging.example.se \
  -d *.staging.example.se
```

Add the new `_acme-challenge` TXT record at your DNS provider when prompted.
The cert renews for another 90 days.

Check expiry: `sudo certbot certificates`

---

## 5. The /remote-control command must be sent after Claude starts

**Problem:** When cron or a script starts a tmux session and runs `claude`,
Claude Code takes 30-60 seconds to fully initialise. If `/remote-control` is
sent immediately, it is typed into a loading screen and ignored. The session
then starts without remote control enabled.

**Fix:** Always sleep 60 seconds between launching claude and sending
`/remote-control`. See `scripts/start-planning.sh` for the pattern.

The HDS-ideas and HDS-overseer sessions handle this automatically. For any
new always-on session you add, follow the same pattern.

---

## 6. Startup context is stage-specific — don't use a single template

**Problem:** If the underseer writes the same startup-context.md to every
agent (e.g. always including a `Spec:` field), agents that run before the
spec exists will look for a file that isn't there yet, and agents that should
be reviewing against a product requirement will anchor to the spec instead —
introducing a subtle bias.

**Fix:** Generate stage-specific startup-context.md content. See
`overseer/underseer.py` `write_startup_context()` for the reference
implementation. Key rules:
- `features` gets `Requirements:` (product req doc), not `Spec:`
- `testing-staging` gets `Criteria:` as primary, `Spec:` as secondary context
- `reviewer` gets `Requirements:` as primary, `Spec:` as secondary
- `dev` and `features` are the only stages that receive kick-back context
- All stages after dev get `Staging URL:` so they know where to test

---

## 7. Bias isolation is a first-class concern

The pipeline's value comes from each agent being an independent judge.
Keep these rules when extending the pipeline:

- Testing agents must not know the kick-back history of a feature
- The reviewer must not know how many times the feature has been through
  the pipeline — it judges what is in front of it, not the journey
- Only dev and features receive kick-back context, because they are the
  ones fixing things
- Each agent's CLAUDE.md should explicitly state what it does NOT read,
  not just what it does read
- Output files between stages should be factual (pass/fail, specific
  locations, exact expected vs actual) — never editorial

---

## 8. Product requirements must exist before the features agent runs

**Problem:** The features agent needs a product requirements document to write
a spec from. If only a one-line build-queue entry exists, the agent has to
guess at intent, and the spec will reflect assumptions rather than decisions.

**Fix:** The product agent writes a requirements doc to:
  `staging/docs/product-requirements/[feature-name].md`

For items going directly to build-queue (bypassing the product agent), write
the requirements doc manually first. The features agent will not start
cleanly without it.

For complex product-backlog items, also write a companion note at:
  `staging/docs/product-backlog-notes/[ID]-[slug].md`

This gives the product agent enough context to write a good requirement
without making assumptions.

---

## 9. Group membership doesn't activate in existing sessions

**Problem:** After running `sudo usermod -a -G hdp patch`, the change takes
effect for NEW login shells only. Any tmux session (including the always-on
HDS-ideas session) that was already running before the usermod will not see
the new group, even after the user logs in again elsewhere. Running the daemon
from such a session will fail with "Permission denied" on group-owned files
even though `id` on a fresh terminal shows the group correctly.

**Fix:** Use `sg hdp` to execute the daemon command with the group active,
regardless of what the current session's group list looks like:

```bash
sg hdp -c "python3 '$UNDERSEER_PY' >> '$LOG' 2>&1 &"
```

This is now the default in `start-underseer.sh`. On a fresh project, add it
from the start so you never depend on group inheritance being active.

The always-on HDS-ideas session will also lack the group until it is
restarted. If the ideas agent ever needs to write to group-owned files
directly, restart the session after the usermod.

---

## 10. Pipeline agents need /remote-control to run autonomously

**Problem:** The daemon starts each pipeline agent with `claude`, but Claude
Code starts in interactive mode and will prompt for approval on file edits and
shell commands. In an unattended tmux session, nobody is there to approve them.
The agent silently stalls.

**Fix:** Send `/remote-control` to each agent session 60 seconds after
launching Claude (same timing rule as pitfall #5). The daemon now does this
automatically via a background subprocess in `start_agent()`:

```python
subprocess.Popen(
    f"sleep 60 && tmux send-keys -t {session} '/remote-control' Enter",
    shell=True
)
```

If you add a new always-on session outside the daemon, follow the same pattern
as `start-planning.sh`: sleep 60 then send `/remote-control`.

---

## 11. Main loop exceptions swallow the traceback

**Problem:** The daemon's `except Exception as e` handler logged only `str(e)`,
which for many errors is just the short message (e.g. `invalid literal for
int() with base 10: '**'`). The file name and line number are lost, making
the root cause impossible to find from the log alone.

**Fix:** Log the full traceback:

```python
import traceback
tb = traceback.format_exc()
log(f"ERROR in main loop: {e}\n{tb}")
```

This is now in the daemon. On a new project, add it from the start.

---

## 12. Product/COMPLETE handler declares cycle done while features are active

**Problem:** When the product agent finishes, it writes "Stage Status: COMPLETE" to
pipeline-state.md. The daemon sees this, kills the product session, and starts the
features agent via `_start_feature` -- which updates pipeline-state.md to
"features / IN PROGRESS" and sets the build-queue item to ACTIVE.

However, in some timing windows the product agent's COMPLETE write lands in
pipeline-state.md AFTER the daemon has already called `_start_feature`. On the next
60-second poll, the daemon sees "product / COMPLETE" again, re-enters the handler,
and calls `next_queued_item`. This time the item is ACTIVE (not QUEUED), so
`next_queued_item` returns None. The daemon then checks the product backlog, finds
nothing QUEUED there either, and incorrectly declares the cycle complete -- even
though the features agent is actively running.

The same logic also had a KeyError: `next_item['name']` should be `next_item['feature']`
(matching the key produced by `read_queue`).

**Fix:** Before declaring cycle complete from the product/COMPLETE path, check whether
any build-queue items are ACTIVE. If so, features are still in flight -- log and
return without escalating.

```python
active_items = [i for i in items if i["status"] == "ACTIVE"]
if active_items:
    log(f"Level 5: product agent complete but features still active: ...")
else:
    # safe to check backlog and potentially call _cycle_complete
```

Also fix the KeyError: use `next_item['feature']`, not `next_item['name']`.

**Generalising:** Any time you add a "nothing left to do" check to the daemon, include
ACTIVE items in the definition of "things in progress". An empty QUEUED list is not
the same as an empty pipeline.

---

## 13. Pipeline agents sit idle after /remote-control -- no startup message sent

**Problem:** The daemon starts each pipeline agent with `claude --permission-mode auto`,
then sends `/remote-control` 60 seconds later. A second blank Enter was intended to
trigger Claude to read its CLAUDE.md and begin work. In practice this is unreliable:
some agents start correctly, others sit idle at the `❯` prompt indefinitely and the
stuck-agent alarm fires 4 hours later.

The root cause: an empty Enter in remote-control mode is not a guaranteed trigger.
The agent has no message to respond to and makes no assumptions about what it should
do without one.

**Fix:** After sending `/remote-control`, wait 5 seconds then send an explicit startup
message: "Read your startup-context.md and begin your work." This is unambiguous and
always triggers the agent to begin.

```python
subprocess.Popen(
    f"sleep 60 && tmux send-keys -t {session} '/remote-control' Enter"
    f" && sleep 5 && tmux send-keys -t {session}"
    f" 'Read your startup-context.md and begin your work.' Enter",
    shell=True
)
```

This is now the default in `start_agent()`.

**Generalising:** Any always-on or pipeline session that activates remote-control
should immediately follow with an explicit message telling Claude what to do. Never
rely on an empty message or an implicit "Claude will just know" assumption.

---

## 14. Always-on agent cron revival must use a revive script, not inline commands

**Problem:** The HDS-ideas cron revival used inline tmux commands:
```
tmux new-session ... && tmux send-keys -t HDS-ideas "claude" Enter
```
This only starts Claude — it does not send `/remote-control` or a startup message.
After a crash revival, the session runs but is inaccessible (no remote control) and
silent (no task). The stuck-agent alarm would eventually fire, but nobody would know
the session had crashed in the meantime.

**Fix:** Create a dedicated revive script (e.g. `scripts/revive-ideas.sh`) that runs
the full startup sequence: start Claude → sleep 60 → send `/remote-control` → sleep 5
→ send startup message. The cron calls the script, not inline commands:

```
*/5 * * * * tmux has-session -t HDS-ideas 2>/dev/null || bash /path/to/revive-ideas.sh >> revive.log 2>&1 &
```

See `scripts/revive-ideas.sh` for the reference implementation.

**Generalising:** Any always-on session managed by cron should have a revive script,
not an inline one-liner. The one-liner is always missing the /remote-control and
startup message steps.

---

## 15. tmux send-keys: text and Enter in one call can leave Enter unregistered

**Problem:** When sending a message to an agent session using:
```bash
tmux send-keys -t SESSION "message text" Enter
```
the Enter sometimes does not register if the session is in a transitional state
(e.g. immediately after `/remote-control` connects, or while Claude is still
rendering). The text lands in the input buffer but is not submitted — it sits at
the `❯` prompt visibly but Claude never sees it.

This affects both manual interventions (sending messages from another agent or
the overseer) and automated scripts that send a message too soon after a state
change.

**Fix:** If a message is sitting in the buffer unsubmitted, send a bare Enter to
flush it:
```bash
tmux send-keys -t SESSION "" Enter
```

For automation, always include an explicit `sleep 5` between `/remote-control` and
the startup message (already the pattern in `start_agent()` and `start-planning.sh`).
If reliability is critical, send text and Enter as two separate `send-keys` calls
with a short sleep between:
```bash
tmux send-keys -t SESSION "message text"
sleep 1
tmux send-keys -t SESSION "" Enter
```

**Diagnosis:** Capture the pane with `tmux capture-pane -t SESSION -p -S -20`. If
the message text appears after `❯` with no Claude response below it, the Enter did
not register. Send a bare Enter to submit.

---

## 16. Pipeline agents must not touch the staging git repo's branch state

**Problem:** The UX/UI agent abandoned its visual review role and attempted git
operations on the staging repo: it checked out `main`, attempted a merge, and left
`docs/archive/` and `docs/cycles/` as untracked blocking files. All pipeline docs
(pipeline-state.md, build-queue.md, etc.) disappeared from the working tree. Manual
recovery was required: kill the agent, remove blocking untracked dirs, restore the
cycle branch, stash modified files, do the merge manually.

**Why it happened:** The UX/UI CLAUDE.md did not explicitly forbid git branch
operations. With no prohibition, the agent reasoned that "closing out the feature"
meant doing the merge itself.

**Fix -- three layers:**

1. **Each agent CLAUDE.md must explicitly prohibit git branch operations:**
   Add to every pipeline agent's CLAUDE.md:
   ```
   ## What you must never do
   - Run git checkout, git merge, git push, or git branch commands on the staging repo
   - Change the staging repo's current branch
   - These operations are reserved for the daemon and Patch
   ```

2. **Add a git pre-checkout hook on the staging repo** to block non-daemon, non-Patch
   branch switches during a cycle. If `daemon-enabled` exists and the user is not hdp,
   refuse the checkout:
   ```bash
   #!/bin/bash
   # .git/hooks/pre-checkout (or use a pre-command wrapper)
   # Soft guard — logs and warns rather than hard-blocks in early deployments
   if [ -f /var/www/hdp/agents/overseer/daemon-enabled ]; then
     echo "WARNING: daemon-enabled flag is set. Branch switch during active cycle."
   fi
   ```

3. **Underseer monitoring:** If the staging repo's current branch changes to anything
   other than the expected cycle branch or the current feature branch, the underseer
   should escalate immediately rather than waiting for the stuck-agent alarm.

**Generalising:** On any new DPA project, add the git prohibition to agent CLAUDE.mds
before the first cycle. It is much easier to prevent this than to recover from it.
