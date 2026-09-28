---
name: exact-query-desk
description: Answer financial questions about Inbox Storage's Exact Online bookkeeping (revenue, cost, margin, wage cost totals, open items, ageing, cash) from Snowflake EXACT.CORE, naming the agreed definition. Use whenever anyone asks about revenue, GL accounts, margins, debtors or creditors from Exact, or when another agent sends a finance.* request.
---
# Query desk

Answer financial questions about Inbox Storage's Exact Online data, from colleagues and from other
agents (capabilities `finance.lookup`, `finance.revenue_posted`, `finance.wage_cost`,
`finance.cost_by_account`). Read only EXACT.CORE and EXACT.GOVERNANCE.

## Always

- **Name the definition and its version**: "Revenue = P&L accounts of revenue type (BalanceType W, Type 110), sign flipped; dictionary v1."
- **Say the data's freshness**: the latest `LOADED_AT` of the tables you used.
- **Codes, not names**: answer per GL code and customer code. If someone asks for a customer by name, say that names aren't loaded and ask for the customer code.
- **Wage cost only as totals** per account and period (EXACT.CORE.WAGE_COST). Never per employee, never line descriptions.
- If the definition needed doesn't exist in the dictionary, say so and propose one for the finance owner; don't improvise one silently.

## Useful views

| Question | View |
|---|---|
| Revenue by account / customer / period | EXACT.CORE.REVENUE_LINES |
| Cost and margin | EXACT.CORE.COST_LINES + governance/account_types.yml `margin` |
| Wage cost | EXACT.CORE.WAGE_COST |
| Open items and ageing | EXACT.CORE.OPEN_RECEIVABLES, OPEN_PAYABLES, AGING_BANDS |
| One customer across systems | PLATFORM.INTEGRATION.CUSTOMER_FINANCE |

## Answering other agents (inbox task)

Read open requests: `SELECT * FROM PLATFORM.AGENT_OPS.MESSAGES_OPEN WHERE TO_CAPABILITY LIKE 'finance.%'`.
Validate the payload against the capability (period, codes). Reply with a `reply` row in the same
THREAD_ID whose payload holds `{"value":..., "definition":"revenue_v1", "as_of":"<loaded_at>", "query_id":"<LAST_QUERY_ID()>"}`,
then an `answered` status row for the request. Unknown or malformed requests get an `error` reply
with the reason; never guess what was meant.
