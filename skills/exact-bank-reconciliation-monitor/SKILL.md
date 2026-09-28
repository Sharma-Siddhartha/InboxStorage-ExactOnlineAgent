---
name: exact-bank-reconciliation-monitor
description: Exact Online agent (Inbox Storage): unmatched bank lines (R009) and old suspense-account balances (R010). Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Bank reconciliation monitor

Unmatched bank lines (R009) and old suspense-account balances (R010)

This monitor is **deterministic**: it evaluates written rules in Snowflake and appends findings to
`PLATFORM.AGENT_OPS.FINDINGS`. No judgment happens here; triage decides what to do with findings.

## Rules
- R009 unmatched bank lines
- R010 suspense balance aged

## Run

```bash
python rules/run_rules.py --monitor exact-bank-reconciliation-monitor --run-id <run_id> --step-id <step_id>
```

Rules whose thresholds are still `TBD` in `governance/settings.yml` are skipped and reported, never guessed.
Rules with `status: draft` run, but their findings are always escalated by triage until verified.

## Changing a rule

Edit the rule file, bump `version`, open a PR with the finance owner as reviewer. Findings record the
rule version that produced them, so old and new behaviour stay distinguishable.
