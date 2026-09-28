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
        seen = set()
        for otype, oid, div, amt, metric in rows:
            k = key(r["id"], otype, oid, div); seen.add(k)
            cur.execute("""INSERT INTO PLATFORM.AGENT_OPS.FINDINGS (FINDING_KEY, RUN_ID, STEP_ID, AGENT, RULE_ID, RULE_VERSION, SEVERITY,
                           OBJECT_TYPE, OBJECT_ID, DIVISION, AMOUNT_EUR, METRIC, STATUS, EVIDENCE_QUERY_ID)
                           SELECT %s,%s,%s,'exact',%s,%s,%s,%s,%s,%s,%s,PARSE_JSON(%s),'open',%s""",
                        (k, a.run_id, a.step_id, r["id"], r["version"], r["severity"], otype, str(oid), div, amt,
                         metric if isinstance(metric, str) else json.dumps(metric), qid))
        # close findings of this rule that were open and are no longer produced
        cur.execute("""SELECT FINDING_KEY, OBJECT_TYPE, OBJECT_ID, DIVISION FROM PLATFORM.AGENT_OPS.FINDINGS_CURRENT
                       WHERE AGENT='exact' AND RULE_ID=%s AND STATUS='open'""", (r["id"],))
        closed = 0
        for k, otype, oid, div in cur.fetchall():
            if k not in seen:
                cur.execute("""INSERT INTO PLATFORM.AGENT_OPS.FINDINGS (FINDING_KEY, RUN_ID, STEP_ID, AGENT, RULE_ID, RULE_VERSION,
                               SEVERITY, OBJECT_TYPE, OBJECT_ID, DIVISION, STATUS) VALUES (%s,%s,%s,'exact',%s,%s,%s,%s,%s,%s,'resolved')""",
                            (k, a.run_id, a.step_id, r["id"], r["version"], r["severity"], otype, oid, div)); closed += 1
        report["evaluated"].append({"rule": r["id"], "version": r["version"], "open": len(rows), "resolved": closed})
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
