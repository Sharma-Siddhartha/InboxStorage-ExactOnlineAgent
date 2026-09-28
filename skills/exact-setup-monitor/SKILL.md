---
name: exact-setup-monitor
description: Exact Online agent (Inbox Storage): setup rules R006-R007 (chart changes, reporting-mapping gaps) and usage evidence for every account, cost centre, VAT code and journal. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Setup monitor

Setup rules R006-R007 (chart changes, reporting-mapping gaps) and usage evidence for every account, cost centre, VAT code and journal

This monitor is **deterministic**: it evaluates written rules in Snowflake and appends findings to
`PLATFORM.AGENT_OPS.FINDINGS`. No judgment happens here; triage decides what to do with findings.

## Rules
- R006 setup change
- R007 reporting-mapping gap
- usage evidence: EXACT.CORE.GL_USAGE (view, refreshed with every load)

## Run

```bash
python rules/run_rules.py --monitor exact-setup-monitor --run-id <run_id> --step-id <step_id>
```

Rules whose thresholds are still `TBD` in `governance/settings.yml` are skipped and reported, never guessed.
Rules with `status: draft` run, but their findings are always escalated by triage until verified.

## Changing a rule

Edit the rule file, bump `version`, open a PR with the finance owner as reviewer. Findings record the
rule version that produced them, so old and new behaviour stay distinguishable.
