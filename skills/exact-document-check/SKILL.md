---
name: exact-document-check
description: Exact Online agent (Inbox Storage): purchase entries without a supporting document, or whose e-invoice differs from the booking. Use when the Exact agent's tasks run this step, or when someone asks the Exact agent to do this job.
---
# Document check  ·  planned (phase 4)

**Job:** Purchase entries without a supporting document, or whose e-invoice differs from the booking

**Status:** specification only. Not scheduled in any task yet. Build it in roadmap phase 4
(plan section 10) once its inputs exist.

## Design notes (from plan v0.4)

Purchase entries (journal type purchase) without a document attached (DOCUMENTS by FinancialTransactionEntryID), and e-invoices whose amount, VAT or due date differ from the booking.

## Contract

- Reads: exact.core
- Writes: ops.findings.documents
- Offers: —
- Uses: —

Follow `knowledge/run-protocol.md` and `knowledge/conventions.md`.
