# Run protocol for Claude-run steps

Every Claude-run task and skill follows this contract, so its work shows up in the same
PLATFORM.AGENT_OPS trace as the Python jobs. Snowflake access is through the Snowflake connector
(role AGENT_EXACT_RO). The Exact Online connector is never used by any skill.

1. **Start the run before any work.**
   `SELECT UUID_STRING() AS RUN_ID;` then
   `INSERT INTO PLATFORM.AGENT_OPS.RUNS (RUN_ID, AGENT, TASK, EVENT, AGENT_VERSION, MODEL, TRIGGER) VALUES ('<run_id>', 'exact', '<task>', 'started', '<agent.yml version>', '<model>', 'schedule');`
2. **Each skill is a step.** Create a STEP_ID the same way and insert `started`, then `succeeded`, `failed` (with REASON) or `skipped` (with REASON).
3. **Every query starts with the header**, exactly:
   `/* agent=exact run_id=<run_id> step_id=<step_id> skill=<skill-name> */`
   The nightly audit export links queries to runs by this header. Queries without it are flagged as untagged.
4. **Check `requires` before a step.** If the task file says a step requires the previous one, read STEPS for this run; if the previous step didn't succeed, insert `skipped` with the reason and move on to the next independent step.
5. **Write only to PLATFORM.AGENT_OPS** (DECISIONS, CHANGE_REQUESTS, MESSAGES, STEPS, RUNS). Insert only; never UPDATE or DELETE. A status change is a new row.
6. **No personal data in anything you write**: codes, IDs, counts and amounts only. No names, e-mail addresses, IBANs, or line descriptions, including in REASON and NOTE fields and in Slack.
7. **Finish the run**: insert `succeeded`, or `partial` if any step failed or was skipped, or `failed`.

## Joining a run started by the ETL machine (mixed tasks)

For `runner: mixed` tasks the ETL machine starts the run, executes the deterministic steps and writes
`handed_over`. Claude then **joins that run** instead of starting a new one:

```sql
/* agent=exact run_id=join step_id= skill=<task> */
SELECT RUN_ID FROM PLATFORM.AGENT_OPS.RUNS_CURRENT
WHERE AGENT='exact' AND TASK='<task>' AND EVENT='handed_over' AND EVENT_AT::DATE = CURRENT_DATE()
ORDER BY EVENT_AT DESC LIMIT 1;
```

If no handed-over run exists (the ETL job didn't run), start a new run, insert a `skipped` step for
each ETL step with reason "etl run missing", run the Claude steps that don't `require` them, and
finish as `partial`. The daily summary reports it.
