"""What breaks if a skill is removed? Reads skills/*/skill.yml (reads/writes/requires) and
tasks/*.yml, and prints Safe / Degrades / Breaks per skill, plus any skill that calls another
directly (not allowed). Usage: python platform/checks/independence_check.py [--remove SKILL]"""
import argparse, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]

def load():
    skills = {}
    for f in (ROOT / "skills").glob("*/skill.yml"):
        s = yaml.safe_load(f.read_text()); skills[s["name"]] = s
    tasks = {f.stem: yaml.safe_load(f.read_text()) for f in (ROOT / "tasks").glob("*.yml")}
    return skills, tasks

def verdict(name, skills, tasks):
    me = skills[name]
    produced = set(me.get("writes", []))
    hard, soft = [], []
    for other, s in skills.items():
        if other == name:
            continue
        needs = set(s.get("reads", [])) & produced
        # an artifact is a hard dependency unless another active skill also writes it
        alt = {a for a in needs for o, t in skills.items() if o not in (name, other) and a in t.get("writes", [])}
        for a in needs - alt:
            (soft if a in set(s.get("optional_reads", [])) else hard).append(f"{other} (reads {a})")
    offers = me.get("offers", [])
    in_tasks = [t for t, d in tasks.items() if any(st.get("skill") == name for st in d.get("steps", []))]
    if hard:
        return "Breaks", hard, in_tasks
    if soft or offers:
        return "Degrades", soft + [f"capability {c} goes unanswered" for c in offers], in_tasks
    return "Safe", [], in_tasks

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--remove")
    a = ap.parse_args()
    skills, tasks = load()
    for s in skills.values():
        if s.get("calls_skills"):
            print(f"VIOLATION: {s['name']} calls other skills directly: {s['calls_skills']}"); sys.exit(1)
    names = [a.remove] if a.remove else sorted(skills)
    for n in names:
        v, why, in_tasks = verdict(n, skills, tasks)
        print(f"{n:38} {v:9} {'; '.join(why) or '-'}" + (f"  | edit tasks: {', '.join(in_tasks)}" if in_tasks else ""))

if __name__ == "__main__":
    main()
