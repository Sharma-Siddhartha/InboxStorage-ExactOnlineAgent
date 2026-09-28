"""Evaluates rules/*.yml in Snowflake and appends findings to PLATFORM.AGENT_OPS.FINDINGS.
Thresholds come from governance/settings.yml ({name} placeholders). A finding open yesterday and
absent today is appended as 'resolved'. Called by the monitor skills:
    python rules/run_rules.py --monitor exact-hygiene-monitor --run-id <id> --step-id <id>
Rules whose thresholds are still TBD are skipped with a reason (never guessed)."""
from __future__ import annotations
import argparse, hashlib, json, os, sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "lib")); load_dotenv(ROOT / ".env")
from agent_ops import connect  # noqa: E402

SETTINGS = yaml.safe_load((ROOT / "governance/settings.yml").read_text())["settings"]


def render(sql: str) -> str:
    out = sql
    for k, v in SETTINGS.items():
        token = "{" + k + "}"
        if token in out:
            if v == "TBD" or (isinstance(v, list) and "TBD" in v):
                raise LookupError(f"setting '{k}' is TBD")
            out = out.replace(token, ", ".join(f"'{x}'" if isinstance(x, str) else str(x) for x in v) if isinstance(v, list) else str(v))
    return out


def key(rule_id, otype, oid, division):
    return hashlib.sha256(f"exact|{rule_id}|{otype}|{oid}|{division}".encode()).hexdigest()[:32]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--monitor", required=True); ap.add_argument("--run-id", required=True); ap.add_argument("--step-id", default="")
    a = ap.parse_args()
    cur = connect(os.environ.get("SNOWFLAKE_ROLE_AGENT", "AGENT_EXACT_RO"),
                  {"agent": "exact", "run_id": a.run_id, "step_id": a.step_id, "skill": a.monitor}).cursor()
    report = {"evaluated": [], "skipped": []}
    for f in sorted((ROOT / "rules").glob("R*.yml")):
        r = yaml.safe_load(f.read_text())
        if r["monitor"] != a.monitor:
            continue
        try:
            sql = render(r["sql"])
        except LookupError as e:
            report["skipped"].append({"rule": r["id"], "reason": str(e)}); continue
        header = f"/* agent=exact run_id={a.run_id} step_id={a.step_id} skill={a.monitor} rule={r['id']}v{r['version']} */\n"
        cur.execute(header + sql)
        qid = cur.sfqid
        rows = cur.fetchall()
        # all findings of a rule in one statement (row-by-row inserts took ~0.4 s each)
        batch, seen = [], set()
        for otype, oid, div, amt, metric in rows:
            k = key(r["id"], otype, oid, div); seen.add(k)
            batch.append({"k": k, "ot": otype, "oi": str(oid), "d": div, "a": float(amt) if amt is not None else None,
                          "m": json.loads(metric) if isinstance(metric, str) else metric})
        if batch:
            cur.execute(header + """INSERT INTO PLATFORM.AGENT_OPS.FINDINGS (FINDING_KEY, RUN_ID, STEP_ID, AGENT, RULE_ID, RULE_VERSION,
                           SEVERITY, OBJECT_TYPE, OBJECT_ID, DIVISION, AMOUNT_EUR, METRIC, STATUS, EVIDENCE_QUERY_ID)
                           SELECT f.value:k::STRING, %s, %s, 'exact', %s, %s, %s, f.value:ot::STRING, f.value:oi::STRING,
                                  f.value:d::STRING, f.value:a::NUMBER(18,2), f.value:m, 'open', %s
                           FROM TABLE(FLATTEN(INPUT => PARSE_JSON(%s))) f""",
                        (a.run_id, a.step_id, r["id"], r["version"], r["severity"], qid, json.dumps(batch, default=str)))
        # close this rule's open findings that were not produced today, also in one statement
        cur.execute(header + """INSERT INTO PLATFORM.AGENT_OPS.FINDINGS (FINDING_KEY, RUN_ID, STEP_ID, AGENT, RULE_ID, RULE_VERSION,
                       SEVERITY, OBJECT_TYPE, OBJECT_ID, DIVISION, STATUS)
                       SELECT c.FINDING_KEY, %s, %s, 'exact', c.RULE_ID, %s, c.SEVERITY, c.OBJECT_TYPE, c.OBJECT_ID, c.DIVISION, 'resolved'
                       FROM PLATFORM.AGENT_OPS.FINDINGS_CURRENT c
                       WHERE c.AGENT = 'exact' AND c.RULE_ID = %s AND c.STATUS = 'open'
                         AND c.FINDING_KEY NOT IN (SELECT VALUE::STRING FROM TABLE(FLATTEN(INPUT => PARSE_JSON(%s))))""",
                    (a.run_id, a.step_id, r["version"], r["id"], json.dumps(sorted(seen))))
        closed = cur.rowcount
        report["evaluated"].append({"rule": r["id"], "version": r["version"], "open": len(rows), "resolved": closed})
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
