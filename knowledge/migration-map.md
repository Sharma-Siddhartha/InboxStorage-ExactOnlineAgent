# Migration map (vendor-neutral)

Kept so a move off Exact is manageable: GL codes don't carry over, the mapping does.

| Neutral concept | Exact field | Notes |
|---|---|---|
| ledger_account.code | GLAccounts.Code | |
| ledger_account.class | GLAccounts.Type + BalanceType | via governance/account_types.yml |
| ledger_account.reporting_line | GLAccountClassificationMappings.Classification | scheme per decision 11.16 |
| posting.date / period | TransactionLines.Date / FinancialYear, FinancialPeriod | |
| posting.amount | TransactionLines.AmountDC | debit positive |
| posting.party | TransactionLines.AccountCode | = Striker customer code |
| tax_code | VATCodes.Code | |
| journal | Journals.Code / Type | |
| cost_center / cost_unit | Costcenters.Code / Costunits.Code | |
