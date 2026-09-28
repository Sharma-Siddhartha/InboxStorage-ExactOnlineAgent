---
name: exact-loader
description: Exact Online agent (Inbox Storage): land GL transactions, receivables, payables and master data in EXACT.RAW, read-only, on Exact's sync endpoints within the API limits. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Loader

Land GL transactions, receivables, payables and master data in EXACT.RAW, read-only, on Exact's sync endpoints within the API limits

Runs on the ETL machine (its IP is on the Snowflake allowlist), started by Windows Task Scheduler
through `tasks/nightly-load.yml`. Uses role `AGENT_EXACT_LOADER`.

## Run

```bash
python platform/checks/write_guard.py && python loader/load.py --phase 1
```

## Guarantees

- Exact is read with GET requests only (`platform/checks/write_guard.py` fails the job otherwise).
- Only allowlisted fields leave Exact (`loader/endpoints.yml`); bank numbers, VAT and KvK numbers and names become keyed fingerprints.
- Every run and step is logged in `PLATFORM.AGENT_OPS` before work starts.
