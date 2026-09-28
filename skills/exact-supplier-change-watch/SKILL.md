---
name: exact-supplier-change-watch
description: Exact Online agent (Inbox Storage): new suppliers, changed bank-account fingerprints, and e-invoices whose bank fingerprint differs from the supplier's. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Supplier change watch  ·  planned (phase 4)

**Job:** New suppliers, changed bank-account fingerprints, and e-invoices whose bank fingerprint differs from the supplier's

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

New BANK_FP for an existing supplier relation = change; always escalated before the next payment run. New suppliers listed. For e-invoices: fingerprint the IBAN in the UBL at load time and compare with the supplier's current BANK_FP.

## Contract

- Reads: exact.core.master, exact.core
- Writes: ops.findings.supplier
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
