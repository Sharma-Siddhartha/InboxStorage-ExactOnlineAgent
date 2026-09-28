---
name: exact-hygiene-monitor
description: Exact Online agent (Inbox Storage): posting rules R001-R005: unposted entries, wrong account type, VAT mismatches, missing cost centres, duplicate suppliers. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Hygiene monitor

Posting rules R001-R005: unposted entries, wrong account type, VAT mismatches, missing cost centres, duplicate suppliers

This monitor is **deterministic**: it evaluates written rules in Snowflake and appends findings to
`PLATFORM.AGENT_OPS.FINDINGS`. No judgment happens here; triage decides what to do with findings.

## Rules
- R001 unposted entries
- R002 wrong account type
- R003 VAT mismatch
- R004 missing cost centre
- R005 duplicate suppliers

## Run

```bash
python rules/run_rules.py --monitor exact-hygiene-monitor --run-id <run_id> --step-id <step_id>
```

Rules whose thresholds are still `TBD` in `governance/settings.yml` are skipped and reported, never guessed.
Rules with `status: draft` run, but their findings are always escalated by triage until verified.

## Changing a rule

Edit the rule file, bump `version`, open a PR with the finance owner as reviewer. Findings record the
rule version that produced them, so old and new behaviour stay distinguishable.
