# Billing integration (to document: decisions 11.6 and 11.8)

Storage revenue is posted straight to the ledger by the billing system's integration: the Sales Invoice
module holds only 81 invoices, the latest from 2018. So revenue is read from transaction lines.

To fill in with the billing owner:
- Which system posts (Striker?), how often, into which journal(s)?
- Every GL account it posts to (revenue, debtor control, VAT, discounts, rounding) → governance/billing_integration_accounts.yml
- Is it the source of truth for revenue? What happens on a failed sync?
