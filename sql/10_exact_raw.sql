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

-- EXACT.RAW.DELETED (sync/Deleted) uses the standard template above; the loader creates it.
-- PAYLOAD:EntityKey = the deleted record's ID, PAYLOAD:EntityType = what kind of record it was.

-- The classification endpoint is disabled until its fields are confirmed; the table exists so
-- the CORE views that reference it compile.
CREATE TABLE IF NOT EXISTS EXACT.RAW.GL_ACCOUNT_CLASSIFICATION_MAPPINGS (
  DIVISION STRING NOT NULL, ID STRING NOT NULL, EXACT_TS NUMBER, RECORD_HASH STRING NOT NULL,
  PAYLOAD VARIANT NOT NULL, LOADED_AT TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP(), RUN_ID STRING NOT NULL
);
