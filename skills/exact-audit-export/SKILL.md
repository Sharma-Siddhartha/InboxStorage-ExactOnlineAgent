---
name: exact-audit-export
description: Exact Online agent (Inbox Storage): fill AGENT_OPS.QUERIES from query history, then export yesterday's runs, decisions and change requests to audit/ in GitHub. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Audit export

Fill AGENT_OPS.QUERIES from query history, then export yesterday's runs, decisions and change requests to audit/ in GitHub

Runs on the ETL machine (its IP is on the Snowflake allowlist), started by Windows Task Scheduler
through `tasks/nightly-load.yml`. Uses role `AGENT_EXACT_LOADER`.

## Run

```bash
python loader/audit_export.py
```

## Guarantees

- Exact is read with GET requests only (`platform/checks/write_guard.py` fails the job otherwise).
- Only allowlisted fields leave Exact (`loader/endpoints.yml`); bank numbers, VAT and KvK numbers and names become keyed fingerprints.
- Every run and step is logged in `PLATFORM.AGENT_OPS` before work starts.
