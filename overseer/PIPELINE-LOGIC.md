# Pipeline Logic -- State Machine Reference

This document is the detailed decision table for underseer.py, the daemon.
For design rationale, see OVERSEER-DESIGN.md.

---

## Stage order

```
features -> acceptance -> dev -> testing-staging -> integration-testing -> reviewer -> ux-ui
```

---

## On each poll (every 60 seconds)

Read pipeline-state.md. Extract: current_stage, stage_status, kick_back_count,
current_feature, current_cycle, current_branch.

Then apply the rules below in order.

---

## Rule 1: IDLE

If stage_status = IDLE: do nothing. Wait for Patch to start a cycle.

---

## Rule 2: IN PROGRESS -- check for stuck agent

If stage_status = IN PROGRESS and time since last state change > 4 hours:
  Write escalation.md: "Agent [stage] stuck for [N] hours on [feature]."
  Set stage_status = BLOCKED, waiting_for = PATCH.
  Stop.

---

## Rule 3: COMPLETE -- advance to next stage

Stage           Next stage          Notes
-----------     ---------------     ------
features        acceptance          Features wrote spec; acceptance writes criteria
acceptance      dev                 Criteria written; dev builds
dev             testing-staging     Build complete; run acceptance criteria
testing-staging integration-testing All criteria pass; run integration checks
integration-testing reviewer        Integration passes; product review
reviewer        features*           *On KICK BACK only; on PASS advance to ux-ui
reviewer        ux-ui               On PASS
ux-ui           [end of feature]    On PASS: merge + housekeeping + next feature

On COMPLETE from any stage (except ux-ui):
  1. Kill current agent session
  2. Write startup-context.md to next agent directory
  3. Update pipeline-state.md: current_stage=next, stage_status=IN PROGRESS,
     kick_back_count=0
  4. Start next agent

On COMPLETE from ux-ui:
  Level 3: escalate to Patch ("feature X ready to merge; merge and continue or stop?")
  Level 4: merge feature branch into cycle branch, run housekeeping, pull next item

---

## Rule 4: KICKED BACK -- route to fix agent

On KICK BACK from testing-staging:    send to dev
On KICK BACK from integration-testing: send to dev
On KICK BACK from reviewer:           send to features
On KICK BACK from ux-ui:              send to dev

Procedure:
  1. Increment kick_back_count
  2. If kick_back_count >= 2: go to Rule 5 (quarantine)
  3. Kill current agent
  4. Write startup-context.md for target agent, including:
       - Kick-back source stage
       - Path to the fixes file (acceptance-fixes.md / integration-fixes.md / ux-fixes.md)
       - Kick-back count so the agent knows how many chances remain
  5. Update pipeline-state.md: current_stage=target, stage_status=IN PROGRESS
  6. Start target agent

Fix files by source:
  testing-staging     -> /var/www/hdp/staging/docs/dev-inbox/acceptance-fixes.md
  integration-testing -> /var/www/hdp/staging/docs/dev-inbox/integration-fixes.md
  reviewer            -> feedback delivered via Patch; spec rewrite required
  ux-ui               -> /var/www/hdp/staging/docs/dev-inbox/ux-fixes.md

---

## Rule 5: QUARANTINE (kick_back_count >= 2)

1. Mark feature QUARANTINED in build-queue.md
2. Kill current agent
3. Reset to cycle branch (delete the feature branch)
4. Mark any QUEUED features with depends_on = this feature's ID as SKIPPED
5. Write escalation.md with the quarantine reason
6. Check build-queue.md for remaining QUEUED eligible features
   - If found and level 4: start next feature (go to _start_feature)
   - If none: go to Rule 6

---

## Rule 6: EMPTY QUEUE / CYCLE COMPLETE

If build-queue.md has no QUEUED items with resolved dependencies:
  Write cycle completion summary to docs/cycles/cycle-00N-active.md
  Set pipeline-state.md: stage_status=IDLE, waiting_for=PATCH
  Write escalation.md: "Cycle complete. Awaiting your review."

---

## Rule 7: BLOCKED (agent set status to BLOCKED, not KICKED BACK)

A BLOCKED state means the agent cannot proceed and the problem is not a
kick-back scenario (e.g. missing external dependency, infrastructure issue,
missing data).

Always escalate to Patch immediately. Do not retry.

---

## Autonomy level modifiers

Level 1: The underseer takes no automated action; it just polls and holds.
         The overseer reads state on request and reports to Patch in plain
         language. All decisions go back to Patch.

Level 2: The underseer advances automatically within a stage sequence but
         stops before each handoff, writing an escalation. The overseer
         presents it: "Stage X complete. Advance to Y?" and waits for
         Patch's explicit go-ahead before the underseer proceeds.

Level 3: The underseer runs the full pipeline without stopping, except:
         - After ux-ui PASS: escalates, and the overseer relays
           "Feature ready to merge. Your call."
         - Any other escalation condition

Level 4: The underseer runs end-to-end. Merges features into the cycle
         branch after ux-ui PASS. Escalates (via the overseer) only on:
         double kick-back, BLOCKED, empty queue.

Level 5: Same as level 4, PLUS: the underseer processes product-backlog.md
         through the product agent, one item at a time, interleaved with the
         dev pipeline. Product-backlog → product agent → build-queue →
         features → ... → ux-ui, all without Patch's involvement.

         Level 5 flow (interleaved, one item at a time):
         1. If build-queue has QUEUED items: run them through the dev pipeline first
         2. When build-queue is empty: check product-backlog for next QUEUED item
         3. If found: start product agent for that single item
         4. Product agent writes 1 or more features to build-queue.md,
            marks product-backlog item COMPLETE, sets pipeline-state COMPLETE
         5. The underseer picks up the new build-queue items and runs them through pipeline
         6. Repeat from step 2 until both queues are exhausted

         Note: one product-backlog item can produce multiple build-queue features.
         All resulting features are run through the pipeline before the next
         product-backlog item is processed.

         Level 5 escalation conditions (same as level 4, plus):
         - Product agent sets BLOCKED (cannot produce a clear requirement)
         - Both product-backlog AND build-queue are empty: nothing to do

---

## Kick-back count reset

kick_back_count resets to 0 whenever a stage advances forward.
It only increments when a stage issues a KICKED BACK status.
A feature can accumulate at most 2 kick-backs at any single stage before
being quarantined.
