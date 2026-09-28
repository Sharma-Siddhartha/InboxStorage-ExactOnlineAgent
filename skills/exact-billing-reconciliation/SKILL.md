---
name: exact-billing-reconciliation
description: Exact Online agent (Inbox Storage): monthly check of revenue invoiced by the billing system against revenue posted, per account and customer code. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Billing reconciliation  ·  planned (phase 5)

**Job:** Monthly check of revenue invoiced by the billing system against revenue posted, per account and customer code

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 5
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Monthly, before close: ask `billing.invoiced_totals` (Striker agent) for invoiced revenue per revenue account and customer code; compare with EXACT.CORE.REVENUE_LINES; any gap above tolerance is a finding.

## Contract

- Reads: exact.core
- Writes: ops.findings.billing
- Offers: —
- Uses: billing.invoiced_totals

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
