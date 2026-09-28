"""Nightly copy of the Exact setup into the repo (snapshots/<division>/*.json) and a git commit,
so `git diff` between nights shows exactly what changed. Reads EXACT.CORE (after the load)."""
from __future__ import annotations
import json, os, subprocess, sys
from datetime import date
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "lib")); sys.path.insert(0, str(ROOT / "platform" / "checks"))
load_dotenv(ROOT / ".env")
from agent_ops import Run            # noqa: E402
from pii_guard import assert_clean, mask_ibans   # noqa: E402

SNAPSHOTS = {
    "gl_accounts":  "SELECT GL_CODE, GL_DESCRIPTION, ACCOUNT_TYPE, BALANCE_TYPE, BALANCE_SIDE, DEFAULT_VAT_CODE, DEFAULT_COST_CENTER, IS_BLOCKED FROM EXACT.CORE.GL_ACCOUNTS WHERE DIVISION=%s ORDER BY GL_CODE",
    "vat_codes":    "SELECT VAT_CODE, VAT_DESCRIPTION, PERCENTAGE, VAT_TYPE, IS_BLOCKED FROM EXACT.CORE.VAT_CODES WHERE DIVISION=%s ORDER BY VAT_CODE",
    "journals":     "SELECT JOURNAL_CODE, JOURNAL_DESCRIPTION, JOURNAL_TYPE FROM EXACT.CORE.JOURNALS WHERE DIVISION=%s ORDER BY JOURNAL_CODE",
    "cost_centers": "SELECT PAYLOAD:Code::STRING CODE, PAYLOAD:Description::STRING DESCRIPTION, PAYLOAD:Active::BOOLEAN ACTIVE FROM EXACT.RAW.COST_CENTERS WHERE DIVISION=%s QUALIFY ROW_NUMBER() OVER (PARTITION BY ID ORDER BY LOADED_AT DESC)=1 ORDER BY 1",
    "cost_units":   "SELECT PAYLOAD:Code::STRING CODE, PAYLOAD:Description::STRING DESCRIPTION FROM EXACT.RAW.COST_UNITS WHERE DIVISION=%s QUALIFY ROW_NUMBER() OVER (PARTITION BY ID ORDER BY LOADED_AT DESC)=1 ORDER BY 1",
    "payment_conditions": "SELECT PAYLOAD:Code::STRING CODE, PAYLOAD:Description::STRING DESCRIPTION, PAYLOAD:PaymentDays::NUMBER DAYS FROM EXACT.RAW.PAYMENT_CONDITIONS WHERE DIVISION=%s QUALIFY ROW_NUMBER() OVER (PARTITION BY ID ORDER BY LOADED_AT DESC)=1 ORDER BY 1",
    "reporting_mapping": "SELECT a.GL_CODE, m.CLASSIFICATION_ID, m.SCHEME_ID FROM EXACT.CORE.GL_CLASSIFICATION_MAP m JOIN EXACT.CORE.GL_ACCOUNTS a ON a.GL_ACCOUNT_ID=m.GL_ACCOUNT_ID AND a.DIVISION=m.DIVISION WHERE m.DIVISION=%s ORDER BY 1,3",
}

def main():
    ver = yaml.safe_load((ROOT / "agent.yml").read_text())["version"]
    run = Run("exact", "nightly-config-snapshot", os.environ["SNOWFLAKE_ROLE"], ROOT, ver).start()
    for division in [d.strip() for d in os.environ["EXACT_DIVISIONS"].split(",") if d.strip()]:
        with run.step("exact-config-snapshot", requires_ok=False) as ctx:
            out = ROOT / "snapshots" / division; out.mkdir(parents=True, exist_ok=True)
            cur = run.conn.cursor(); n = 0
            for name, sql in SNAPSHOTS.items():
                cur.execute(run.header(skill="exact-config-snapshot") + sql, (division,))
                cols = [c[0] for c in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
                text = mask_ibans(json.dumps(rows, indent=1, ensure_ascii=False, default=str))
                assert_clean(text, f"snapshots/{division}/{name}.json")
                (out / f"{name}.json").write_text(text + "\n", encoding="utf-8"); n += len(rows)
            ctx["rows_out"] = n
    subprocess.run(["git", "-C", str(ROOT), "add", "snapshots"], check=True)
    if subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--quiet"]).returncode:
        subprocess.run(["git", "-C", str(ROOT), "commit", "-m", f"config snapshot {date.today()} (run {run.run_id})"], check=True)
        subprocess.run(["git", "-C", str(ROOT), "push"], check=True)
    run.finish()

if __name__ == "__main__":
    main()
