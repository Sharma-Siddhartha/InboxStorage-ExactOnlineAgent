# Scheduling

Two runners, one run. Deterministic steps run on the ETL machine (IP on the Snowflake allowlist,
decision 11.13); judgment steps run as Claude scheduled tasks with this plugin installed and the
Snowflake and Slack connectors enabled. Claude joins the run the ETL machine started.

## Windows Task Scheduler (ETL machine)

| Name | Trigger | Action (start in the repo folder) |
|---|---|---|
| exact-nightly-load | daily 02:00 | `python platform/runner/run_task.py tasks/nightly-load.yml` |
| exact-aging-pass | weekdays 07:15 | `python platform/runner/run_task.py tasks/aging-pass.yml` |
| exact-daily-upkeep | weekdays 16:45 | `python platform/runner/run_task.py tasks/daily-upkeep.yml` |
| exact-ledger-cleanup | quarterly | `python platform/runner/run_task.py tasks/ledger-cleanup.yml` |
| exact-governance-sync | on merge / daily 01:30 | `python loader/sync_governance.py` |

Before the first run: `git pull` in a pre-step, so the machine always runs the merged version.

## Claude scheduled tasks (prompts)

**exact-daily-upkeep · weekdays 17:00**
> Run the Claude steps of `tasks/daily-upkeep.yml` for the Exact agent. Follow `knowledge/run-protocol.md`: join today's handed-over daily-upkeep run, then run exact-finding-triage, exact-change-proposals (only if triage succeeded) and exact-daily-summary, logging each step. Use only the Snowflake and Slack connectors; never use the Exact Online connector.

**exact-inbox · hourly, weekdays 09:00–17:00**
> Run `tasks/inbox.yml` for the Exact agent: start a run per knowledge/run-protocol.md, answer every open finance.* request in PLATFORM.AGENT_OPS.MESSAGES_OPEN with the exact-query-desk skill, and finish the run. If there are no open requests, finish immediately as succeeded.

**exact-ledger-cleanup · quarterly, 30 minutes after the ETL job**
> Run the Claude step of `tasks/ledger-cleanup.yml`: join the handed-over run and produce the clean-up list with exact-ledger-cleanup-advisor.

Phase 4+ tasks (aging-pass Claude step, weekly-forecast, close-checklist, monthly-billing-check,
year-end-pack) get prompts in the same shape when their skills are built.
