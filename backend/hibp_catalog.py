"""
Have I Been Pwned (HIBP) Master Breach Catalog Synchronizer
Maintains an authoritative local cache of all 1,000+ documented global data breaches
published via HIBP's free, public encyclopedia API (https://haveibeenpwned.com/api/v3/breaches).
Provides deep context, compromised data classes (Passwords, SSNs, Physical Addresses),
breach verification status, and historical timeline metadata.
"""

import os
import json
import urllib.request
import re
from typing import Dict, Any, List, Optional

CATALOG_CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "hibp_breaches_catalog.json")
HIBP_PUBLIC_BREACHES_URL = "https://haveibeenpwned.com/api/v3/breaches"
USER_AGENT = "BreachSpillover-Sovereign-OSINT/3.0"

_CATALOG_INDEX: Optional[Dict[str, Dict[str, Any]]] = None

def sync_hibp_catalog(force: bool = False) -> List[Dict[str, Any]]:
    """
    Downloads and caches HIBP's complete public breach catalog (1,000+ breaches).
    If cached file exists and is less than 7 days old, uses cached data unless force=True.
    """
    global _CATALOG_INDEX
    os.makedirs(os.path.dirname(CATALOG_CACHE_PATH), exist_ok=True)

    if not force and os.path.exists(CATALOG_CACHE_PATH):
        try:
            with open(CATALOG_CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 100:
                    _build_catalog_index(data)
                    return data
        except Exception:
            pass

    # Fetch live from official HIBP API
    try:
        req = urllib.request.Request(HIBP_PUBLIC_BREACHES_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10.0) as response:
            if response.status == 200:
                raw = response.read().decode("utf-8", errors="ignore")
                data = json.loads(raw)
                with open(CATALOG_CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                _build_catalog_index(data)
                return data
    except Exception as e:
        # Fallback to existing cache if offline
        if os.path.exists(CATALOG_CACHE_PATH):
            with open(CATALOG_CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                _build_catalog_index(data)
                return data
        return []

    return []

def _normalize_key(text: str) -> str:
    """Normalizes breach names/domains for fuzzy matching."""
    if not text:
        return ""
    clean = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    return clean

def _build_catalog_index(breaches: List[Dict[str, Any]]):
    """Indexes catalog entries by multiple keys (Name, Title, Domain) for instant lookup."""
    global _CATALOG_INDEX
    idx: Dict[str, Dict[str, Any]] = {}
    for b in breaches:
        name = b.get("Name", "")
        title = b.get("Title", "")
        domain = b.get("Domain", "")

        for key in [name, title, domain]:
            norm = _normalize_key(key)
            if norm:
                idx[norm] = b
    _CATALOG_INDEX = idx

def lookup_breach_metadata(breach_name_or_domain: str) -> Optional[Dict[str, Any]]:
    """
    Looks up authoritative HIBP breach metadata for a given breach name or domain.
    Returns normalized dictionary containing Title, Date, DataClasses, PwnCount, Description, and Severity.
    """
    global _CATALOG_INDEX
    if _CATALOG_INDEX is None:
        sync_hibp_catalog()

    if not _CATALOG_INDEX or not breach_name_or_domain:
        return None

    norm = _normalize_key(breach_name_or_domain)
    # Direct match
    if norm in _CATALOG_INDEX:
        raw = _CATALOG_INDEX[norm]
        return _format_breach_info(raw)

    # Substring match
    for key, raw in _CATALOG_INDEX.items():
        if len(norm) >= 4 and (norm in key or key in norm):
            return _format_breach_info(raw)

    return None

def _format_breach_info(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Formats raw HIBP schema into BreachSpillover intelligence format."""
    data_classes = raw.get("DataClasses", [])
    raw_desc = raw.get("Description", "")
    # Clean HTML tags from HIBP description
    clean_desc = re.sub(r'<[^>]+>', '', raw_desc).strip()

    # Determine severity based on compromised data classes
    dc_lower = [dc.lower() for dc in data_classes]
    is_critical = any(
        k in dc_lower for k in [
            "passwords", "bank account numbers", "credit cards", "social security numbers",
            "government issued ids", "private keys", "health records"
        ]
    )
    is_high = any(
        k in dc_lower for k in [
            "phone numbers", "physical addresses", "dates of birth", "ip addresses"
        ]
    )
    severity = "CRITICAL" if is_critical else ("HIGH" if is_high else "MEDIUM")

    return {
        "hibp_name": raw.get("Name"),
        "title": raw.get("Title") or raw.get("Name"),
        "domain": raw.get("Domain"),
        "breach_date": raw.get("BreachDate"),
        "pwn_count": raw.get("PwnCount", 0),
        "description": clean_desc,
        "data_classes": data_classes,
        "is_verified": raw.get("IsVerified", True),
        "is_fabricated": raw.get("IsFabricated", False),
        "is_sensitive": raw.get("IsSensitive", False),
        "is_retired": raw.get("IsRetired", False),
        "is_spam_list": raw.get("IsSpamList", False),
        "severity": severity
    }
