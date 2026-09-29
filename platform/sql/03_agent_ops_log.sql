-- Write path for Claude-run skills. The Snowflake MCP server's SQL tool stays read-only;
-- agents write to their logbook through ONE procedure, exposed as a second MCP tool.
-- The procedure only inserts, only into the five agent tables, max 1,000 rows, and refuses
-- anything that looks like an IBAN. Run as ACCOUNTADMIN.

CREATE OR REPLACE PROCEDURE PLATFORM.AGENT_OPS.LOG_ROWS(TABLE_NAME STRING, ROWS_JSON STRING)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
  t STRING;
  rws VARIANT;
  first_row VARIANT;
  cols STRING;
  sel STRING;
  stmt STRING;
BEGIN
  t := UPPER(TRIM(TABLE_NAME));
  IF (t NOT IN ('RUNS', 'STEPS', 'DECISIONS', 'CHANGE_REQUESTS', 'MESSAGES')) THEN
    RETURN 'refused: ' || t || ' is not a table agents may write';
  END IF;
  rws := TRY_PARSE_JSON(ROWS_JSON);
  IF (rws IS NULL OR TYPEOF(rws) <> 'ARRAY' OR ARRAY_SIZE(rws) = 0 OR ARRAY_SIZE(rws) > 1000) THEN
    RETURN 'refused: rows_json must be a JSON array of 1 to 1000 objects';
  END IF;
  IF (REGEXP_LIKE(ROWS_JSON, '.*[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}.*', 's')) THEN
    RETURN 'refused: the rows look like they contain an IBAN';
  END IF;
  first_row := rws[0];
  SELECT LISTAGG(COLUMN_NAME, ', ') WITHIN GROUP (ORDER BY ORDINAL_POSITION),
         LISTAGG('f.value:"' || COLUMN_NAME || '"::' ||
                 IFF(DATA_TYPE = 'NUMBER', 'NUMBER(' || NUMERIC_PRECISION || ',' || NUMERIC_SCALE || ')', DATA_TYPE), ', ')
           WITHIN GROUP (ORDER BY ORDINAL_POSITION)
    INTO :cols, :sel
    FROM PLATFORM.INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = 'AGENT_OPS' AND TABLE_NAME = :t
     AND ARRAY_CONTAINS(COLUMN_NAME::VARIANT, OBJECT_KEYS(:first_row));
  IF (cols IS NULL) THEN
    RETURN 'refused: the first row has no known columns of ' || t || ' (keys must be UPPERCASE column names)';
  END IF;
  stmt := 'INSERT INTO PLATFORM.AGENT_OPS.' || t || ' (' || cols || ') SELECT ' || sel ||
          ' FROM TABLE(FLATTEN(INPUT => PARSE_JSON(?))) f';
  EXECUTE IMMEDIATE :stmt USING (ROWS_JSON);
  RETURN 'inserted ' || SQLROWCOUNT || ' row(s) into ' || t;
END;
$$;

GRANT USAGE ON PROCEDURE PLATFORM.AGENT_OPS.LOG_ROWS(STRING, STRING) TO ROLE MCP_ACCESS_ROLE;

-- Re-create the MCP server with the read-only SQL tool unchanged plus the logbook tool.
-- (Same name, so the connector URL stays the same; reconnect in Claude to see the new tool.)
CREATE OR REPLACE MCP SERVER BUMBAL.ACTIVITIES_SCHEMA.INBOX_MCP_SERVER FROM SPECIFICATION $$
tools:
  - title: "SQL Execution Tool"
    name: "sql_exec_tool"
    type: "SYSTEM_EXECUTE_SQL"
    description: "Executes SQL queries against Inbox Storage's Snowflake warehouse."
    config:
      read_only: true
      query_timeout: 600
      warehouse: "COMPUTE_WH"
  - title: "Agent logbook: write rows"
    name: "agent_ops_log"
    type: "GENERIC"
    identifier: "PLATFORM.AGENT_OPS.LOG_ROWS"
    description: "Append rows to the department agents' logbook (PLATFORM.AGENT_OPS). table_name is one of RUNS, STEPS, DECISIONS, CHANGE_REQUESTS, MESSAGES. rows_json is a JSON array (1-1000) of objects whose keys are the table's UPPERCASE column names; omitted columns get their defaults. Insert-only: status changes are new rows. Never include names, e-mail addresses, IBANs or line descriptions."
    config:
      type: "procedure"
      warehouse: "COMPUTE_WH"
      input_schema:
        type: "object"
        properties:
          table_name:
            description: "RUNS, STEPS, DECISIONS, CHANGE_REQUESTS or MESSAGES"
            type: "string"
          rows_json:
            description: "JSON array of row objects with UPPERCASE column names as keys"
            type: "string"
$$;

GRANT USAGE ON MCP SERVER BUMBAL.ACTIVITIES_SCHEMA.INBOX_MCP_SERVER TO ROLE MCP_ACCESS_ROLE;
