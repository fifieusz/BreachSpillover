"""
Historical Web & Archive Reconnaissance Engine
Leverages Wayback Machine (Internet Archive), AlienVault OTX, and URLScan.io
to uncover historical configuration files, sensitive exposures (.env, database dumps, git roots),
API definitions (Swagger/OpenAPI), and unlisted subdomains.
"""

import re
import json
import urllib.request
import urllib.parse
import urllib.error
import concurrent.futures
from typing import List, Dict, Any, Optional, Set

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Categorization rules for historical sensitive endpoints
SENSITIVE_PATTERNS = [
    (r'(\.env|\.env\.local|\.env\.production|\.env\.bak)$', "EXPOSED_CREDENTIALS", "CRITICAL", "Archived environment configuration potentially containing API keys and database secrets."),
    (r'(credentials|secrets|passwords?|id_rsa|id_dsa|\.pem|\.key|\.htpasswd)$', "EXPOSED_CREDENTIALS", "CRITICAL", "Archived cryptographic key or plaintext credential store."),
    (r'(\.sql|\.sql\.gz|\.dump|\.dump\.gz|backup\.tar\.gz|db\.sqlite3)$', "DATABASE_DUMP", "HIGH", "Archived database backup or SQL dump file."),
    (r'(wp-config\.php|config\.json|settings\.py|database\.yml|web\.config|configuration\.php)', "CONFIG_LEAK", "HIGH", "Archived application infrastructure configuration file."),
    (r'(\.git/|\.git/config|\.svn/|\.hg/)', "GIT_SOURCE_EXPOSURE", "HIGH", "Exposed version control metadata repository."),
    (r'(swagger\.json|openapi\.json|api-docs|/api/v[0-9]+/|/graphql)', "API_DOCS_SWAGGER", "MEDIUM", "Exposed API schema, endpoint catalogue, or documentation gateway."),
    (r'(/admin/|/phpmyadmin/|/cpanel/|/dashboard/|/internal/)', "ADMIN_PANEL", "HIGH", "Archived internal administration gateway or maintenance interface.")
]

def classify_historical_url(url: str) -> Optional[Dict[str, str]]:
    """Inspects a historical URL for known sensitive file or directory exposures."""
    clean_url = url.split("?")[0].lower()
    for pattern, category, risk, desc in SENSITIVE_PATTERNS:
        if re.search(pattern, clean_url):
            return {
                "category": category,
                "risk_level": risk,
                "description": desc
            }
    return None


def query_alienvault_otx_urls(domain: str, limit: int = 40, timeout: float = 3.5) -> List[Dict[str, Any]]:
    """Queries AlienVault Open Threat Exchange (OTX) URL list indicator API for a domain."""
    clean_dom = domain.strip().lower().lstrip("@")
    url = f"https://otx.alienvault.com/api/v1/indicators/domain/{urllib.parse.quote(clean_dom)}/url_list?limit={limit}&page=1"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers)

    results = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                for item in data.get("url_list", []):
                    raw_u = item.get("url")
                    if raw_u:
                        results.append({
                            "url": raw_u,
                            "timestamp": item.get("date"),
                            "http_code": item.get("httpcode"),
                            "source": "AlienVault OTX Threat Intel"
                        })
    except Exception:
        pass
    return results


def query_urlscan_urls(domain: str, size: int = 30, timeout: float = 3.5) -> List[Dict[str, Any]]:
    """Queries URLScan.io public historical crawl index for a domain."""
    clean_dom = domain.strip().lower().lstrip("@")
    query_str = f"domain:{clean_dom}"
    url = f"https://urlscan.io/api/v1/search/?q={urllib.parse.quote(query_str)}&size={size}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers)

    results = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                for r in data.get("results", []):
                    page = r.get("page", {})
                    raw_u = page.get("url")
                    if raw_u:
                        results.append({
                            "url": raw_u,
                            "timestamp": r.get("task", {}).get("time"),
                            "http_code": page.get("status"),
                            "ip": page.get("ip"),
                            "title": page.get("title"),
                            "source": "URLScan.io Historical Crawl"
                        })
    except Exception:
        pass
    return results


def query_wayback_cdx_urls(domain: str, limit: int = 30, timeout: float = 2.5) -> List[Dict[str, Any]]:
    """Queries Wayback Machine CDX API with strict timeout."""
    clean_dom = domain.strip().lower().lstrip("@")
    url = f"https://web.archive.org/cdx/search/cdx?url=*.{urllib.parse.quote(clean_dom)}/*&output=json&collapse=urlkey&filter=statuscode:200&limit={limit}"
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)

    results = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                rows = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if len(rows) > 1:
                    header = rows[0]
                    orig_idx = header.index("original") if "original" in header else 2
                    ts_idx = header.index("timestamp") if "timestamp" in header else 1
                    status_idx = header.index("statuscode") if "statuscode" in header else 4

                    for row in rows[1:]:
                        raw_u = row[orig_idx]
                        ts = row[ts_idx]
                        sc = row[status_idx]
                        results.append({
                            "url": raw_u,
                            "timestamp": ts,
                            "http_code": sc,
                            "source": "Internet Archive Wayback Machine"
                        })
    except Exception:
        pass
    return results


def query_historical_archives(domain: str) -> Dict[str, Any]:
    """
    Executes parallel multi-source historical reconnaissance across Wayback CDX, AlienVault OTX, and URLScan.io.
    Deduplicates URLs, classifies sensitive exposed endpoints, and extracts discovered subdomains.
    """
    clean_dom = domain.strip().lower().lstrip("@")
    if not clean_dom or "." not in clean_dom:
        return {
            "domain": domain,
            "total_urls_indexed": 0,
            "sensitive_exposures_count": 0,
            "discovered_subdomains": [],
            "items": []
        }

    raw_items: List[Dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_otx = executor.submit(query_alienvault_otx_urls, clean_dom, limit=40)
        f_urlscan = executor.submit(query_urlscan_urls, clean_dom, size=30)
        f_cdx = executor.submit(query_wayback_cdx_urls, clean_dom, limit=25)

        for f in concurrent.futures.as_completed([f_otx, f_urlscan, f_cdx]):
            try:
                res = f.result()
                if res:
                    raw_items.extend(res)
            except Exception:
                pass

    # Deduplicate by URL
    seen_urls: Set[str] = set()
    discovered_subdomains: Set[str] = set()
    classified_items: List[Dict[str, Any]] = []
    sensitive_count = 0

    for item in raw_items:
        u = item.get("url", "").strip()
        if not u or u in seen_urls:
            continue
        seen_urls.add(u)

        # Extract host/subdomain
        try:
            parsed = urllib.parse.urlparse(u)
            host = parsed.netloc.split(":")[0].lower()
            if host.endswith(f".{clean_dom}") and host != clean_dom:
                discovered_subdomains.add(host)
        except Exception:
            pass

        # Classify sensitivity
        classification = classify_historical_url(u)
        ts_val = item.get("timestamp") or ""
        # Build Wayback archive playback URL
        ts_digits = re.sub(r'\D', '', str(ts_val))
        playback_ts = ts_digits[:14] if len(ts_digits) >= 8 else "*"
        wayback_link = f"https://web.archive.org/web/{playback_ts}/{u}"

        is_sensitive = classification is not None
        if is_sensitive:
            sensitive_count += 1

        entry = {
            "url": u,
            "wayback_url": wayback_link,
            "source": item.get("source", "Historical Web Index"),
            "timestamp": item.get("timestamp"),
            "http_code": item.get("http_code"),
            "is_sensitive": is_sensitive,
            "category": classification["category"] if is_sensitive else "STANDARD_ARCHIVE",
            "risk_level": classification["risk_level"] if is_sensitive else "INFO",
            "description": classification["description"] if is_sensitive else "Historical crawled URL endpoint."
        }
        classified_items.append(entry)

    # Sort: high-risk sensitive exposures first
    risk_weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
    classified_items.sort(key=lambda x: (-risk_weights.get(x["risk_level"], 0), x["url"]))

    return {
        "domain": clean_dom,
        "total_urls_indexed": len(seen_urls),
        "sensitive_exposures_count": sensitive_count,
        "discovered_subdomains": sorted(list(discovered_subdomains)),
        "items": classified_items[:50]
    }
