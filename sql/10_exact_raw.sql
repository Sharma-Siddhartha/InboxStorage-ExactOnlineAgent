-- EXACT.RAW: every version of every record the loader lands. Insert-only.
-- One table per endpoint, same shape. The loader creates missing tables from this template
-- (loader/load.py -> ensure_table). Only allowlisted fields reach PAYLOAD (loader/endpoints.yml).
-- A new row is written only when RECORD_HASH changes, so history = every distinct version.

-- Template (the loader substitutes the table name):
-- CREATE TABLE IF NOT EXISTS EXACT.RAW.<ENTITY> (
--   DIVISION      STRING        NOT NULL,
--   ID            STRING        NOT NULL,     -- Exact GUID
--   EXACT_TS      NUMBER,                     -- Exact 'Timestamp' (sync cursor); NULL for non-sync endpoints
--   RECORD_HASH   STRING        NOT NULL,     -- SHA2 of the allowlisted payload
--   PAYLOAD       VARIANT       NOT NULL,     -- allowlisted fields only; bank numbers replaced by fingerprints
--   LOADED_AT     TIMESTAMP_TZ  NOT NULL DEFAULT CURRENT_TIMESTAMP(),
--   RUN_ID        STRING        NOT NULL
-- );

CREATE TABLE IF NOT EXISTS EXACT.RAW.SYNC_STATE (     -- one cursor per division + endpoint
  DIVISION   STRING NOT NULL,
  ENTITY     STRING NOT NULL,
  LAST_TS    NUMBER,
  UPDATED_AT TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  RUN_ID     STRING
);

CREATE TABLE IF NOT EXISTS EXACT.RAW.DELETED (        -- from sync/Deleted: records removed in Exact
  DIVISION STRING, ENTITY_TYPE NUMBER, ENTITY_KEY STRING, DELETED_AT TIMESTAMP_TZ,
  EXACT_TS NUMBER, LOADED_AT TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(), RUN_ID STRING
);
