---
name: exact-aging-monitor
description: Exact Online agent (Inbox Storage): receivables and payables ageing against agreed thresholds (R008), grouped below materiality. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Aging monitor

Receivables and payables ageing against agreed thresholds (R008), grouped below materiality

This monitor is **deterministic**: it evaluates written rules in Snowflake and appends findings to
`PLATFORM.AGENT_OPS.FINDINGS`. No judgment happens here; triage decides what to do with findings.

## Rules
- R008 receivables ageing above materiality (payables ageing: add as R011 once thresholds are agreed)

## Run

```bash
python rules/run_rules.py --monitor exact-aging-monitor --run-id <run_id> --step-id <step_id>
```

Rules whose thresholds are still `TBD` in `governance/settings.yml` are skipped and reported, never guessed.
Rules with `status: draft` run, but their findings are always escalated by triage until verified.

## Changing a rule

Edit the rule file, bump `version`, open a PR with the finance owner as reviewer. Findings record the
rule version that produced them, so old and new behaviour stay distinguishable.
