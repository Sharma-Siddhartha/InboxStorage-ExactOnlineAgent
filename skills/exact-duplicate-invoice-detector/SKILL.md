---
name: exact-duplicate-invoice-detector
description: Exact Online agent (Inbox Storage): possible duplicate purchase or sales invoices by party, amount and date. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Duplicate invoice detector  ·  planned (phase 4)

**Job:** Possible duplicate purchase or sales invoices by party, amount and date

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Same party, same amount, invoice dates within 7 days, different entry numbers. Purchase side first (duplicate payments), then sales.

## Contract

- Reads: exact.core
- Writes: ops.findings.duplicates
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
