"""Rejects any code that could write to Exact Online. Run in CI and before every nightly job.
The loader may only issue GET; skills never call Exact at all."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATTERNS = [
    re.compile(r"\.(post|put|patch|delete)\s*\(", re.I),                 # requests.post(...)
    re.compile(r"method\s*=\s*['\"](POST|PUT|PATCH|DELETE)['\"]", re.I),
    re.compile(r"write_operation", re.I),                                 # Claude Exact connector write tool
]
ALLOW = {"platform/checks/write_guard.py", "loader/exact_client.py", "loader/authorize.py"}  # POST only to /oauth2/token

SKIP_DIRS = {".venv", "venv", "env", ".git", "site-packages", "node_modules", "__pycache__", ".pytest_cache"}

def main() -> int:
    bad = []
    for p in list(ROOT.rglob("*.py")) + list(ROOT.rglob("SKILL.md")):
        rel = p.relative_to(ROOT).as_posix()
        if rel in ALLOW or SKIP_DIRS & set(p.relative_to(ROOT).parts):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for pat in PATTERNS:
            for m in pat.finditer(text):
                line = text[: m.start()].count("\n") + 1
                bad.append(f"{rel}:{line}: {m.group(0)}")
    # exact_client: the only POST allowed is the token endpoint
    client = (ROOT / "loader/exact_client.py").read_text()
    if len(re.findall(r"requests\.post\(", client)) != 1 or "oauth2/token" not in client:
        bad.append("loader/exact_client.py: POST allowed only for /oauth2/token")
    auth = (ROOT / "loader/authorize.py").read_text()
    if len(re.findall(r"requests\.post\(", auth)) != 1 or "oauth2/token" not in auth:
        bad.append("loader/authorize.py: POST allowed only for /oauth2/token")
    for b in bad:
        print("WRITE-GUARD:", b)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())