"""
Have I Been Pwned (HIBP) Paid API v3 Engine
Integrates official HIBP API key authentication (https://haveibeenpwned.com/API/Key).
Queries breached account histories and darknet/clearnet paste dumps (Pastebin, Ghostbin)
with Troy Hunt's mandatory rate-limit backoff handling.
"""

import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import re
from typing import List, Dict, Any, Optional

USER_AGENT = "BreachSpillover-Sovereign-OSINT/3.0"
HIBP_BASE_URL = "https://haveibeenpwned.com/api/v3"

def get_hibp_api_key() -> Optional[str]:
    """Retrieves the configured HIBP API key from environment or returns None."""
    key = os.getenv("HIBP_API_KEY", "").strip()
    if not key:
        try:
            from backend.ai_engine import load_dotenv
            load_dotenv()
            key = os.getenv("HIBP_API_KEY", "").strip()
        except Exception:
            pass
    return key if key else None

def is_hibp_configured() -> bool:
    """Checks if a non-empty HIBP API key is active."""
    return get_hibp_api_key() is not None

def _make_hibp_request(endpoint: str, api_key: str, max_retries: int = 2) -> Optional[Any]:
    """Executes authenticated HTTP request to HIBP v3 with rate-limit backoff."""
    url = f"{HIBP_BASE_URL}/{endpoint}"
    headers = {
        "hibp-api-key": api_key,
        "user-agent": USER_AGENT,
        "Accept": "application/json"
    }

    req = urllib.request.Request(url, headers=headers)

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=8.0) as response:
                if response.status == 200:
                    raw = response.read().decode("utf-8", errors="ignore")
                    return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # 404 indicates target email has zero breaches/pastes in HIBP
                return []
            elif e.code == 429:
                # Rate limit encountered: inspect Retry-After header
                retry_after = e.headers.get("Retry-After", "2")
                try:
                    sleep_sec = float(retry_after) + 0.2
                except ValueError:
                    sleep_sec = 2.0
                if attempt < max_retries:
                    time.sleep(sleep_sec)
                    continue
                return None
            elif e.code == 401:
                # Invalid or expired API key
                print(f"[!] HIBP API Error 401: Unauthorized. Please verify HIBP_API_KEY in .env.")
                return None
            else:
                return None
        except Exception:
            return None

    return None

def query_hibp_breaches(email: str) -> List[Dict[str, Any]]:
    """
    Queries HIBP v3 /breachedaccount endpoint for documented data breaches.
    Requires HIBP_API_KEY in .env. Returns empty list if key is not configured.
    """
    api_key = get_hibp_api_key()
    if not api_key or not email or "@" not in email:
        return []

    cleaned_email = email.strip().lower()
    endpoint = f"breachedaccount/{urllib.parse.quote(cleaned_email)}?truncateResponse=false"
    data = _make_hibp_request(endpoint, api_key)
    if not data or not isinstance(data, list):
        return []

    results = []
    for b in data:
        data_classes = b.get("DataClasses", [])
        raw_desc = b.get("Description", "")
        clean_desc = re.sub(r'<[^>]+>', '', raw_desc).strip()

        dc_lower = [dc.lower() for dc in data_classes]
        is_critical = any(
            k in dc_lower for k in [
                "passwords", "bank account numbers", "credit cards", "social security numbers"
            ]
        )
        severity = "CRITICAL" if is_critical else "HIGH"

        results.append({
            "breach_id": b.get("Name", "").lower(),
            "breach_name": f"{b.get('Title') or b.get('Name')} Data Breach",
            "leak_type": "HISTORICAL_BREACH",
            "breach_date": b.get("BreachDate", "2023-01-01"),
            "description": clean_desc or f"Official breach event documented in Have I Been Pwned repository.",
            "threat_actor_source": "Have I Been Pwned (HIBP v3 Official)",
            "severity": severity,
            "domain": b.get("Domain", "external-platform.com"),
            "records_count": b.get("PwnCount", 0),
            "exposed_data": data_classes,
            "is_verified": b.get("IsVerified", True),
            "is_fabricated": b.get("IsFabricated", False),
            "is_sensitive": b.get("IsSensitive", False),
            "logo_path": b.get("LogoPath")
        })

    return results

def query_hibp_pastes(email: str) -> List[Dict[str, Any]]:
    """
    Queries HIBP v3 /pasteaccount endpoint for public paste dumps (Pastebin, Ghostbin).
    Returns list of discovered paste leaks.
    """
    api_key = get_hibp_api_key()
    if not api_key or not email or "@" not in email:
        return []

    cleaned_email = email.strip().lower()
    endpoint = f"pasteaccount/{urllib.parse.quote(cleaned_email)}"
    data = _make_hibp_request(endpoint, api_key)
    if not data or not isinstance(data, list):
        return []

    pastes = []
    for p in data:
        src = p.get("Source", "Pastebin")
        pid = p.get("Id", "")
        paste_url = f"https://pastebin.com/{pid}" if src.lower() == "pastebin" and pid else ""
        pastes.append({
            "source": src,
            "paste_id": pid,
            "title": p.get("Title") or f"Public {src} Dump #{pid}",
            "date": p.get("Date", "Unknown"),
            "email_count": p.get("EmailCount", 0),
            "url": paste_url,
            "context": f"Public paste dump identified on {src} (Indexed accounts: {p.get('EmailCount', 0):,})"
        })

    return pastes
