"""One-time Exact Online authorisation for the loader. Run once on the ETL machine:
    python loader/authorize.py
Exact requires a public HTTPS redirect URI, so there is no local callback server:
you log in in the browser, Exact redirects to EXACT_REDIRECT_URI with ?code=... in
the address bar, and you paste that full address here. The page itself may show
anything (even a 404): only the code in the address matters. The code is valid for
a few minutes, so paste it straight away.
Writes EXACT_TOKEN_FILE in the format loader/exact_client.py expects."""
import json, os, sys, time, urllib.parse
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
BASE = os.environ.get("EXACT_BASE_URL", "https://start.exactonline.nl")
CLIENT_ID = os.environ["EXACT_CLIENT_ID"]
REDIRECT = os.environ["EXACT_REDIRECT_URI"]

def main():
    if not REDIRECT.startswith("https://"):
        sys.exit("EXACT_REDIRECT_URI must be a public https:// URL (Exact rejects others).")
    auth_url = f"{BASE}/api/oauth2/auth?" + urllib.parse.urlencode(
        {"client_id": CLIENT_ID, "redirect_uri": REDIRECT, "response_type": "code", "force_login": "0"})
    print("\n1. Open this URL and log in with the Exact account the loader should use:\n")
    print("   " + auth_url + "\n")
    pasted = input("2. Paste the full address you were redirected to: ").strip()
    code = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query).get("code", [pasted])[0]
    r = requests.post(f"{BASE}/api/oauth2/token", data={
        "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
        "client_id": CLIENT_ID, "client_secret": os.environ["EXACT_CLIENT_SECRET"]}, timeout=30)
    if r.status_code != 200:
        sys.exit(f"Token request failed ({r.status_code}): {r.text[:300]}")
    t = r.json(); now = time.time()
    out = Path(os.environ["EXACT_TOKEN_FILE"]); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"access_token": t["access_token"], "refresh_token": t["refresh_token"],
                               "expires_at": now + int(t["expires_in"]), "issued_at": now}))
    # sanity check: which user and division did we get?
    me = requests.get(f"{BASE}/api/v1/current/Me?$select=CurrentDivision,UserName",
                      headers={"Authorization": f"Bearer {t['access_token']}", "Accept": "application/json"}, timeout=30)
    d = me.json()["d"]["results"][0] if me.ok else {}
    print(f"\nToken saved to {out}.\nLogged in as: {d.get('UserName', '?')}; current division: {d.get('CurrentDivision', '?')}")
    print("Put the division number(s) in EXACT_DIVISIONS in .env.")

if __name__ == "__main__":
    main()