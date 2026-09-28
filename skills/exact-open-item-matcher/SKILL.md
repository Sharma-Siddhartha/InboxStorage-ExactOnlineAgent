---
name: exact-open-item-matcher
description: Exact Online agent (Inbox Storage): unmatched receipts that fit an open item by customer, amount and date, with a confidence score. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Open item matcher  ·  planned (phase 4)

**Job:** Unmatched receipts that fit an open item by customer, amount and date, with a confidence score

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Needs the unmatched-receipts endpoint (loader/endpoints.yml UNMATCHED_RECEIPTS, to verify). For every unmatched receipt: candidates = open invoices of the same customer code; score exact amount > sum of several invoices > amount within tolerance; date proximity breaks ties. Findings carry receipt ID, invoice IDs and confidence; change proposals turn them into match sets for the bookkeeper.

## Contract

- Reads: exact.core
- Writes: ops.findings.matches
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
