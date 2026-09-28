"""Read-only Exact Online client. GET only; the single POST is the OAuth token refresh.
Respects: 60 calls/min and 5,000/day per administration, one token per 10 minutes,
and stops an endpoint after 5 errors in a run (Exact blocks the key at >10/hour)."""
from __future__ import annotations
import json, os, time
from pathlib import Path
import requests

BASE = os.environ.get("EXACT_BASE_URL", "https://start.exactonline.nl")


class ExactReadOnly:
    def __init__(self):
        self.token_file = Path(os.environ["EXACT_TOKEN_FILE"])
        self.tok = json.loads(self.token_file.read_text())
        self.errors: dict[str, int] = {}
        self.calls_today_remaining = None

    # --- auth -------------------------------------------------------------------------------------
    def _token(self) -> str:
        if time.time() < self.tok.get("expires_at", 0) - 30:
            return self.tok["access_token"]
        if time.time() - self.tok.get("issued_at", 0) < 600:        # at most one new token per 10 min
            time.sleep(600 - (time.time() - self.tok["issued_at"]))
        r = requests.post(f"{BASE}/api/oauth2/token", data={
            "grant_type": "refresh_token", "refresh_token": self.tok["refresh_token"],
            "client_id": os.environ["EXACT_CLIENT_ID"], "client_secret": os.environ["EXACT_CLIENT_SECRET"]},
            timeout=30)
        r.raise_for_status()
        new = r.json()
        now = time.time()
        self.tok = {"access_token": new["access_token"], "refresh_token": new["refresh_token"],  # refresh token rotates
                    "expires_at": now + int(new["expires_in"]), "issued_at": now}
        self.token_file.write_text(json.dumps(self.tok))
        return self.tok["access_token"]

    # --- read -------------------------------------------------------------------------------------
    def get(self, url: str, params: dict | None = None, entity: str = "") -> dict:
        if self.errors.get(entity, 0) >= 5:
            raise RuntimeError(f"{entity}: 5 errors this run, stopping to protect the API key")
        if self.calls_today_remaining is not None and self.calls_today_remaining < 200:
            raise RuntimeError("daily API budget nearly used; leaving headroom for colleagues' integrations")
        for attempt in range(3):                       # ride out short network/DNS blips
            try:
                r = requests.get(url, params=params, timeout=120,
                                 headers={"Authorization": f"Bearer {self._token()}", "Accept": "application/json"})
                break
            except requests.ConnectionError:
                if attempt == 2:
                    raise
                time.sleep(30 * (attempt + 1))
        self._respect_limits(r)
        if r.status_code >= 400:
            self.errors[entity] = self.errors.get(entity, 0) + 1
            if r.status_code == 429:
                time.sleep(60)
                return self.get(url, params, entity)
            raise requests.HTTPError(f"{r.status_code} {entity}: {r.text[:500]}", response=r)
        return r.json()["d"]

    def _respect_limits(self, r):
        rem_min = r.headers.get("X-RateLimit-Minutely-Remaining")
        reset = r.headers.get("X-RateLimit-Minutely-Reset")            # ms epoch
        if r.headers.get("X-RateLimit-Remaining"):
            self.calls_today_remaining = int(r.headers["X-RateLimit-Remaining"])
        if rem_min is not None and int(rem_min) <= 2 and reset:
            time.sleep(max(0, int(reset) / 1000 - time.time()) + 1)
        else:
            time.sleep(1.05)                                             # <= ~57 calls/min

    def pages(self, division: str, path: str, select: list[str], flt: str | None = None, entity: str = ""):
        url = f"{BASE}/api/v1/{division}/{path}"
        params = {"$select": ",".join(select)}
        if flt:
            params["$filter"] = flt
        while url:
            d = self.get(url, params, entity)
            results = d["results"] if isinstance(d, dict) and "results" in d else d
            yield results
            url, params = (d.get("__next") if isinstance(d, dict) else None), None
