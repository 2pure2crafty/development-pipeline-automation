# DPA Pitfalls and Setup Notes

Things that bit us during the initial setup of the HDS Development Pipeline
Automation. Read this before spinning up the DPA on a new project.

---

## 1. File ownership and the daemon user

**Problem:** The overseer daemon writes to files in two different places:
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

**Problem:** `pgrep -f overseer.py` in a cron job (or a bash command run by
a tool) will match any bash process whose command line contains the string
"overseer.py" — including the cron line itself, or a tool evaluation string.
This causes the cron to think the daemon is running when it isn't.

**Fix:** Use a more specific pattern: `pgrep -f "python3.*overseer.py"`.
This only matches an actual python3 process running overseer.py.

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

**Problem:** If the overseer writes the same startup-context.md to every
agent (e.g. always including a `Spec:` field), agents that run before the
spec exists will look for a file that isn't there yet, and agents that should
be reviewing against a product requirement will anchor to the spec instead —
introducing a subtle bias.

**Fix:** Generate stage-specific startup-context.md content. See
`overseer/overseer.py` `write_startup_context()` for the reference
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
