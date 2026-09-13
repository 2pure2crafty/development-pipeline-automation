# Pipeline Orchestration — Design Document

Everything agreed in conversation before the CLAUDE.md is written.
Use this as the source of truth when writing the overseer CLAUDE.md.

**Terminology:** the overseer is the AI persona (Patch's interface, judgment
calls, escalations). The underseer is `underseer.py`, the background daemon
doing the mechanical polling, state transitions, and tmux spawning underneath
it. Most of the step-by-step mechanics below (spinning up agents, killing
sessions, merging branches, writing pipeline-state.md) are underseer work;
"overseer" below is reserved for the moments Patch is actually being talked to.

---

## What the underseer is

The underseer is the always-on daemon. It is one of only two things that run
permanently (the other is the ideas agent). Every pipeline agent is spun up by
the underseer when it has work to do and killed when it hands off. The overseer
Claude session runs alongside it as Patch's interface and is revived by the
underseer if it dies.

The underseer never deploys. It works entirely within staging. The deploy agent
only ever receives instructions directly from Patch.

---

## Autonomy levels

The underseer can be set to run at any of five levels. Patch specifies the
level and optionally a stop condition (specific build phase ID, or unlimited)
via the overseer.

**Level 1 -- monitor and report.**
The underseer takes no automated action. The overseer observes the pipeline
state and tells Patch what is happening and what should happen next. Nothing
moves without Patch's explicit instruction. The overseer is a dashboard.

**Level 2 -- Patch's interface to the pipeline.**
Patch talks only to the overseer. The underseer spins up the correct agent,
passes the work, and stops at each handoff; the overseer reports the result to
Patch and waits for go-ahead before the underseer advances. Every handoff
requires Patch's approval. The relay burden shifts from Patch to the overseer,
but Patch remains in every decision.

**Level 3 -- autonomous staging pipeline.**
The underseer runs the full pipeline from features through to ux-ui sign-off
without Patch's involvement. It stops at the end of each feature and the
overseer reports: "Feature X has passed ux-ui and is ready to merge. Merge and
continue, or stop?" Patch makes the merge decision. Nothing merges at level 3.

**Level 4 -- autonomous end-to-end development.**
The underseer runs the full pipeline, merges completed features into the cycle
branch, runs housekeeping, pulls the next queued item, and starts the next
cycle without Patch. It escalates (via the overseer) only on: double kick-back
on the same issue, a BLOCKED state no agent can resolve, or an empty build
queue. The underseer never merges into staging main and never deploys.

---

## The autonomous cycle

Each time a cycle is set to level 3 or 4, the underseer drives it as an
autonomous cycle.

**Cycle ID format:** cycle-001, cycle-002, cycle-003 (incrementing)

**Cycle branch:** autonomous/cycle-001
All feature branches within the cycle branch off the cycle branch:
  autonomous/cycle-001
    └── feature/new-resident-onboarding
    └── feature/notice-board-filters

Feature branches merge back into the cycle branch when ux-ui signs off.
The cycle branch merges into staging main only when Patch intervenes.

---

## Cycle documentation

```
/var/www/hdp/staging/docs/cycles/
  cycle-001-active.md       ← created at cycle start, live record
  cycle-001-complete.md     ← renamed here when Patch closes the cycle
  cycle-archive.md          ← permanent record, all cycles appended
```

cycle-active.md contains:
  - Cycle ID and start timestamp
  - Autonomy level
  - Build phases queued at cycle start
  - Build phases completed, with timestamps and outcome notes
  - Any escalations to Patch during the cycle
  - Quarantined features and reasons
  - Skipped features and reasons
  - Current status

When Patch closes the cycle: overseer renames active to complete, appends
a summary to cycle-archive.md, and clears the active doc.

---

## Pipeline state signal

Single source of truth for pipeline state:

```
/var/www/hdp/staging/docs/pipeline-state.md
```

Structure:
  Current cycle: cycle-001
  Current feature: [feature name]
  Current branch: feature/[name]
  Current stage: [agent name]
  Stage status: IN PROGRESS / COMPLETE / KICKED BACK / BLOCKED
  Waiting for: [agent name or PATCH]
  Kick-back count: [n] (resets to 0 when stage advances)
  Last updated: [timestamp]

Each agent updates pipeline-state.md when it finishes. The underseer reads it
to know when to act.

---

## Build queue

```
/var/www/hdp/staging/docs/build-queue.md
```

Format:
  | ID  | Feature name | Status              | Depends on |
  |-----|-------------|---------------------|------------|
  | 001 | [name]      | QUEUED/ACTIVE/COMPLETE/QUARANTINED/SKIPPED | none / [ID] |

Status values:
  QUEUED: approved and waiting
  ACTIVE: currently in the pipeline
  COMPLETE: passed full pipeline including live-testing
  QUARANTINED: double kick-back, needs Patch review
  SKIPPED: dependency was quarantined, cannot proceed

The depends-on field is filled in by the features agent when writing the spec.
If a feature has no dependencies on unbuilt features, it states: none.
If it depends on a feature not yet complete, it states the ID of that feature.

---

## Level 4 underseer flow -- step by step

1.  Patch sets level 4, specifies queue or unlimited
2.  The underseer creates cycle ID, creates cycle branch (autonomous/cycle-00n)
3.  The underseer creates cycle-active.md
4.  The underseer reads first QUEUED item with no unresolved dependencies from build-queue.md
5.  The underseer marks it ACTIVE in build-queue.md
6.  The underseer updates pipeline-state.md
7.  The underseer spins up features agent, passes: feature name, cycle ID, cycle branch
8.  Features writes spec to build-phase-current.md, fills in depends-on in build-queue.md,
    updates pipeline-state.md to COMPLETE
9.  The underseer detects COMPLETE, kills features agent
10. The underseer spins up acceptance agent
11. Acceptance writes criteria doc to /docs/acceptance/[feature]-criteria.md,
    updates pipeline-state.md to COMPLETE
12. The underseer detects COMPLETE, kills acceptance agent
13. The underseer spins up dev agent, passes: feature name, branch name, criteria doc location
14. Dev builds on feature branch off cycle branch, writes deployment-note.md,
    updates pipeline-state.md to COMPLETE
15. The underseer detects COMPLETE, kills dev agent
16. The underseer spins up acceptance-testing
17. Acceptance-testing runs criteria:
      PASS: updates pipeline-state.md COMPLETE
            The underseer kills acceptance-testing, spins up integration-testing
      KICK BACK: updates pipeline-state.md KICKED BACK, increments kick-back count
            The underseer kills acceptance-testing
            If kick-back count < 2: spins up dev with kick-back context
            If kick-back count = 2: STOP, escalate to Patch
18. Integration-testing runs:
      PASS: updates pipeline-state.md COMPLETE
            The underseer kills integration-testing, spins up product-reviewer
      KICK BACK: updates pipeline-state.md KICKED BACK, increments kick-back count
            The underseer kills integration-testing
            If kick-back count < 2: spins up dev with kick-back context
            If kick-back count = 2: STOP, escalate to Patch
19. Product-reviewer assesses:
      PASS: updates pipeline-state.md COMPLETE
            The underseer kills product-reviewer, spins up ux-ui
      KICK BACK: updates pipeline-state.md KICKED BACK, increments kick-back count
            The underseer kills product-reviewer
            If kick-back count < 2: spins up features with kick-back context
            If kick-back count = 2: STOP, escalate to Patch
20. UX-ui reviews:
      KICK BACK: updates pipeline-state.md KICKED BACK, increments kick-back count
            The underseer kills ux-ui
            If kick-back count < 2: spins up dev with kick-back context
            If kick-back count = 2: STOP, escalate to Patch
      PASS: updates pipeline-state.md COMPLETE
            The underseer kills ux-ui
21. The underseer merges feature branch into cycle branch
22. The underseer runs housekeeping:
      - Moves completed phase from build-phase-current.md to cycle-active.md
      - Marks phase COMPLETE in build-queue.md
      - Updates pipeline-state.md
23. The underseer checks build-queue.md for next QUEUED item with no unresolved dependencies
      If found: go to step 4
      If empty: update cycle-active.md with summary, update pipeline-state.md,
                notify Patch: "Cycle complete. N phases built. Awaiting your review."

---

## Double kick-back and feature skipping

When a feature reaches kick-back count 2 on any stage:
1. The underseer marks feature as QUARANTINED in build-queue.md
2. The underseer resets cycle branch to pre-feature state
3. The underseer records the quarantine in cycle-active.md with reason
4. The underseer checks remaining QUEUED features:
     - Features with depends-on = quarantined feature ID: mark SKIPPED
     - Features with no dependency on quarantined feature: proceed normally
5. The underseer continues cycle with remaining eligible features
6. At end of cycle, report to Patch includes quarantined and skipped features

---

## Escalation conditions -- underseer stops regardless of level

- Kick-back count reaches 2 on the same issue
- Any agent sets pipeline-state to BLOCKED (not KICKED BACK)
- Build queue is empty
- Any unexpected error no agent can resolve
- A feature cannot proceed because its dependency was quarantined and no
  other eligible features remain in the queue

---

## Housekeeping -- when it happens

Housekeeping happens after live-testing passes, before the next branch opens.
At level 4, the underseer handles the staging-side housekeeping (build-phase-current
to cycle-active). The post-deployment housekeeping (cycle-active to archive) happens
when Patch intervenes and closes the cycle.

---

## What the overseer needs at startup from Patch

- Autonomy level (1, 2, 3, or 4)
- Stop condition: specific build phase ID, or unlimited
- Confirmation that the build queue has approved items ready

---

## What the underseer tells each agent at startup

- Feature name
- Cycle ID and cycle branch name
- Location of relevant input documents
- Any kick-back context if the agent is being re-spun after a kick-back
