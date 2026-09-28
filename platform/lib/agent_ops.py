"""Run context shared by every agent job: creates the run before work starts, tags every
query, and records steps. Used by the nightly jobs (Python). Claude-run skills follow the same
contract by hand: see knowledge/query-header.md."""
from __future__ import annotations
import json, os, subprocess, uuid
from contextlib import contextmanager
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.primitives import serialization

OPS = "PLATFORM.AGENT_OPS"


def git_sha(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def connect(role: str, query_tag: dict | None = None):
    key = serialization.load_pem_private_key(Path(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"]).read_bytes(), password=None)
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"], user=os.environ["SNOWFLAKE_USER"], role=role,
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        private_key=key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                      serialization.NoEncryption()),
        session_parameters={"QUERY_TAG": json.dumps(query_tag or {})},
    )


class Run:
    def __init__(self, agent: str, task: str, role: str, repo: Path, agent_version: str, trigger="schedule"):
        self.agent, self.task, self.role = agent, task, role
        # A script started by the task runner joins the runner's run instead of opening its own.
        self.joined = bool(os.environ.get("EXACT_RUN_ID"))
        self.run_id = os.environ.get("EXACT_RUN_ID") or str(uuid.uuid4())
        self.repo, self.agent_version, self.trigger = repo, agent_version, trigger
        self.conn = connect(role, {"agent": agent, "run_id": self.run_id, "task": task})
        self.status = "succeeded"

    def header(self, step_id: str = "", skill: str = "") -> str:
        return f"/* agent={self.agent} run_id={self.run_id} step_id={step_id} skill={skill} */\n"

    def _event(self, event: str, note: str = ""):
        self.conn.cursor().execute(
            f"INSERT INTO {OPS}.RUNS (RUN_ID, AGENT, TASK, EVENT, CODE_VERSION, AGENT_VERSION, TRIGGER, NOTE) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (self.run_id, self.agent, self.task, event, git_sha(self.repo), self.agent_version, self.trigger, note))

    def start(self):
        if not self.joined:
            self._event("started")      # before any work: a crash still leaves a trace
        return self

    @contextmanager
    def step(self, skill: str, requires_ok: bool = True, prev_ok: bool = True, skip_reason: str | None = None):
        """One skill in the task. If requires_ok and the previous step failed, it is skipped with a reason."""
        step_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        ins = f"INSERT INTO {OPS}.STEPS (STEP_ID, RUN_ID, SKILL, EVENT, REASON, ROWS_OUT) VALUES (%s,%s,%s,%s,%s,%s)"
        if skip_reason or (requires_ok and not prev_ok):
            cur.execute(ins, (step_id, self.run_id, skill, "skipped", skip_reason or "required step did not succeed", None))
            if not skip_reason:
                self.status = "partial"
            yield None
            return
        cur.execute(f"ALTER SESSION SET QUERY_TAG = '{json.dumps({'agent': self.agent, 'run_id': self.run_id, 'step_id': step_id, 'skill': skill})}'")
        cur.execute(ins, (step_id, self.run_id, skill, "started", None, None))
        ctx = {"step_id": step_id, "rows_out": None}
        try:
            yield ctx
            cur.execute(ins, (step_id, self.run_id, skill, "succeeded", None, ctx["rows_out"]))
        except Exception as e:  # logged, then the task carries on with independent steps
            cur.execute(ins, (step_id, self.run_id, skill, "failed", str(e)[:1000], None))
            self.status = "partial"
            ctx["failed"] = True

    def finish(self, note: str = "", event: str | None = None):
        if not self.joined:
            self._event(event or self.status, note)
        self.conn.close()
