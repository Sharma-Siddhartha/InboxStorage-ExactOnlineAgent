---
name: exact-margin-analyst
description: Exact Online agent (Inbox Storage): revenue, cost and margin per account or service line, using the agreed definitions. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Margin analyst  ·  planned (phase 4)

**Job:** Revenue, cost and margin per account or service line, using the agreed definitions

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Revenue, cost and margin per GL account and service line using governance/account_types.yml `margin`. Budget vs actual only if budgets are kept in Exact (decision 11.17).

## Contract

- Reads: exact.core, exact.governance
- Writes: reports.margin
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
