-- PLATFORM.INTEGRATION: one customer across systems.
-- Exact's relation number (AccountCode on transaction lines) = Striker customer code = Bumbal code,
-- so the Exact side joins without fuzzy matching. Extends the HubSpot agent's contact -> Striker link.
-- The HubSpot-side view is owned by the HubSpot agent; this view only adds Exact.

CREATE OR REPLACE VIEW PLATFORM.INTEGRATION.CUSTOMER_FINANCE AS
SELECT
  c.DIVISION,
  c.CUSTOMER_CODE,                       -- = Striker customer code
  c.IS_CUSTOMER, c.IS_SUPPLIER,
  c.PAYMENT_TERM_CODE,
  r.OPEN_RECEIVABLE_EUR,
  r.OLDEST_OPEN_DAYS,
  cb.CREDIT_BALANCE_EUR
FROM EXACT.CORE.RELATIONS c
LEFT JOIN (SELECT DIVISION, CUSTOMER_CODE, SUM(AMOUNT_OPEN_EUR) OPEN_RECEIVABLE_EUR, MAX(DAYS_OVERDUE) OLDEST_OPEN_DAYS
           FROM EXACT.CORE.OPEN_RECEIVABLES GROUP BY 1,2) r USING (DIVISION, CUSTOMER_CODE)
LEFT JOIN (SELECT DIVISION, CUSTOMER_CODE, -SUM(AMOUNT_OPEN_EUR) CREDIT_BALANCE_EUR
           FROM EXACT.CORE.OPEN_RECEIVABLES GROUP BY 1,2 HAVING SUM(AMOUNT_OPEN_EUR) < 0) cb USING (DIVISION, CUSTOMER_CODE);
