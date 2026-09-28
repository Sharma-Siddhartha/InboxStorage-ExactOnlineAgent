---
name: exact-rate-table-sync
description: Exact Online agent (Inbox Storage): load exchange rates, only if foreign-currency postings exist (decision 11.9). Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Rate table sync  ·  planned (phase 4)

**Job:** Load exchange rates, only if foreign-currency postings exist (decision 11.9)

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Only if foreign-currency postings exist (decision 11.9). Load daily rates into EXACT.RAW.EXCHANGE_RATES via the loader.

## Contract

- Reads: exact.api
- Writes: exact.raw.rates
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
