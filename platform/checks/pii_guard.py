"""Blocks anything that looks like an IBAN, card number, e-mail or access token from logs,
snapshots and audit exports. Called by audit_export.py and config_snapshot.py before writing,
and in CI over snapshots/ and audit/."""
import re, sys
from pathlib import Path

IBAN  = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b")
CARD  = re.compile(r"\b(?:\d[ -]?){13,19}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
TOKEN = re.compile(r"\b(eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{10,}|gAAAA[\w-]{20,}|Bearer\s+[\w.-]{20,})\b")

def luhn(s: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", s)][::-1]
    if not 13 <= len(d) <= 19:
        return False
    total = sum(d[0::2]) + sum(sum(divmod(2 * x, 10)) for x in d[1::2])
    return total % 10 == 0

def scan(text: str) -> list[str]:
    hits = [f"IBAN-like: {m.group(0)[:6]}…" for m in IBAN.finditer(text)]
    hits += [f"card-like: {m.group(0)[:4]}…" for m in CARD.finditer(text) if luhn(m.group(0))]
    hits += [f"e-mail: …@{m.group(0).split('@')[1]}" for m in EMAIL.finditer(text)]
    hits += ["token-like" for _ in TOKEN.finditer(text)]
    return hits

def assert_clean(text: str, where: str):
    hits = scan(text)
    if hits:
        raise ValueError(f"PII guard blocked write to {where}: {hits[:5]}")

if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bad = 0
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".json", ".csv", ".md", ".yml", ".yaml", ".txt"}:
            for h in scan(p.read_text(errors="ignore")):
                print(f"PII-GUARD: {p}: {h}"); bad += 1
    sys.exit(1 if bad else 0)
