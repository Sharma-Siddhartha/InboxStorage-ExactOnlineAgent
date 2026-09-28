---
name: exact-reconciliation
description: Exact Online agent (Inbox Storage): cross-agent checks: HubSpot won deals vs revenue, Shiftbase hours vs wage cost, Bumbal jobs vs logistics cost. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Reconciliation  ·  planned (phase 5)

**Job:** Cross-agent checks: HubSpot won deals vs revenue, Shiftbase hours vs wage cost, Bumbal jobs vs logistics cost

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 5
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Requests to other agents via MESSAGES by capability. HubSpot: won deal (customer code, month) with no revenue posting within 60 days. Shiftbase: hours x rate band vs wage cost per period, totals only. Bumbal: job volumes vs logistics cost accounts per month.

## Contract

- Reads: exact.core, ops.messages.in
- Writes: ops.messages.out, ops.findings.reconciliation
- Offers: finance.reconcile
- Uses: crm.won_deals, workforce.hours, logistics.job_volumes

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
