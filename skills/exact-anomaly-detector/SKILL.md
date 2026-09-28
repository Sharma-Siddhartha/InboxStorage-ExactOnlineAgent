---
name: exact-anomaly-detector
description: Exact Online agent (Inbox Storage): unusual postings (amounts, timing, round numbers) for review; report-only, points to entries not people. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Anomaly detector  ·  planned (phase 6)

**Job:** Unusual postings (amounts, timing, round numbers) for review; report-only, points to entries not people

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 6
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Once there's a year of history: z-scores per account and weekday, round-number manual entries above a threshold, postings outside office hours or on closed periods. Points to entries, never to users; findings go through normal triage.

## Contract

- Reads: exact.core
- Writes: ops.findings.anomaly
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
