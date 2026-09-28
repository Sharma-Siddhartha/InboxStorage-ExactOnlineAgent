---
name: exact-collections-assistant
description: Exact Online agent (Inbox Storage): draft a prioritised reminder list for overdue receivables; never sends anything. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Collections assistant  ·  planned (phase 4)

**Job:** Draft a prioritised reminder list for overdue receivables; never sends anything

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Draft a prioritised list of overdue receivables per customer code (amount x age x history) for the finance owner or credit control (decision 11.11). Never sends anything; a person decides and sends.

## Contract

- Reads: ops.decisions, exact.core
- Writes: drafts.reminder_list
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
