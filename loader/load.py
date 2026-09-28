"""Nightly loader: Exact Online -> EXACT.RAW (insert-only, a new row only when a record changes).
Run on the ETL machine (IP allowlisted) by Windows Task Scheduler. Usage:
    python loader/load.py [--entities TRANSACTION_LINES,GL_ACCOUNTS] [--phase 1]"""
from __future__ import annotations
import argparse, hashlib, hmac, json, os, sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "lib"))
load_dotenv(ROOT / ".env")
from agent_ops import Run                        # noqa: E402
from exact_client import ExactReadOnly           # noqa: E402

CFG = yaml.safe_load((ROOT / "loader/endpoints.yml").read_text())
SETTINGS = yaml.safe_load((ROOT / "governance/settings.yml").read_text())["settings"]
AGENT_VERSION = yaml.safe_load((ROOT / "agent.yml").read_text())["version"]
FP_KEY = os.environ["FINGERPRINT_KEY"].encode()


def fingerprint(value) -> str | None:
    if value in (None, ""):
        return None
    norm = "".join(str(value).upper().split())
    return hmac.new(FP_KEY, norm.encode(), hashlib.sha256).hexdigest()[:24]   # keyed: not brute-forceable


WAGE_CODES: set[str] = set()   # filled at start: GL accounts of type 125/126 + settings.wage_gl_codes


def load_wage_codes(cur):
    WAGE_CODES.update(str(c) for c in SETTINGS.get("wage_gl_codes") or [])
    try:
        cur.execute("SELECT DISTINCT PAYLOAD:Code::STRING FROM EXACT.RAW.GL_ACCOUNTS WHERE PAYLOAD:Type::NUMBER IN (125, 126)")
        WAGE_CODES.update(r[0] for r in cur.fetchall())
    except Exception:
        pass   # first ever load: GL accounts not there yet; they load before transaction lines next time


def shape(entity: str, cfg: dict, rec: dict) -> dict:
    out = {k: rec.get(k) for k in cfg["fields"]}
    for src, dst in (cfg.get("fingerprint") or {}).items():
        out[dst] = fingerprint(rec.get(src))                  # the raw value is dropped here
    if cfg.get("wage_strip") and str(rec.get("GLAccountCode", "")).strip() in WAGE_CODES:
        for f in cfg["wage_strip"]:
            out[f] = None
    return out


def ensure_table(cur, entity: str):
    cur.execute(f"""CREATE TABLE IF NOT EXISTS EXACT.RAW.{entity} (
        DIVISION STRING NOT NULL, ID STRING NOT NULL, EXACT_TS NUMBER, RECORD_HASH STRING NOT NULL,
        PAYLOAD VARIANT NOT NULL, LOADED_AT TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP(), RUN_ID STRING NOT NULL)""")


def write_batch(run: Run, cur, entity: str, division: str, rows: list[dict], id_field: str, mode: str):
    """Stage one API page (up to 1,000 rows) with a single INSERT instead of one per row."""
    if not rows:
        return 0
    cur.execute(f"CREATE TEMPORARY TABLE IF NOT EXISTS STG_{entity} (DIVISION STRING, ID STRING, EXACT_TS NUMBER, RECORD_HASH STRING, PAYLOAD STRING)")
    batch = []
    for r in rows:
        payload = json.dumps(r, sort_keys=True, default=str)
        batch.append({"d": division, "i": str(r.get(id_field)), "t": r.get("Timestamp"),
                      "h": hashlib.sha256(payload.encode()).hexdigest(), "p": payload})
    cur.execute(f"""INSERT INTO STG_{entity}
        SELECT f.value:d::STRING, f.value:i::STRING, f.value:t::NUMBER, f.value:h::STRING, f.value:p::STRING
        FROM TABLE(FLATTEN(INPUT => PARSE_JSON(%s))) f""", (json.dumps(batch),))
    return len(batch)


def flush(run: Run, cur, entity: str, mode: str) -> int:
    # full-refresh lists (open items) keep every nightly state; others only store changed versions
    changed_only = "" if mode == "full" and entity.endswith("_LIST") else f"""
        LEFT JOIN (SELECT DIVISION, ID, RECORD_HASH FROM EXACT.RAW.{entity}
                   QUALIFY ROW_NUMBER() OVER (PARTITION BY DIVISION, ID ORDER BY LOADED_AT DESC) = 1) l
          ON l.DIVISION = s.DIVISION AND l.ID = s.ID
        WHERE l.RECORD_HASH IS NULL OR l.RECORD_HASH <> s.RECORD_HASH"""
    cur.execute(run.header(skill="exact-loader") + f"""
        INSERT INTO EXACT.RAW.{entity} (DIVISION, ID, EXACT_TS, RECORD_HASH, PAYLOAD, RUN_ID)
        SELECT s.DIVISION, s.ID, s.EXACT_TS, s.RECORD_HASH, PARSE_JSON(s.PAYLOAD), '{run.run_id}'
        FROM STG_{entity} s {changed_only}""")
    n = cur.rowcount
    cur.execute(f"DROP TABLE IF EXISTS STG_{entity}")
    return n


def load_entity(run: Run, api: ExactReadOnly, entity: str, cfg: dict, division: str) -> int:
    cur = run.conn.cursor()
    cur.execute("USE SCHEMA EXACT.RAW")          # staging tables live next to the RAW tables
    ensure_table(cur, entity)
    id_field = cfg.get("id_field", "ID")
    select = list(dict.fromkeys(cfg["fields"] + list((cfg.get("fingerprint") or {}).keys())))
    flt = None
    if cfg["mode"] == "sync":
        cur.execute("SELECT MAX(LAST_TS) FROM EXACT.RAW.SYNC_STATE WHERE DIVISION=%s AND ENTITY=%s", (division, entity))
        last = cur.fetchone()[0] or 1
        flt = f"Timestamp gt {int(last)}L"
    max_ts, staged = None, 0
    for page in api.pages(division, cfg["path"], select, flt, entity):
        rows = [shape(entity, cfg, r) for r in page]
        staged += write_batch(run, cur, entity, division, rows, id_field, cfg["mode"])
        ts = [int(r["Timestamp"]) for r in page if r.get("Timestamp") is not None]
        if ts:
            max_ts = max([max_ts or 0] + ts)
        if not page:
            break
    written = flush(run, cur, entity, cfg["mode"]) if staged else 0
    if max_ts:
        cur.execute("INSERT INTO EXACT.RAW.SYNC_STATE (DIVISION, ENTITY, LAST_TS, RUN_ID) VALUES (%s,%s,%s,%s)",
                    (division, entity, max_ts, run.run_id))
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entities"); ap.add_argument("--phase", type=int, default=1)
    a = ap.parse_args()
    wanted = a.entities.split(",") if a.entities else [e for e, c in CFG["entities"].items()
                                                       if c.get("enabled", True) and c.get("phase", 1) <= a.phase]
    run = Run("exact", "nightly-load", os.environ["SNOWFLAKE_ROLE"], ROOT, AGENT_VERSION).start()
    api = ExactReadOnly()
    load_wage_codes(run.conn.cursor())
    for division in [d.strip() for d in os.environ["EXACT_DIVISIONS"].split(",") if d.strip()]:
        for entity in wanted:
            with run.step(f"exact-loader:{entity}:{division}", requires_ok=False) as ctx:
                ctx["rows_out"] = load_entity(run, api, entity, CFG["entities"][entity], division)
    run.finish()
    print(f"run {run.run_id}: {run.status}")
    sys.exit(0 if run.status == "succeeded" else 1)


if __name__ == "__main__":
    main()
