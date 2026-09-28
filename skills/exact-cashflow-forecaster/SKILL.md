---
name: exact-cashflow-forecaster
description: Exact Online agent (Inbox Storage): short-term cash projection from open items and recurring postings. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Cashflow forecaster  ·  planned (phase 4)

**Job:** Short-term cash projection from open items and recurring postings

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

13-week projection: open receivables by expected payment date (due date + customer's historic delay), open payables by due date, recurring postings (rent, wages, storage revenue run-rate).

## Contract

- Reads: exact.core
- Writes: reports.cash_forecast
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
