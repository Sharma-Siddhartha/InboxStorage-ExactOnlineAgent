---
name: exact-master-data-sync
description: Exact Online agent (Inbox Storage): load customers, suppliers, items, cost centres, cost units, payment conditions (codes and fingerprints only). Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Master data sync

Load customers, suppliers, items, cost centres, cost units, payment conditions (codes and fingerprints only)

Runs on the ETL machine (its IP is on the Snowflake allowlist), started by Windows Task Scheduler
through `tasks/nightly-load.yml`. Uses role `AGENT_EXACT_LOADER`.

## Run

```bash
python loader/load.py --entities ACCOUNTS,BANK_ACCOUNTS,ITEMS,COST_CENTERS,COST_UNITS,PAYMENT_CONDITIONS,VAT_CODES,JOURNALS,GL_ACCOUNT_CLASSIFICATION_MAPPINGS
```

## Guarantees

- Exact is read with GET requests only (`platform/checks/write_guard.py` fails the job otherwise).
- Only allowlisted fields leave Exact (`loader/endpoints.yml`); bank numbers, VAT and KvK numbers and names become keyed fingerprints.
- Every run and step is logged in `PLATFORM.AGENT_OPS` before work starts.
