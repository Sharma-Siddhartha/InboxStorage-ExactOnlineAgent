"""Writes governance/*.yml and rules/*.yml to EXACT.GOVERNANCE as new versions. Run after each
merged change (CI or manually). Uses the loader role's governance grant (add: INSERT on EXACT.GOVERNANCE)."""
import json, os, sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "lib")); load_dotenv(ROOT / ".env")
from agent_ops import connect  # noqa: E402

def main():
    c = connect(os.environ["SNOWFLAKE_ROLE"], {"agent": "exact", "skill": "sync-governance"}).cursor()
    def exists(table, version):
        c.execute(f"SELECT COUNT(*) FROM EXACT.GOVERNANCE.{table} WHERE DICT_VERSION = %s", (version,))
        return c.fetchone()[0] > 0
    at = yaml.safe_load((ROOT / "governance/account_types.yml").read_text())
    for t in ([] if exists("ACCOUNT_TYPES", at["dict_version"]) else at["types"]):
        c.execute("INSERT INTO EXACT.GOVERNANCE.ACCOUNT_TYPES (ACCOUNT_TYPE,BALANCE_TYPE,LABEL,METRIC_CLASS,DEFINITION,DICT_VERSION) VALUES (%s,%s,%s,%s,%s,%s)",
                  (t["type"], t["balance"], t["label"], t["metric_class"], t["definition"], at["dict_version"]))
    st = yaml.safe_load((ROOT / "governance/settings.yml").read_text())
    for k, v in ({} if exists("SETTINGS", st["dict_version"]) else st["settings"]).items():
        c.execute("INSERT INTO EXACT.GOVERNANCE.SETTINGS (SETTING,SETTING_VALUE,DICT_VERSION) SELECT %s, PARSE_JSON(%s), %s",
                  (k, json.dumps(v), st["dict_version"]))
    bi = yaml.safe_load((ROOT / "governance/billing_integration_accounts.yml").read_text())
    for a in ([] if exists("BILLING_INTEGRATION_ACCOUNTS", bi["dict_version"]) else bi["accounts"]):
        c.execute("INSERT INTO EXACT.GOVERNANCE.BILLING_INTEGRATION_ACCOUNTS (GL_CODE,NOTE,DICT_VERSION) VALUES (%s,%s,%s)",
                  (a["gl_code"], a["note"], bi["dict_version"]))
    for f in sorted((ROOT / "rules").glob("R*.yml")):
        r = yaml.safe_load(f.read_text())
        c.execute("SELECT COUNT(*) FROM EXACT.GOVERNANCE.RULES WHERE RULE_ID=%s AND RULE_VERSION=%s", (r["id"], r["version"]))
        if c.fetchone()[0]:
            continue
        c.execute("INSERT INTO EXACT.GOVERNANCE.RULES (RULE_ID,RULE_VERSION,MONITOR,OWNER,SEVERITY,THRESHOLD,SQL_TEXT) SELECT %s,%s,%s,%s,%s,PARSE_JSON(%s),%s",
                  (r["id"], r["version"], r["monitor"], r["owner"], r["severity"], json.dumps(r.get("threshold")), r["sql"]))

if __name__ == "__main__":
    main()
