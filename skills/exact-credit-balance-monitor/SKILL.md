---
name: exact-credit-balance-monitor
description: Exact Online agent (Inbox Storage): customer accounts in credit longer than agreed (refunds owed), as totals and customer codes. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Credit balance monitor  ·  planned (phase 4)

**Job:** Customer accounts in credit longer than agreed (refunds owed), as totals and customer codes

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Customer codes with a net credit balance for longer than `credit_balance_refund_days` after the contract ends (contract end date via the Striker agent or PLATFORM.INTEGRATION). Totals and codes only.

## Contract

- Reads: exact.core, exact.governance
- Writes: ops.findings.credit
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
