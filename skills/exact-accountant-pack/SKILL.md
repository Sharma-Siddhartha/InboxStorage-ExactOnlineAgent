---
name: exact-accountant-pack
description: Exact Online agent (Inbox Storage): year-end pack for the external accountant from ledger data and snapshots. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Accountant pack  ·  planned (phase 6)

**Job:** Year-end pack for the external accountant from ledger data and snapshots

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 6
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Trial balance, reconciliation status, open items by age, manual journal entries above a threshold, every chart-of-accounts change of the year (from snapshots/ git history). One reviewed file.

## Contract

- Reads: exact.core, repo.snapshots
- Writes: reports.accountant_pack
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
