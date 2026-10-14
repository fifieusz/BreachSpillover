"""
BreachSpillover - Public Leaks & Credential Exposure Aggregator
Coordinates live threat intelligence across public breach indexes, stealer repositories,
open paste aggregators, and free/community credential lookup services:

1. XposedOrNot Live Network (130M+ Breaches & Pastes)
2. Hudson Rock Cavalier Cybercrime Intelligence (Infostealer logs, unmasked passwords)
3. HIBP Pwned Passwords k-Anonymity Index (800M+ real breached passwords)
4. LeakCheck Community / Public Lookup API
5. BreachDirectory RapidAPI / Public Connector
6. Snusbase Threat Intelligence Connector (optional API key)
7. DeHashed Credential Lake Connector (optional API key)
8. Live Public Pastebin/JustPaste/Rentry Combolist Scraper & Parser
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import concurrent.futures
from typing import List, Dict, Any, Optional

USER_AGENT = "BreachSpillover-Sovereign-OSINT/3.0"

# Public Leak Engines Status
ENGINE_REGISTRY = [
    {
        "id": "xposedornot",
        "name": "XposedOrNot Live Threat Network",
        "type": "PUBLIC_API",
        "description": "Global breach index analyzing 130M+ compromised records and data classes.",
        "requires_key": False,
        "is_active": True
    },
    {
        "id": "hudson_rock",
        "name": "Hudson Rock Cavalier Cybercrime Intelligence",
        "type": "STEALER_C2_INTEL",
        "description": "Exfiltrated plaintext passwords and active malware infections (RedLine, LummaC2, Vidar).",
        "requires_key": False,
        "is_active": True
    },
    {
        "id": "hibp_passwords",
        "name": "HIBP Pwned Passwords (k-Anonymity)",
        "type": "GLOBAL_HASH_DATABASE",
        "description": "Searches 800M+ real compromised passwords via privacy-preserving 5-char SHA-1 range queries.",
        "requires_key": False,
        "is_active": True
    },
    {
        "id": "paste_harvester",
        "name": "Live Combolist & Pastebin Harvester",
        "type": "PASTE_DUMP_PARSER",
        "description": "Active search & extraction of email:password combinations across Pastebin, JustPaste, Rentry, Ghostbin.",
        "requires_key": False,
        "is_active": True
    },
    {
        "id": "leakcheck",
        "name": "LeakCheck Public & Community Engine",
        "type": "BREACH_AGGREGATOR",
        "description": "Public database of thousands of compromised databases and combolists.",
        "requires_key": False,
        "is_active": True
    },
    {
        "id": "breachdirectory",
        "name": "BreachDirectory Engine",
        "type": "BREACH_AGGREGATOR",
        "description": "Searches across billions of leaked records with optional RapidAPI key.",
        "requires_key": False,
        "is_active": True
    },
    {
        "id": "snusbase",
        "name": "Snusbase Threat Intelligence",
        "type": "PREMIUM_CONNECTOR",
        "description": "10B+ credential repository (active when SNUSBASE_API_KEY is configured).",
        "requires_key": True,
        "is_active": bool(os.getenv("SNUSBASE_API_KEY"))
    },
    {
        "id": "dehashed",
        "name": "DeHashed Credential Lake",
        "type": "PREMIUM_CONNECTOR",
        "description": "Cleartext and hashed credential lake (active when DEHASHED_API_KEY is configured).",
        "requires_key": True,
        "is_active": bool(os.getenv("DEHASHED_API_KEY"))
    }
]

def get_active_engines_summary() -> List[Dict[str, Any]]:
    """Returns the catalog of configured and operational public leaks engines."""
    engines = []
    for eng in ENGINE_REGISTRY:
        item = dict(eng)
        if item["id"] == "snusbase":
            item["is_active"] = bool(os.getenv("SNUSBASE_API_KEY"))
        elif item["id"] == "dehashed":
            item["is_active"] = bool(os.getenv("DEHASHED_API_KEY"))
        elif item["id"] == "breachdirectory":
            item["has_key"] = bool(os.getenv("BREACHDIRECTORY_API_KEY"))
        elif item["id"] == "leakcheck":
            item["has_key"] = bool(os.getenv("LEAKCHECK_API_KEY"))
        engines.append(item)
    return engines


def query_leakcheck_public(email: str, timeout: float = 3.5) -> List[Dict[str, Any]]:
    """
    Queries LeakCheck's public and community API endpoint.
    If LEAKCHECK_API_KEY is configured, queries the full authenticated endpoint.
    """
    cleaned_email = email.strip().lower()
    api_key = os.getenv("LEAKCHECK_API_KEY", "").strip()
    results = []

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
        url = f"https://leakcheck.io/api/v2/query/{urllib.parse.quote(cleaned_email)}"
    else:
        url = f"https://leakcheck.io/api/v2/public?check={urllib.parse.quote(cleaned_email)}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
                # Handle public format
                sources = payload.get("sources", []) or payload.get("result", []) or []
                for s in sources:
                    s_name = s.get("name") if isinstance(s, dict) else str(s)
                    s_date = s.get("date", "2023-01-01") if isinstance(s, dict) else "2023-01-01"
                    plain = s.get("password") if isinstance(s, dict) else None
                    hsh = s.get("hash") if isinstance(s, dict) else None

                    item = {
                        "breach_id": f"leakcheck_{re.sub(r'[^a-zA-Z0-9]', '_', s_name.lower())}",
                        "breach_name": f"{s_name} Leak",
                        "leak_type": "DATABASE_LEAK",
                        "breach_date": s_date if len(s_date) >= 10 else f"{s_date[:4]}-01-01",
                        "description": f"Compromised credentials documented in LeakCheck public database index ({s_name}).",
                        "threat_actor_source": "LeakCheck Threat Database",
                        "severity": "CRITICAL" if plain else "HIGH",
                        "domain": f"{re.sub(r'[^a-zA-Z0-9]', '', s_name.lower())}.com",
                        "records_count": 1,
                        "exposed_data": ["Email addresses", "Passwords"] if (plain or hsh) else ["Email addresses", "Account Metadata"]
                    }
                    if plain:
                        item["top_passwords"] = [plain]
                    if hsh:
                        item["raw_hash"] = hsh
                    results.append(item)
    except Exception:
        pass

    return results


def query_breachdirectory_public(email: str, timeout: float = 3.5) -> List[Dict[str, Any]]:
    """
    Queries BreachDirectory for compromised database entries.
    Supports BREACHDIRECTORY_API_KEY if configured in .env.
    """
    api_key = os.getenv("BREACHDIRECTORY_API_KEY", "").strip()
    if not api_key:
        return []

    cleaned_email = email.strip().lower()
    results = []
    url = f"https://breachdirectory.p.rapidapi.com/?func=auto&term={urllib.parse.quote(cleaned_email)}"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "breachdirectory.p.rapidapi.com",
        "User-Agent": USER_AGENT
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
                res_list = payload.get("result", []) or []
                for idx, r in enumerate(res_list):
                    src_list = r.get("sources", ["BreachDirectory Index"])
                    src_name = src_list[0] if src_list else "BreachDirectory Index"
                    password = r.get("password")
                    hash_val = r.get("hash")
                    
                    item = {
                        "breach_id": f"bd_{re.sub(r'[^a-zA-Z0-9]', '_', src_name.lower())}_{idx}",
                        "breach_name": f"{src_name} Breach Record",
                        "leak_type": "DATABASE_LEAK",
                        "breach_date": "2023-01-01",
                        "description": f"Exfiltrated record verified via BreachDirectory threat intelligence ({src_name}).",
                        "threat_actor_source": "BreachDirectory Threat Lake",
                        "severity": "CRITICAL" if password else "HIGH",
                        "domain": "external-leak.net",
                        "records_count": 1,
                        "exposed_data": ["Email addresses", "Passwords"] if (password or hash_val) else ["Email addresses"]
                    }
                    if password and not password.startswith("$2a$"):
                        item["top_passwords"] = [password]
                    elif hash_val:
                        item["raw_hash"] = hash_val
                    results.append(item)
    except Exception:
        pass

    return results


def query_dehashed_api(email: str, timeout: float = 4.0) -> List[Dict[str, Any]]:
    """
    Queries DeHashed API when DEHASHED_API_KEY and DEHASHED_EMAIL are configured in .env.
    """
    api_key = os.getenv("DEHASHED_API_KEY", "").strip()
    account_email = os.getenv("DEHASHED_EMAIL", "").strip()
    if not api_key or not account_email:
        return []

    cleaned_email = email.strip().lower()
    results = []
    url = f"https://api.dehashed.com/search?query=email:{urllib.parse.quote(cleaned_email)}"
    import base64
    auth_str = base64.b64encode(f"{account_email}:{api_key}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_str}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
                entries = payload.get("entries", []) or []
                for idx, entry in enumerate(entries):
                    db_name = entry.get("database_name") or "DeHashed Exfiltrated Archive"
                    plain_pass = entry.get("password")
                    hash_pass = entry.get("hashed_password")

                    item = {
                        "breach_id": f"dehashed_{re.sub(r'[^a-zA-Z0-9]', '_', db_name.lower())}_{idx}",
                        "breach_name": f"{db_name} Leak Dump",
                        "leak_type": "DATABASE_LEAK",
                        "breach_date": entry.get("obtained_date", "2023-01-01")[:10],
                        "description": f"Exfiltrated record cataloged in DeHashed threat intelligence repository ({db_name}).",
                        "threat_actor_source": "DeHashed Threat Database",
                        "severity": "CRITICAL" if plain_pass else "HIGH",
                        "domain": entry.get("ip_address") or "dehashed-dump.local",
                        "records_count": 1,
                        "exposed_data": ["Email addresses", "Passwords"] if (plain_pass or hash_pass) else ["Email addresses"]
                    }
                    if plain_pass:
                        item["top_passwords"] = [plain_pass]
                    if hash_pass:
                        item["raw_hash"] = hash_pass
                    results.append(item)
    except Exception:
        pass

    return results


def query_snusbase_api(email: str, timeout: float = 4.0) -> List[Dict[str, Any]]:
    """
    Queries Snusbase API when SNUSBASE_API_KEY is configured in .env.
    """
    api_key = os.getenv("SNUSBASE_API_KEY", "").strip()
    if not api_key:
        return []

    cleaned_email = email.strip().lower()
    results = []
    url = "https://api.snusbase.com/data/search"
    headers = {
        "Auth": api_key,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }
    data = json.dumps({"terms": [cleaned_email], "types": ["email"]}).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
                res_dict = payload.get("results", {})
                for term_key, records in res_dict.items():
                    for idx, rec in enumerate(records or []):
                        db_name = rec.get("_table") or "Snusbase Threat Lake"
                        plain = rec.get("password")
                        hsh = rec.get("hash")
                        item = {
                            "breach_id": f"snusbase_{re.sub(r'[^a-zA-Z0-9]', '_', db_name.lower())}_{idx}",
                            "breach_name": f"{db_name} Compromised Record",
                            "leak_type": "DATABASE_LEAK",
                            "breach_date": "2023-01-01",
                            "description": f"Exfiltrated record verified via Snusbase 10B+ threat repository ({db_name}).",
                            "threat_actor_source": "Snusbase Threat Intelligence",
                            "severity": "CRITICAL" if plain else "HIGH",
                            "domain": "snusbase-lake.local",
                            "records_count": 1,
                            "exposed_data": ["Email addresses", "Passwords"] if (plain or hsh) else ["Email addresses"]
                        }
                        if plain:
                            item["top_passwords"] = [plain]
                        if hsh:
                            item["raw_hash"] = hsh
                        results.append(item)
    except Exception:
        pass

    return results


def harvest_public_pastes_and_combolists(email: str, timeout: float = 3.5) -> List[Dict[str, Any]]:
    """
    Searches public paste services (Pastebin, JustPaste, Rentry, Ghostbin, Gists)
    for exact combolist lines: target_email:password or user:target_email:password.
    Extracts authentic plaintext passwords directly from public leaks on the web.
    """
    from backend.paste_recon import search_paste_leaks
    cleaned_email = email.strip().lower()
    discovered_creds = []

    try:
        paste_intel = search_paste_leaks(cleaned_email, max_results=10)
        pastes = paste_intel.get("pastes", [])

        # Pattern: email:password or email;password or email|password
        target_pattern = re.compile(re.escape(cleaned_email) + r'[:;|,]([^\s\r\n\t,;]{4,})', re.IGNORECASE)

        for p in pastes:
            snippet = p.get("snippet", "")
            match = target_pattern.search(snippet)
            raw_password = None

            if match:
                raw_password = match.group(1).strip()
            else:
                # If snippet didn't contain full line, try downloading raw paste if service allows
                raw_url = p.get("url", "")
                raw_fetch_url = None
                if "pastebin.com/" in raw_url and "/raw/" not in raw_url:
                    pid = raw_url.rstrip("/").split("/")[-1]
                    if pid and pid != "pastebin.com":
                        raw_fetch_url = f"https://pastebin.com/raw/{pid}"
                elif "rentry.co/" in raw_url and "/raw" not in raw_url:
                    pid = raw_url.rstrip("/").split("/")[-1]
                    if pid:
                        raw_fetch_url = f"https://rentry.co/{pid}/raw"

                if raw_fetch_url:
                    try:
                        f_req = urllib.request.Request(raw_fetch_url, headers={"User-Agent": USER_AGENT})
                        with urllib.request.urlopen(f_req, timeout=2.0) as resp:
                            if resp.status == 200:
                                raw_text = resp.read().decode("utf-8", errors="ignore")
                                f_match = target_pattern.search(raw_text)
                                if f_match:
                                    raw_password = f_match.group(1).strip()
                    except Exception:
                        pass

            if raw_password:
                discovered_creds.append({
                    "breach_id": f"paste_{re.sub(r'[^a-zA-Z0-9]', '_', p.get('service', 'paste').lower())}_{len(discovered_creds) + 1}",
                    "breach_name": f"Public Combolist Paste ({p.get('service', 'Web Paste')})",
                    "leak_type": "COMBO_LIST",
                    "breach_date": "2024-01-01",
                    "description": f"Identity and plaintext credential leaked in public online paste ({p.get('title', p.get('url'))}).",
                    "threat_actor_source": f"Public Paste Dump ({p.get('service')})",
                    "severity": "CRITICAL",
                    "domain": p.get("url", "pastebin.com"),
                    "records_count": 1,
                    "exposed_data": ["Email addresses", "Passwords (Plaintext)"],
                    "top_passwords": [raw_password]
                })
    except Exception:
        pass

    return discovered_creds


def query_all_public_leak_databases(email: str) -> List[Dict[str, Any]]:
    """
    Executes concurrent multi-source reconnaissance across all operational public leak databases:
    1. XposedOrNot Live Network
    2. Hudson Rock Cavalier Cybercrime Intelligence
    3. Live Combolist & Pastebin Harvester
    4. LeakCheck Public / Community Engine
    5. BreachDirectory Engine
    6. DeHashed (if key configured)
    7. Snusbase (if key configured)
    8. HaveIBeenPwned Paid v3 (if key configured)
    """
    cleaned_email = email.strip().lower()
    from backend.osint_scanner import query_xposedornot, query_hudson_rock
    from backend.hibp_engine import is_hibp_configured, query_hibp_breaches

    all_breaches: Dict[str, Dict[str, Any]] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        f_xon = executor.submit(query_xposedornot, cleaned_email)
        f_hr = executor.submit(query_hudson_rock, cleaned_email)
        f_pastes = executor.submit(harvest_public_pastes_and_combolists, cleaned_email)
        f_lc = executor.submit(query_leakcheck_public, cleaned_email)
        f_bd = executor.submit(query_breachdirectory_public, cleaned_email)
        f_dh = executor.submit(query_dehashed_api, cleaned_email)
        f_sb = executor.submit(query_snusbase_api, cleaned_email)
        f_hibp = executor.submit(query_hibp_breaches, cleaned_email) if is_hibp_configured() else None

        # Collect XON
        try:
            for b in f_xon.result(timeout=5.0):
                all_breaches[b["breach_id"]] = b
        except Exception:
            pass

        # Collect Hudson Rock
        try:
            for b in f_hr.result(timeout=5.0):
                all_breaches[b["breach_id"]] = b
        except Exception:
            pass

        # Collect Pastes
        try:
            for b in f_pastes.result(timeout=5.0):
                all_breaches[b["breach_id"]] = b
        except Exception:
            pass

        # Collect LeakCheck
        try:
            for b in f_lc.result(timeout=5.0):
                all_breaches[b["breach_id"]] = b
        except Exception:
            pass

        # Collect BreachDirectory
        try:
            for b in f_bd.result(timeout=5.0):
                all_breaches[b["breach_id"]] = b
        except Exception:
            pass

        # Collect DeHashed
        try:
            for b in f_dh.result(timeout=5.0):
                all_breaches[b["breach_id"]] = b
        except Exception:
            pass

        # Collect Snusbase
        try:
            for b in f_sb.result(timeout=5.0):
                all_breaches[b["breach_id"]] = b
        except Exception:
            pass

        # Collect HIBP
        if f_hibp:
            try:
                for b in f_hibp.result(timeout=5.0):
                    all_breaches[b["breach_id"]] = b
            except Exception:
                pass

    return list(all_breaches.values())
