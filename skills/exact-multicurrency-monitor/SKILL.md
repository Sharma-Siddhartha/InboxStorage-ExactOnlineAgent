---
name: exact-multicurrency-monitor
description: Exact Online agent (Inbox Storage): unrealised exchange differences and missing rates, if needed. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Multicurrency monitor  ·  planned (phase 4)

**Job:** Unrealised exchange differences and missing rates, if needed

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Only if needed (decision 11.9).

## Contract

- Reads: exact.core, exact.raw.rates
- Writes: ops.findings.fx
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
