# Recovery runbook (plan section 9; targets proposed, to be agreed)

| If this happens | Restore from | Steps |
|---|---|---|
| GL account, VAT code or journal deleted/changed | `snapshots/<division>/*.json` | `git log -p snapshots/<division>/gl_accounts.json` → find the last good version → Exact admin recreates/corrects it in Exact → next load confirms. |
| Values overwritten by a bad import | EXACT.RAW history | Query the last version before the import (`LOADED_AT < <import time>`), hand the before/after list to the bookkeeper as change requests. |
| Entry reversed/changed/deleted by mistake | EXACT.RAW history + RAW.DELETED | Bookkeeper corrects in Exact using the RAW record as the original; goes through a change request. |
| Integration broken / token revoked | — | Re-authorise the Exact app, write a fresh token file, re-run `loader/load.py`. Sync cursors resume from EXACT.RAW.SYNC_STATE. |
| Exact unavailable | — | Work from Snowflake; pause change requests (set task `change-proposals` to skip). |

Rehearse quarterly in a test administration.
