# Exact Online agent · Inbox Storage

The third department agent on the shared platform (after HubSpot and Shiftbase), built from
*The Exact Online Agent* plan v0.4 (`knowledge/plan-v0.4.pdf`). It looks after the bookkeeping
data the way a small finance-operations team would, and **never writes to Exact**.

**An agent here = skills + tasks that sequence them + a manifest (`agent.yml`) + permissions +
its records in Snowflake and GitHub.** Claude supplies judgment inside a few skills (triage,
change proposals, query desk, summary, clean-up advice); everything else is deterministic.

## Map of the repo

| Path | What it is | Plan section |
|---|---|---|
| `agent.yml` | Manifest: owns, offers, uses, permissions, administrations | 5 |
| `platform/sql/` | Roles, `PLATFORM.AGENT_OPS` (runs, steps, queries, findings, decisions, change requests, messages), `PLATFORM.INTEGRATION` | 6, 8 |
| `platform/lib/agent_ops.py` | Run context: run before work, query tags, steps | 8 |
| `platform/runner/run_task.py` | Runs the ETL steps of a task, hands the run to Claude | 4 |
| `platform/checks/` | Write guard, PII guard, independence checker | 5, 7 |
| `sql/` | `EXACT.RAW` (every version), `EXACT.CORE` (clean views), `EXACT.GOVERNANCE` (dictionary, settings, rules) | 6 |
| `loader/` | Read-only Exact client, field allowlist, nightly load, config snapshot, audit export, governance sync | 2, 7 |
| `rules/` | R001–R010 + rule runner | 3 |
| `governance/` | Account-type dictionary, thresholds, billing-integration accounts | 3, 11 |
| `skills/` | 31 skills, each `SKILL.md` + `skill.yml` (reads / writes / phase) | 5 |
| `tasks/` | 9 task files: order, schedule, `after` / `requires` | 4 |
| `knowledge/` | Run protocol, conventions, scheduling, runbook, migration map, billing integration | 9 |
| `snapshots/`, `audit/`, `reports/` | Written nightly / quarterly by the agent | 3, 9 |

Phases 1–3 are active (`status: active`); phases 4–6 skills are specifications (`status: planned`)
and are skipped by the tasks until `EXACT_AGENT_PHASE` is raised.

## Setting it up (phase 1)

1. **Snowflake** (as SYSADMIN/SECURITYADMIN): run `platform/sql/00_roles.sql`, `01_agent_ops.sql`,
   `sql/10_exact_raw.sql`, `sql/30_exact_governance.sql`. Create users `AGENT_EXACT_LOADER` (key-pair)
   and grant the roles. Add the ETL machine's IP to the network policy.
2. **Exact app**: register an app in the Exact App Center with read scopes only; authorise once and
   save the token JSON (`access_token`, `refresh_token`, `expires_at`, `issued_at`) at `EXACT_TOKEN_FILE`.
3. **ETL machine**: clone the repo, `pip install -r requirements.txt`, fill `.env` from `.env.example`
   (including a long random `FINGERPRINT_KEY`).
4. `python loader/sync_governance.py`, then first load: `python platform/runner/run_task.py tasks/nightly-load.yml`.
   The initial transaction-line sync (2007 onwards, ~325k+ lines at 1,000 per call) fits one day's API budget.
5. Run `sql/20_exact_core.sql` and `platform/sql/02_integration.sql` (the views need the RAW tables to exist).
6. **Verify** every `[VERIFY]` in `sql/20_exact_core.sql`, `rules/` and `loader/endpoints.yml` against the loaded data
   (status codes, journal types, closing-entry type, classification endpoint). Then set `closing_entry_types`.
7. Schedule per `knowledge/scheduled-tasks.md`; install the plugin (`.claude-plugin/`) in Claude with the
   Snowflake and Slack connectors.

## Before changing anything

```bash
python -m pytest tests                                  # write guard, PII guard, rule/task/skill contracts
python platform/checks/independence_check.py            # Safe / Degrades / Breaks per skill
python platform/checks/independence_check.py --remove exact-daily-summary
```
Every change goes through a PR; bump `version` in `agent.yml` (and in a rule file when its logic changes).

## Open decisions wired into the code (plan section 11)

`TBD` values block only the parts that depend on them; nothing is guessed.

| Decision | Where it plugs in |
|---|---|
| Finance owner, bookkeeper | `agent.yml` |
| Materiality threshold | `governance/settings.yml` → R008 skipped until set |
| Billing-integration accounts | `governance/billing_integration_accounts.yml` (8000/8001/8020/8021 pre-filled) |
| Reporting scheme | `settings.yml: reporting_scheme_id` → R007 skipped until set |
| Suspense accounts, wage accounts, standard payment terms | `settings.yml` |
| Kubox administration | `agent.yml: administrations`, `.env: EXACT_DIVISIONS` |
| Fixed Assets module | `loader/endpoints.yml: ASSETS` (disabled) |
| Unmatched-receipts endpoint | `loader/endpoints.yml: UNMATCHED_RECEIPTS` (phase 4, to verify) |
| Slack channel | `agent.yml: slack_channel` |
| Exact connector after 25 Oct | not used by any skill; `agent.yml: exact_connector_write: false` |
