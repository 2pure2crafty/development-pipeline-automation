# HDS Development Pipeline Automation

A multi-agent autonomous development pipeline for Hitta Ditt Sverige. Claude agents
handle every stage from idea to merged feature, with a Python daemon coordinating
handoffs and Patch as the final authority.

---

## How it works — the short version

1. Patch spitballs with the **ideas agent**, which routes approved ideas into one of
   two backlogs depending on whether they need commercial framing first.
2. The **overseer daemon** (`overseer.py`) polls `pipeline-state.md` every 60 seconds
   and drives features through an 8-stage pipeline automatically.
3. Each pipeline agent runs in its own tmux session, reads a `startup-context.md`
   written by the daemon, does its work, and updates `pipeline-state.md` when done.
4. The daemon detects the state change and either advances to the next stage or
   escalates to Patch if something needs a human decision.

---

## Architecture

```
                        ┌─────────────────────────────────────────────┐
                        │  /var/www/hdp/staging/docs/                 │
                        │                                             │
  ┌────────────┐        │  product-backlog.md   build-queue.md        │
  │   Patch    │        │  pipeline-state.md    build-phase.md        │
  └─────┬──────┘        │  acceptance/          dev-inbox/            │
        │               └──────────────────────────────────────────────┘
        │ spitballs               ▲▲          ││
        ▼                         read        write
  ┌────────────┐         ┌────────────────────────────────────────────┐
  │   Ideas    │         │         overseer.py  (daemon)              │
  │   Agent    │         │   polls every 60 s · writes heartbeat      │
  │ HDS-ideas  │         │   starts/kills agent tmux sessions         │
  └─────┬──────┘         │   handles kick-backs · escalates           │
        │                └────────────────────────────────────────────┘
        │                         ▲
        ├── planning-backlog ──► Planning Agent (on demand)
        │                         │
        ├── product-backlog ───────┤ (Level 5: also auto-fed to Product Agent)
        │                         │
        └── "start overseer" ─► daemon-enabled flag created
```

---

## Pipeline flowchart

```
  Idea approved by Patch
         │
         ├─── needs commercial framing? ──► planning-backlog.md
         │                                        │
         │                                  Planning Agent
         │                                  (on demand, manual start)
         │                                        │
         └─────────────────────────────────► product-backlog.md
                                                   │
                                          [Level 5: auto]
                                            Product Agent
                                          (turns backlog item
                                           into build-queue row)
                                                   │
                                            build-queue.md
                                                   │
                                         ┌─────────▼──────────┐
                                         │   Features Agent   │ ◄─── kick-back from reviewer
                                         │  (technical spec)  │
                                         └─────────┬──────────┘
                                                   │
                                         ┌─────────▼──────────┐
                                         │ Acceptance Agent   │
                                         │ (test criteria)    │
                                         └─────────┬──────────┘
                                                   │
                                         ┌─────────▼──────────┐
                          ┌── kick-back ─┤    Dev Agent       │ ◄─── kick-back from testing/ux-ui
                          │             │    (writes code)    │
                          │             └─────────┬──────────┘
                          │                       │
                          │             ┌─────────▼──────────┐
                          │             │  Testing (staging)  │
                          └────────────►  acceptance tests   │
                                        └─────────┬──────────┘
                                         PASS     │   FAIL ──► dev (fix + retest)
                                                  │
                                         ┌────────▼───────────┐
                                         │ Integration Testing │
                                         │  regression tests  │
                                         └────────┬───────────┘
                                          PASS    │   FAIL ──► dev (fix + retest)
                                                  │
                                         ┌────────▼───────────┐
                                         │  Product Reviewer  │
                                         │  (product fit)     │
                                         └────────┬───────────┘
                                          PASS    │   FAIL ──► features (spec problem)
                                                  │
                                         ┌────────▼───────────┐
                                         │   UX/UI Agent      │
                                         │  (design review)   │
                                         └────────┬───────────┘
                                          PASS    │   FAIL ──► dev (fix + re-review)
                                                  │
                                    merge feature → cycle branch
                                                  │
                                       more QUEUED items?
                                          │           │
                                         YES          NO
                                          │           │
                                    next feature   Cycle complete
                                                  (escalate to Patch)
```

**Double kick-back rule:** if a feature is kicked back a second time at any stage,
it is quarantined. Its branch is deleted, dependent features are marked SKIPPED,
and Patch is notified. The pipeline continues with remaining eligible features.

---

## Agent roles

| Agent | tmux session | Directory | Role |
|-------|-------------|-----------|------|
| Ideas | HDS-ideas | `agents/ideas/` | Brainstorming partner, routes ideas, starts other agents |
| Planning | HDS-planning | `agents/planning/` | Commercial strategy, pricing, pitch materials |
| Product | HDS-product | `agents/product/` | Translates business intent into product requirements |
| Features | HDS-features | `agents/features/` | Writes technical specs from product requirements |
| Acceptance | HDS-acceptance | `agents/acceptance/` | Writes acceptance criteria before dev starts |
| Dev | HDS-dev | `agents/dev/` | Writes code to satisfy the acceptance criteria |
| Testing (staging) | HDS-testing-staging | `agents/testing-staging/` | Runs acceptance criteria against feature branch |
| Integration Testing | HDS-integration-testing | `agents/integration-testing/` | Tests feature interactions with the rest of the platform |
| Reviewer | HDS-reviewer | `agents/reviewer/` | Product-fit review (not a code review) |
| UX/UI | HDS-ux-ui | `agents/ux-ui/` | Visual and interaction review, last gate before merge |
| Overseer | HDS-overseer | `agents/overseer/` | Patch's interface; receives instructions, reports status |

The **overseer Claude session** (HDS-overseer) is Patch's conversational interface.
The **overseer daemon** (`overseer.py`) is the mechanical engine running underneath it.
They are separate: the Claude session can crash and restart without stopping the daemon.

---

## Autonomy levels

The daemon respects an `autonomy_level` setting in `current-config.md`. Higher levels
mean less human intervention between stages.

| Level | Behaviour |
|-------|-----------|
| 1 | Manual only — no automatic advancement |
| 2 | Auto-start each stage but wait for Patch go-ahead before advancing |
| 3 | Auto-advance through pipeline; pause after ux-ui for Patch to approve merge |
| 4 | Auto-advance and auto-merge feature branches into cycle branch |
| 5 | Level 4 + auto-pull from product-backlog when build-queue is empty |

---

## Kick-back routing

When an agent is not satisfied, it sets `stage_status: KICKED BACK` in
`pipeline-state.md` and writes its findings to the appropriate inbox file.
The daemon detects this and routes accordingly:

| Kicked back from | Routed to | Inbox file |
|-----------------|-----------|------------|
| testing-staging | dev | `dev-inbox/acceptance-fixes.md` |
| integration-testing | dev | `dev-inbox/integration-fixes.md` |
| reviewer | features | reviewer output |
| ux-ui | dev | `dev-inbox/ux-fixes.md` |

---

## Key files

| File | Purpose |
|------|---------|
| `staging/docs/pipeline-state.md` | Single source of truth for pipeline state |
| `staging/docs/build-queue.md` | Features queued for the pipeline |
| `staging/docs/product-backlog.md` | Ideas approved for the product agent |
| `staging/docs/build-phase.md` | Current feature spec (written by features agent) |
| `staging/docs/dev-inbox/` | Fix briefs written by testing/reviewer/ux-ui agents |
| `staging/docs/acceptance/` | Acceptance criteria documents (one per feature) |
| `agents/overseer/current-config.md` | Cycle config: autonomy level, stop condition |
| `agents/overseer/overseer.log` | Daemon activity log |
| `agents/overseer/overseer-restart.md` | Crash recovery snapshot (overwritten every 60s) |
| `agents/overseer/escalation.md` | Pending escalations requiring Patch input |
| `agents/overseer/daemon-enabled` | Flag file — daemon auto-revives only while this exists |

---

## Starting the system

### Starting an automation cycle

1. Tell the ideas agent you want to start a cycle.
2. Ideas agent runs `start-overseer.sh`, which creates `daemon-enabled` and starts
   `overseer.py` in the background.
3. The daemon immediately starts the HDS-overseer Claude session (your interface).
4. In HDS-overseer, use the intake form to configure and start the cycle.
5. The daemon picks up the config and begins processing features from build-queue.md.

### Starting the planning agent (on demand)

Tell the ideas agent "start planning" and it runs `start-planning.sh`, which creates
the HDS-planning session, waits 60 seconds, and sends `/remote-control`.

### Stopping the daemon

```bash
kill $(cat /var/www/hdp/agents/overseer/overseer.pid)
rm /var/www/hdp/agents/overseer/daemon-enabled
```

Removing `daemon-enabled` prevents cron from restarting it.

---

## Session management

### Always-on sessions (managed by cron)

| Session | Managed by | Behaviour |
|---------|-----------|-----------|
| HDS-ideas | cron (`*/5 * * * *`) | Revives automatically if dead |
| HDS-overseer | overseer.py daemon | Revived by daemon every 10 polls (10 min) |

### Pipeline sessions (managed by daemon)

Pipeline agent sessions (HDS-features, HDS-dev, etc.) are created fresh by the
daemon when a stage starts and killed when the stage completes. They do not persist
between stages.

### First-time setup

Claude Code requires a one-time trust confirmation when first opening each directory.
Run this once before starting the first cycle:

```bash
bash /var/www/hdp/agents/ideas/scripts/bootstrap-trust.sh
```

---

## Directory structure

```
/var/www/hdp/agents/
├── ideas/              Ideas agent workspace (always-on)
│   ├── CLAUDE.md
│   ├── scripts/
│   │   ├── start-overseer.sh
│   │   ├── start-planning.sh
│   │   └── bootstrap-trust.sh
│   ├── ideas-log.md    Private conversation log
│   └── memory/         Persistent memory files
├── overseer/           Overseer workspace
│   ├── CLAUDE.md
│   ├── overseer.py     The daemon
│   ├── current-config.md
│   ├── escalation.md
│   ├── overseer.log
│   ├── overseer-restart.md
│   └── daemon-enabled  (created when cycle is active)
├── planning/           Planning agent workspace
├── product/            Product agent workspace
├── features/           Features agent workspace
├── acceptance/         Acceptance agent workspace
├── dev/                Dev agent workspace
├── testing-staging/    Acceptance testing workspace
├── integration-testing/ Integration testing workspace
├── reviewer/           Product reviewer workspace
└── ux-ui/              UX/UI agent workspace

/var/www/hdp/staging/docs/   Shared workspace (agents read/write here)
```
