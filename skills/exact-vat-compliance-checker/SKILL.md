---
name: exact-vat-compliance-checker
description: Exact Online agent (Inbox Storage): vAT deadlines, VAT code coverage, and VIES checks for any cross-border invoices. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Vat compliance checker  ·  planned (phase 4)

**Job:** VAT deadlines, VAT code coverage, and VIES checks for any cross-border invoices

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Deadlines from the accountant's filing calendar (decision 11.10). VAT code coverage vs account defaults; VIES check for cross-border invoices if any.

## Contract

- Reads: exact.core, exact.governance
- Writes: ops.findings.vat
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
