---
name: exact-benchmark-tracker
description: Exact Online agent (Inbox Storage): trend lines for hygiene, ageing and margin, so slow deterioration shows. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Benchmark tracker  ·  planned (phase 6)

**Job:** Trend lines for hygiene, ageing and margin, so slow deterioration shows

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 6
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Weekly trend lines: open findings per monitor, ageing buckets, DSO, margin per service line.

## Contract

- Reads: ops.runs
- Writes: reports.benchmarks
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
