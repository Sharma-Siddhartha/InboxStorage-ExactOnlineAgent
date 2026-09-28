-- PLATFORM.AGENT_OPS: the shared logbook and mailbox for every department agent.
-- Append-only: status changes are new rows; *_CURRENT views show the latest state.
-- No IBANs, names, e-mail addresses or line descriptions in any column (see platform/checks/pii_guard.py).

CREATE TABLE IF NOT EXISTS PLATFORM.AGENT_OPS.RUNS (
  RUN_ID        STRING        NOT NULL,   -- UUID, created before any work starts
  AGENT         STRING        NOT NULL,   -- 'exact', 'hubspot', 'shiftbase', ...
  TASK          STRING        NOT NULL,   -- 'daily-upkeep', ...
  EVENT         STRING        NOT NULL,   -- 'started' | 'handed_over' | 'succeeded' | 'failed' | 'partial'
  EVENT_AT      TIMESTAMP_TZ  NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  CODE_VERSION  STRING,                   -- git commit of the agent repo
  AGENT_VERSION STRING,                   -- agent.yml version
  MODEL         STRING,                   -- model used for judgment steps, if any
  TRIGGERED_BY  STRING,                   -- 'schedule' | 'manual' | 'message'                  -- 'schedule' | 'manual' | 'message'
  NOTE          STRING
);

CREATE TABLE IF NOT EXISTS PLATFORM.AGENT_OPS.STEPS (
  STEP_ID     STRING NOT NULL,
  RUN_ID      STRING NOT NULL,
  SKILL       STRING NOT NULL,
  EVENT       STRING NOT NULL,            -- 'started' | 'succeeded' | 'failed' | 'skipped'
  EVENT_AT    TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  REASON      STRING,                     -- why skipped / failed
  ROWS_OUT    NUMBER
);

-- Filled nightly from SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY via the query tag or the
-- /* agent=... run_id=... step_id=... */ header (see platform/lib/agent_ops.py).
CREATE TABLE IF NOT EXISTS PLATFORM.AGENT_OPS.QUERIES (
  QUERY_ID           STRING NOT NULL,
  RUN_ID             STRING,
  STEP_ID            STRING,
  AGENT              STRING,
  SKILL              STRING,
  ROLE_NAME          STRING,
  QUERY_TEXT         STRING,
  EXECUTION_STATUS   STRING,
  ERROR_MESSAGE      STRING,
  ROWS_PRODUCED      NUMBER,
  TOTAL_ELAPSED_MS   NUMBER,
  START_TIME         TIMESTAMP_LTZ,
  TAGGED             BOOLEAN          -- FALSE = query from an agent role without run header
);

CREATE TABLE IF NOT EXISTS PLATFORM.AGENT_OPS.FINDINGS (
  FINDING_KEY    STRING NOT NULL,       -- stable hash of AGENT|RULE_ID|OBJECT_TYPE|OBJECT_ID
  RUN_ID         STRING NOT NULL,
  STEP_ID        STRING,
  AGENT          STRING NOT NULL,
  RULE_ID        STRING NOT NULL,
  RULE_VERSION   NUMBER NOT NULL,
  SEVERITY       STRING NOT NULL,       -- 'info' | 'low' | 'medium' | 'high'
  OBJECT_TYPE    STRING,                -- 'gl_account' | 'customer_code' | 'entry' | 'bank_line' | 'group'
  OBJECT_ID      STRING,                -- codes/IDs only
  DIVISION       STRING,
  AMOUNT_EUR     NUMBER(18,2),
  METRIC         VARIANT,               -- counts, ages, etc.
  STATUS         STRING NOT NULL,       -- 'open' | 'resolved' | 'set_aside'
  OBSERVED_AT    TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  EVIDENCE_QUERY_ID STRING              -- LAST_QUERY_ID() of the query that found it
);

CREATE TABLE IF NOT EXISTS PLATFORM.AGENT_OPS.DECISIONS (
  DECISION_ID    STRING NOT NULL,
  RUN_ID         STRING NOT NULL,
  STEP_ID        STRING,
  AGENT          STRING NOT NULL,
  FINDING_KEY    STRING,                -- or GROUP_KEY for grouped findings
  GROUP_KEY      STRING,
  OPTIONS        VARIANT,               -- ['set_aside','escalate','propose_fix','ask_agent']
  CHOICE         STRING NOT NULL,
  REASON         STRING NOT NULL,
  CONFIDENCE     FLOAT,                 -- 0..1
  RULE_ID        STRING,
  RULE_VERSION   NUMBER,
  DECIDED_AT     TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS PLATFORM.AGENT_OPS.CHANGE_REQUESTS (
  CR_ID          STRING NOT NULL,
  RUN_ID         STRING NOT NULL,
  AGENT          STRING NOT NULL,
  DECISION_ID    STRING,
  TARGET_SYSTEM  STRING NOT NULL,       -- 'exact'
  DIVISION       STRING,
  TARGET_OBJECT  STRING NOT NULL,       -- e.g. 'transaction_line', 'gl_account', 'match_set'
  TARGET_ID      STRING NOT NULL,
  FIELD          STRING,
  CURRENT_VALUE  VARIANT,
  PROPOSED_VALUE VARIANT,
  LEVEL          NUMBER NOT NULL,       -- 1 = propose, 2 = structural
  ASSIGNEE_ROLE  STRING,                -- 'bookkeeper' | 'finance_owner' | 'exact_admin'
  STATUS         STRING NOT NULL,       -- 'proposed' | 'applied' | 'confirmed' | 'mismatch' | 'rejected' | 'expired'
  EVENT_AT       TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  NOTE           STRING
);

CREATE TABLE IF NOT EXISTS PLATFORM.AGENT_OPS.MESSAGES (
  MESSAGE_ID     STRING NOT NULL,
  THREAD_ID      STRING NOT NULL,       -- request and its replies share a thread
  FROM_AGENT     STRING NOT NULL,
  TO_CAPABILITY  STRING NOT NULL,       -- e.g. 'finance.lookup'; routed via agent.yml 'offers'
  KIND           STRING NOT NULL,       -- 'request' | 'reply' | 'error'
  PAYLOAD        VARIANT NOT NULL,      -- typed; schema per capability in platform/capabilities/
  STATUS         STRING NOT NULL,       -- 'open' | 'answered' | 'failed' | 'expired'
  RUN_ID         STRING,
  EVENT_AT       TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

-- Latest-state views
CREATE OR REPLACE VIEW PLATFORM.AGENT_OPS.RUNS_CURRENT AS
SELECT * FROM PLATFORM.AGENT_OPS.RUNS
QUALIFY ROW_NUMBER() OVER (PARTITION BY RUN_ID ORDER BY EVENT_AT DESC) = 1;

CREATE OR REPLACE VIEW PLATFORM.AGENT_OPS.FINDINGS_CURRENT AS
SELECT * FROM PLATFORM.AGENT_OPS.FINDINGS
QUALIFY ROW_NUMBER() OVER (PARTITION BY FINDING_KEY ORDER BY OBSERVED_AT DESC) = 1;

CREATE OR REPLACE VIEW PLATFORM.AGENT_OPS.CHANGE_REQUESTS_CURRENT AS
SELECT * FROM PLATFORM.AGENT_OPS.CHANGE_REQUESTS
QUALIFY ROW_NUMBER() OVER (PARTITION BY CR_ID ORDER BY EVENT_AT DESC) = 1;

CREATE OR REPLACE VIEW PLATFORM.AGENT_OPS.MESSAGES_OPEN AS
SELECT * FROM PLATFORM.AGENT_OPS.MESSAGES
QUALIFY ROW_NUMBER() OVER (PARTITION BY MESSAGE_ID ORDER BY EVENT_AT DESC) = 1
  AND STATUS = 'open' AND KIND = 'request';

-- A run's full timeline, for the run number in the Slack post
CREATE OR REPLACE VIEW PLATFORM.AGENT_OPS.RUN_TIMELINE AS
SELECT r.RUN_ID, r.AGENT, r.TASK, 'step' AS KIND, s.SKILL AS WHAT, s.EVENT, s.EVENT_AT, s.REASON AS DETAIL
FROM PLATFORM.AGENT_OPS.RUNS_CURRENT r JOIN PLATFORM.AGENT_OPS.STEPS s USING (RUN_ID)
UNION ALL
SELECT q.RUN_ID, q.AGENT, NULL, 'query', q.SKILL, q.EXECUTION_STATUS, q.START_TIME, COALESCE(q.ERROR_MESSAGE, LEFT(q.QUERY_TEXT, 200))
FROM PLATFORM.AGENT_OPS.QUERIES q
UNION ALL
SELECT d.RUN_ID, d.AGENT, NULL, 'decision', d.CHOICE, d.RULE_ID, d.DECIDED_AT, d.REASON
FROM PLATFORM.AGENT_OPS.DECISIONS d;
