---
name: exact-daily-summary
description: Exact Online agent (Inbox Storage): post the end-of-day summary to Slack with the run number. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Daily summary

Follow `references/run-protocol.md` (run/step bookkeeping, query header, writes via `agent_ops_log`) and `references/conventions.md`.


Post one end-of-day message to the agent's Slack channel (agent.yml `slack_channel`) for the finance
owner. It must be readable in 30 seconds and traceable to the run.

## Content, in this order

1. **Header**: `Exact agent · <date> · run <first 8 chars of RUN_ID>` and the data freshness (latest load).
2. **Found and closed today**: new findings and resolved findings, counted per monitor and severity.
3. **Decisions**: counts per choice (set aside / escalated / fix proposed / asked another agent). List every **escalated** item as one line: rule, object code, amount, reason.
4. **Waiting for the bookkeeper**: change requests `proposed`, oldest first, count and oldest age; any `mismatch`.
5. **Skipped steps**: every step in this run (and last night's loads) that failed or was skipped, with its reason.
6. If nothing needs attention, say so in one line.

Totals, codes and amounts only: no names, no line descriptions, no bank details.

## Data

```sql
/* agent=exact run_id=<run_id> step_id=<step_id> skill=exact-daily-summary */
SELECT RULE_ID, SEVERITY, STATUS, COUNT(*) N, SUM(AMOUNT_EUR) AMT
FROM PLATFORM.AGENT_OPS.FINDINGS WHERE AGENT='exact' AND OBSERVED_AT::DATE = CURRENT_DATE()
GROUP BY 1,2,3;
```
plus DECISIONS and CHANGE_REQUESTS_CURRENT for today, and `PLATFORM.AGENT_OPS.RUN_TIMELINE` for skipped/failed steps.

Post with the Slack connector (send a message to the channel). If Slack is unavailable, mark the step
`failed` with the reason; the data is still in AGENT_OPS.
