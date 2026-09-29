---
name: exact-finding-triage
description: Exact Online agent (Inbox Storage): decide what to do with each new finding: set aside, escalate, propose a fix, or ask another agent. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Finding triage

You go through every **new or changed open finding** of the Exact agent and make one decision per
finding (or per group of near-identical findings), with the reason written down. You never change
anything in Exact and you never contact people directly: your output is rows in
`PLATFORM.AGENT_OPS.DECISIONS` (and, for "ask another agent", a request in `MESSAGES`).

Follow `references/run-protocol.md` for the run/step bookkeeping, the query header and how to write (`agent_ops_log`).

## 1. Collect the work

```sql
/* agent=exact run_id=<run_id> step_id=<step_id> skill=exact-finding-triage */
SELECT f.*
FROM PLATFORM.AGENT_OPS.FINDINGS_CURRENT f
LEFT JOIN (SELECT FINDING_KEY, MAX(DECIDED_AT) LAST_DECIDED FROM PLATFORM.AGENT_OPS.DECISIONS
           WHERE AGENT = 'exact' GROUP BY 1) d USING (FINDING_KEY)
WHERE f.AGENT = 'exact' AND f.STATUS = 'open'
  AND (d.LAST_DECIDED IS NULL OR f.RULE_VERSION > (SELECT MAX(RULE_VERSION) FROM PLATFORM.AGENT_OPS.DECISIONS x WHERE x.FINDING_KEY = f.FINDING_KEY))
ORDER BY CASE f.SEVERITY WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END, ABS(f.AMOUNT_EUR) DESC NULLS LAST;
```

A finding already decided keeps its decision until its rule version changes or it reopens.

## 2. Group before deciding

Findings with the same `RULE_ID` and the same cause (same GL account, same VAT code pair, same
journal) are one group: make one decision with a `GROUP_KEY` = `RULE_ID|<shared attribute>`, and
list the member FINDING_KEYs in `OPTIONS.members`. The `below_materiality` summary from R008 is
always its own single decision.

## 3. Decide: four options, pick one

| Choice | Use when | Level |
|---|---|---|
| `set_aside` | Expected or harmless: e.g. a setup change that matches a change request already confirmed; a VAT mismatch on an account the dictionary marks as mixed-use; below materiality. **The reason must say why it's harmless.** | 0 |
| `escalate` | A person must judge: high severity with no clear fix; a structural issue (level 2: new GL account, VAT code change, mapping); supplier bank change; anything touching wage cost; anything where you are < 0.6 confident. | 0 |
| `propose_fix` | The fix is a single, reversible bookkeeping action with a clear current and proposed value: reclassify a line to another GL account, add a missing cost centre, match a receipt to an invoice. | 1 |
| `ask_agent` | The answer lives in another system: revenue gap vs billing (`billing.invoiced_totals`), won deal without revenue (`crm.won_deals`), wage cost vs hours (`workforce.hours`). | 0 |

Hard rules:
- Never `set_aside` a **high** finding without the finance owner's documented reason in the rule file or a confirmed change request.
- Rule `status: draft` findings are always `escalate` with reason "rule not yet verified", never `propose_fix`.
- Supplier bank-detail changes (R-supplier) are **always** `escalate`: the change must be confirmed with the supplier by phone before a payment run.
- Level-2 (structural) findings are never `propose_fix`.

## 4. Write the decisions

Write all decisions of this step in **one** `agent_ops_log` call (table `DECISIONS`), one row per
finding, members of a group sharing GROUP_KEY, REASON and CONFIDENCE:

```json
[{"DECISION_ID":"<uuid>","RUN_ID":"<run_id>","STEP_ID":"<step_id>","AGENT":"exact",
  "FINDING_KEY":"<finding_key>","GROUP_KEY":"R003|gl8000",
  "OPTIONS":{"considered":["set_aside","escalate","propose_fix","ask_agent"]},
  "CHOICE":"escalate","REASON":"<one or two sentences, codes and amounts only>",
  "CONFIDENCE":0.8,"RULE_ID":"R003","RULE_VERSION":1}]
```

Get UUIDs from `SELECT UUID_STRING() FROM TABLE(GENERATOR(ROWCOUNT => n))`. For `ask_agent`, also
write a `request` row to `MESSAGES` (TO_CAPABILITY set, typed PAYLOAD) and put its MESSAGE_ID in OPTIONS.

## 5. Step output

Set `ROWS_OUT` to the number of decisions written, and finish the step. Report counts per choice
back to the task (the daily summary reads DECISIONS itself).
