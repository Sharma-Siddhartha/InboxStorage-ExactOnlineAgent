---
name: exact-month-end-checklist
description: Exact Online agent (Inbox Storage): close-readiness checklist for the finance owner before cut-off, grouped by owner. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Month end checklist  ·  planned (phase 4)

**Job:** Close-readiness checklist for the finance owner before cut-off, grouped by owner

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Everything that would block a clean close or VAT filing, grouped by owner: open bank lines, suspense balances, unconfirmed change requests, open periods, missing accruals.

## Contract

- Reads: exact.core
- Writes: reports.close_checklist
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
