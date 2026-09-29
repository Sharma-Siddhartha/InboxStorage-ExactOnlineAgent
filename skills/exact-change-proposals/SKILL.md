---
name: exact-change-proposals
description: Exact Online agent (Inbox Storage): turn 'propose fix' decisions into change requests for the bookkeeper, with current and proposed value. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Change proposals

Turn today's `propose_fix` decisions into **change requests** for the bookkeeper. A change request
is a precise instruction a person can carry out in Exact: which record, which field, what it is now,
what it should become, and why. You never post in Exact.

Follow `references/run-protocol.md`.

## Steps

1. Read today's `propose_fix` decisions of this agent that have no change request yet:
   `SELECT d.* FROM PLATFORM.AGENT_OPS.DECISIONS d LEFT JOIN PLATFORM.AGENT_OPS.CHANGE_REQUESTS c USING (DECISION_ID) WHERE d.AGENT='exact' AND d.CHOICE='propose_fix' AND c.CR_ID IS NULL`.
2. For each, look up the **current value** in EXACT.CORE (never from memory or the finding alone).
3. Write the change requests in one `agent_ops_log` call (table `CHANGE_REQUESTS`), one row per field change:
   - `TARGET_OBJECT` in `transaction_line | gl_account | relation | match_set`
   - `LEVEL = 1` (only level-1 changes may come here; if you find a structural change, don't write it: add an `escalate` decision instead)
   - `ASSIGNEE_ROLE = 'bookkeeper'`, `STATUS = 'proposed'`
   - `CURRENT_VALUE` / `PROPOSED_VALUE` as JSON; `NOTE` = the instruction in one line, e.g. "Reclassify entry 24011234 line 2 from GL 4410 to GL 4420 (cost centre missing: add KP02)."
4. Matches (open-item matching) become `TARGET_OBJECT = 'match_set'` with the receipt and invoice IDs in PROPOSED_VALUE and the confidence in NOTE.

## Confirmation loop (runs each day before new proposals)

For each change request with `STATUS='proposed'` older than one load:
- If EXACT.CORE now shows the proposed value → write a `confirmed` row (via `agent_ops_log`).
- If it shows a third value → insert `mismatch` and let triage escalate it tomorrow.
- If unchanged after 14 days → insert `expired` (the finding stays open and returns to triage).
