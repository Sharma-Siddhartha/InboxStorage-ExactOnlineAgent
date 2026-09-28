---
name: exact-period-close-monitor
description: Exact Online agent (Inbox Storage): periods open past their close date, missing accruals, unposted month-end journals. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Period close monitor  ·  planned (phase 4)

**Job:** Periods open past their close date, missing accruals, unposted month-end journals

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Flag periods open past their close date, missing accruals (recurring cost accounts without a posting this period), and unposted month-end journals. Uses FINANCIAL_PERIODS.

## Contract

- Reads: exact.core
- Writes: ops.findings.close
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
