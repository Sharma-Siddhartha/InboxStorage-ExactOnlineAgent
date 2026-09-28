"""Static checks run in CI (no Snowflake needed): python -m pytest tests"""
import subprocess, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]

def test_write_guard():
    assert subprocess.run([sys.executable, "platform/checks/write_guard.py"], cwd=ROOT).returncode == 0

def test_no_pii_in_repo_outputs():
    for d in ("snapshots", "audit"):
        assert subprocess.run([sys.executable, "platform/checks/pii_guard.py", d], cwd=ROOT).returncode == 0

def test_rules_well_formed():
    for f in (ROOT / "rules").glob("R*.yml"):
        r = yaml.safe_load(f.read_text())
        for k in ("id", "version", "monitor", "owner", "severity", "sql"):
            assert k in r, f"{f.name} missing {k}"
        assert (ROOT / "skills" / r["monitor"]).exists(), f"{f.name}: unknown monitor"

def test_tasks_reference_existing_skills():
    skills = {p.name for p in (ROOT / "skills").iterdir()}
    for f in (ROOT / "tasks").glob("*.yml"):
        for st in yaml.safe_load(f.read_text())["steps"]:
            assert st["skill"] in skills, f"{f.name}: {st['skill']}"

def test_every_skill_has_contract():
    for d in (ROOT / "skills").iterdir():
        meta = yaml.safe_load((d / "skill.yml").read_text())
        assert meta["name"] == d.name and "reads" in meta and "writes" in meta
        assert (d / "SKILL.md").read_text().startswith("---\nname: " + d.name)
