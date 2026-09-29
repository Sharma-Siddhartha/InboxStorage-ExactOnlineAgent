---
name: exact-ledger-cleanup-advisor
description: Exact Online agent (Inbox Storage): turn usage evidence into the quarterly clean-up list: delete, block, clear first, keep or merge. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Ledger clean-up advisor

Follow `references/run-protocol.md` (run/step bookkeeping, query header, writes via `agent_ops_log`) and `references/conventions.md`.


Produce the quarterly (and pre-year-end) **ledger clean-up list** from the usage evidence in
EXACT.CORE.GL_USAGE. You recommend; the finance owner (ideally with the external accountant) approves,
and someone with Exact admin rights acts. You never delete or block anything.

## The four tests (all must hold for "unused")

1. No postings in the last `unused_months` (24) months, **ignoring year-end closing entries**
   (GL_USAGE already excludes `closing_entry_types`; if that setting is TBD, stop and report that the list can't be produced yet).
2. Zero balance (`ABS(BALANCE_EUR) < 0.005`).
3. Not referenced in the setup (`REFERENCED_BY IS NULL`).
4. Not used by the billing integration (`USED_BY_BILLING_INTEGRATION = FALSE`).

## Suggestion per account

| Evidence | Suggestion |
|---|---|
| `LINES_EVER = 0` and no references | **Delete**. Nothing depends on it; the nightly snapshot can recreate it. |
| Posted in the past, unused 24 months, zero balance, no references | **Block** for new postings, don't delete (7-year retention; accounts with postings generally can't be deleted). |
| Unused but balance ≠ 0 | **Clear first** (reclassify or write off, as the finance owner decides); reappears next quarter. |
| Unused but referenced | **Keep**, and show where it's referenced; remove the reference first if it should go. |
| Two accounts doing the same job (same type, same reporting line, similar description, one dormant) | **Merge**: point future postings to one, then block the other. Flag as "possible", with the evidence. |

Protected: accounts in `governance/billing_integration_accounts.yml` are never suggested, whatever the evidence.

## Output

A Markdown file `ledger-cleanup-<YYYY>-Q<n>.md`, delivered to the person as a file (to be committed to `reports/ledger-cleanup/` in the repo), one row per account:
GL code, description, type, reporting line, last posting, lines ever, balance, references, suggestion, one-line evidence.
Start with a count per suggestion. Run the same tests over cost centres, cost units, VAT codes and journals as separate tables.
Mention it in the daily summary on the day it's produced.
