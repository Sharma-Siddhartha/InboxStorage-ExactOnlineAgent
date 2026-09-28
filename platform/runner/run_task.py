"""Runs the etl steps of a task file (tasks/*.yml) and starts the run that Claude steps join.
Usage: python platform/runner/run_task.py tasks/daily-upkeep.yml
Steps with a phase above agent.yml's current phase are skipped with a logged reason."""
import os, subprocess, sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "platform" / "lib")); load_dotenv(ROOT / ".env")
from agent_ops import Run  # noqa: E402

CURRENT_PHASE = int(os.environ.get("EXACT_AGENT_PHASE", "3"))
FOUNDATION = {
    "exact-loader": [sys.executable, "loader/load.py", "--phase", str(CURRENT_PHASE)],
    "exact-master-data-sync": [sys.executable, "loader/load.py", "--entities",
                               "ACCOUNTS,BANK_ACCOUNTS,ITEMS,COST_CENTERS,COST_UNITS,PAYMENT_CONDITIONS,VAT_CODES,JOURNALS"],
    "exact-config-snapshot": [sys.executable, "loader/config_snapshot.py"],
    "exact-audit-export": [sys.executable, "loader/audit_export.py"],
}

def main(task_file: str):
    t = yaml.safe_load(Path(task_file).read_text())
    ver = yaml.safe_load((ROOT / "agent.yml").read_text())["version"]
    if subprocess.run([sys.executable, "platform/checks/write_guard.py"], cwd=ROOT).returncode:
        sys.exit("write guard failed: refusing to run")
    run = Run("exact", t["task"], os.environ["SNOWFLAKE_ROLE"], ROOT, ver).start()
    ok = {}
    for st in t["steps"]:
        runner = st.get("runner", t["runner"])
        if runner != "etl":
            continue                                   # Claude joins this run for its steps
        name, need = st["skill"], st.get("requires")
        if st.get("phase", 0) > CURRENT_PHASE:
            with run.step(name, skip_reason=f"phase {st['phase']} not yet active"):
                pass
            ok[name] = False
            continue
        with run.step(name, requires_ok=bool(need), prev_ok=ok.get(need, True) if need else True) as ctx:
            if ctx is None:
                ok[name] = False; continue
            cmd = FOUNDATION.get(name) or [sys.executable, "rules/run_rules.py", "--monitor", name,
                                           "--run-id", run.run_id, "--step-id", ctx["step_id"]]
            subprocess.run(cmd, cwd=ROOT, check=True, env={**os.environ, "EXACT_RUN_ID": run.run_id})
        ok[name] = not (ctx or {}).get("failed", False)
    print(run.run_id)
    claude_pending = any(s.get("runner", t["runner"]) == "claude" for s in t["steps"])
    # mixed tasks: hand the open run to Claude, which writes the final event
    run.finish("etl steps done; claude steps pending" if claude_pending else "", event="handed_over" if claude_pending else None)

if __name__ == "__main__":
    main(sys.argv[1])
