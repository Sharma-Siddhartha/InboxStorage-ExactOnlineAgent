"""Nightly export of yesterday's runs, decisions and change requests to audit/YYYY/MM/DD.json.
First fills PLATFORM.AGENT_OPS.QUERIES from Snowflake query history (tag or header comment)."""
from __future__ import annotations
import json, os, subprocess, sys
from datetime import date, timedelta
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "lib")); sys.path.insert(0, str(ROOT / "platform" / "checks"))
load_dotenv(ROOT / ".env")
from agent_ops import Run            # noqa: E402
from pii_guard import assert_clean   # noqa: E402

FILL_QUERIES = """
INSERT INTO PLATFORM.AGENT_OPS.QUERIES
SELECT q.QUERY_ID,
  COALESCE(TRY_PARSE_JSON(q.QUERY_TAG):run_id::STRING,  REGEXP_SUBSTR(q.QUERY_TEXT, 'run_id=([^ ]+)', 1, 1, 'e')),
  COALESCE(TRY_PARSE_JSON(q.QUERY_TAG):step_id::STRING, NULLIF(REGEXP_SUBSTR(q.QUERY_TEXT, 'step_id=([^ ]*)', 1, 1, 'e'), '')),
  COALESCE(TRY_PARSE_JSON(q.QUERY_TAG):agent::STRING,   REGEXP_SUBSTR(q.QUERY_TEXT, 'agent=([^ ]+)', 1, 1, 'e')),
  COALESCE(TRY_PARSE_JSON(q.QUERY_TAG):skill::STRING,   REGEXP_SUBSTR(q.QUERY_TEXT, 'skill=([^ ]+)', 1, 1, 'e')),
  q.ROLE_NAME, q.QUERY_TEXT, q.EXECUTION_STATUS, q.ERROR_MESSAGE, q.ROWS_PRODUCED, q.TOTAL_ELAPSED_TIME, q.START_TIME,
  (q.QUERY_TAG <> '' OR q.QUERY_TEXT LIKE '/* agent=%')
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
WHERE (q.ROLE_NAME IN ('AGENT_EXACT_RO', 'AGENT_EXACT_LOADER')
       OR (q.ROLE_NAME = 'MCP_ACCESS_ROLE' AND q.QUERY_TEXT LIKE '/* agent=exact%'))
  AND q.START_TIME >= DATEADD(day, -2, CURRENT_TIMESTAMP())
  AND q.QUERY_ID NOT IN (SELECT QUERY_ID FROM PLATFORM.AGENT_OPS.QUERIES WHERE START_TIME >= DATEADD(day, -3, CURRENT_TIMESTAMP()))
"""
EXPORTS = {
    "runs":            "SELECT * FROM PLATFORM.AGENT_OPS.RUNS WHERE AGENT='exact' AND EVENT_AT::DATE = %s",
    "steps":           "SELECT s.* FROM PLATFORM.AGENT_OPS.STEPS s JOIN PLATFORM.AGENT_OPS.RUNS r USING (RUN_ID) WHERE r.AGENT='exact' AND r.EVENT='started' AND r.EVENT_AT::DATE = %s",
    "decisions":       "SELECT * FROM PLATFORM.AGENT_OPS.DECISIONS WHERE AGENT='exact' AND DECIDED_AT::DATE = %s",
    "change_requests": "SELECT * FROM PLATFORM.AGENT_OPS.CHANGE_REQUESTS WHERE AGENT='exact' AND EVENT_AT::DATE = %s",
    "untagged_queries": "SELECT QUERY_ID, ROLE_NAME, START_TIME FROM PLATFORM.AGENT_OPS.QUERIES WHERE NOT TAGGED AND START_TIME::DATE = %s",
}

def main():
    ver = yaml.safe_load((ROOT / "agent.yml").read_text())["version"]
    day = date.today() - timedelta(days=1)
    run = Run("exact", "nightly-audit-export", os.environ["SNOWFLAKE_ROLE"], ROOT, ver).start()
    with run.step("exact-audit-export", requires_ok=False) as ctx:
        cur = run.conn.cursor()
        cur.execute(run.header(skill="exact-audit-export") + FILL_QUERIES)
        bundle = {}
        for name, sql in EXPORTS.items():
            cur.execute(run.header(skill="exact-audit-export") + sql, (day,))
            cols = [c[0] for c in cur.description]
            bundle[name] = [dict(zip(cols, r)) for r in cur.fetchall()]
        text = json.dumps(bundle, indent=1, default=str)
        assert_clean(text, "audit export")
        out = ROOT / "audit" / f"{day:%Y/%m}"; out.mkdir(parents=True, exist_ok=True)
        (out / f"{day:%d}.json").write_text(text + "\n"); ctx["rows_out"] = sum(len(v) for v in bundle.values())
    subprocess.run(["git", "-C", str(ROOT), "add", "audit"], check=True)
    if subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--quiet"]).returncode:
        subprocess.run(["git", "-C", str(ROOT), "commit", "-m", f"audit export {day} (run {run.run_id})"], check=True)
        subprocess.run(["git", "-C", str(ROOT), "push"], check=True)
    run.finish()

if __name__ == "__main__":
    main()
