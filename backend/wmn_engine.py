"""
BreachSpillover - WhatsMyName (WMN) Account Enumeration Engine
High-throughput concurrent handle enumeration across 700+ public platforms.
Reads local catalog in backend/data/wmn-data.json and performs accurate status-code
and content-string heuristic validation.
"""

import os
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional
import concurrent.futures

BASE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = BASE_DIR / "data" / "wmn-data.json"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# In-memory cache for loaded sites
_WMN_SITES: List[Dict[str, Any]] = []

# High-value priority sites for quick triage
PRIORITY_SITES = [
    "GitHub", "GitLab", "Docker Hub", "Keybase", "Reddit", "Medium", "Dev.to",
    "Chess.com", "Steam", "Telegram", "HackerNews", "Twitch", "Duolingo",
    "Pastebin", "Spotify", "SoundCloud", "Pinterest", "Vimeo", "Disqus",
    "Gravatar", "Substack", "Roblox", "Bluesky", "Mastodon", "About.me"
]

def load_wmn_catalog() -> List[Dict[str, Any]]:
    """Loads and sanitizes WMN site definitions from local JSON catalog."""
    global _WMN_SITES
    if _WMN_SITES:
        return _WMN_SITES

    if not CATALOG_PATH.exists():
        return []

    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_sites = data.get("sites", [])
        # Filter out NSFW by default
        clean_sites = [s for s in raw_sites if s.get("cat") != "xx NSFW xx" and "{account}" in s.get("uri_check", "")]
        _WMN_SITES = clean_sites
        return _WMN_SITES
    except Exception as e:
        print(f"[!] Error loading WMN catalog: {e}")
        return []

def check_single_site(site: Dict[str, Any], handle: str, timeout: float = 2.5) -> Optional[Dict[str, Any]]:
    """
    Probes a single site endpoint for handle existence using WMN signature rules.
    Returns result dict if confirmed, otherwise None.
    """
    clean_handle = handle.strip()
    check_url = site["uri_check"].replace("{account}", urllib.parse.quote(clean_handle))
    pretty_url = site.get("uri_pretty", check_url).replace("{account}", urllib.parse.quote(clean_handle))
    
    req = urllib.request.Request(
        check_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            body = resp.read(65536).decode("utf-8", errors="ignore")
            elapsed = round(time.time() - t0, 3)

            m_str = site.get("m_string")
            e_str = site.get("e_string")
            m_c = site.get("m_code")
            e_c = site.get("e_code")

            # 1. Negative string check (indicates not found)
            if m_str and m_str in body:
                return None
            # 2. Positive string check (must be present if specified)
            if e_str and e_str not in body:
                return None
            # 3. Negative status code match
            if m_c and code == m_c and not m_str:
                return None
            # 4. Positive status code match
            if (e_c and code == e_c) or (not e_c and code == 200):
                return {
                    "platform": site.get("name", "Unknown"),
                    "category": site.get("cat", "social"),
                    "url": pretty_url,
                    "handle": clean_handle,
                    "status_code": code,
                    "response_time_sec": elapsed,
                    "confidence_score": 0.95 if (e_str and e_str in body) else 0.85
                }
            return None

    except urllib.error.HTTPError as e:
        # Check if HTTPError code matches m_code
        if site.get("m_code") and e.code == site.get("m_code"):
            return None
        return None
    except Exception:
        return None

def enumerate_handle_wmn(
    handle: str,
    category: Optional[str] = None,
    max_sites: int = 50,
    priority_only: bool = False
) -> Dict[str, Any]:
    """
    Executes concurrent multi-platform handle verification across WMN database.
    """
    clean_handle = handle.strip().lstrip("@")
    if not clean_handle:
        return {"handle": "", "total_scanned": 0, "matches_count": 0, "matches": []}

    all_sites = load_wmn_catalog()
    if not all_sites:
        return {"handle": clean_handle, "total_scanned": 0, "matches_count": 0, "matches": []}

    # Filter sites
    filtered = []
    if priority_only:
        filtered = [s for s in all_sites if s.get("name") in PRIORITY_SITES]
    elif category:
        cat_lower = category.lower()
        filtered = [s for s in all_sites if cat_lower in s.get("cat", "").lower()]
    else:
        # Prioritize prominent sites first, followed by general tech and social
        prio = [s for s in all_sites if s.get("name") in PRIORITY_SITES]
        others = [s for s in all_sites if s.get("name") not in PRIORITY_SITES and s.get("cat") in ["social", "tech", "coding", "gaming", "music", "blog"]]
        filtered = prio + others

    selected_sites = filtered[:max_sites]
    matches: List[Dict[str, Any]] = []

    # Execute concurrent probes
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_map = {
            executor.submit(check_single_site, site, clean_handle): site
            for site in selected_sites
        }
        for future in concurrent.futures.as_completed(future_map):
            try:
                res = future.result()
                if res:
                    matches.append(res)
            except Exception:
                pass

    matches.sort(key=lambda m: (m["platform"] not in PRIORITY_SITES, m["platform"]))

    return {
        "handle": clean_handle,
        "total_scanned": len(selected_sites),
        "matches_count": len(matches),
        "matches": matches,
        "categories_checked": list(set(s.get("cat", "other") for s in selected_sites))
    }
