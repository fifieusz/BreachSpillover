"""
BreachSpillover - Live Threat Dump & Paste Aggregator Engine
Automates passive searches for exposed credentials, combo-lists, database dumps,
and darkweb-mirrored paste dumps (Pastebin, JustPaste.it, Rentry, Ghostbin, GitHub Gist)
related to target identities (emails, domains, handles, hashes).
"""

import json
import re
import time
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional
import concurrent.futures

from backend.database import get_connection

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

PASTE_SERVICES = [
    {"name": "Pastebin", "domain": "pastebin.com", "icon": "file-code"},
    {"name": "JustPaste.it", "domain": "justpaste.it", "icon": "file-text"},
    {"name": "Rentry.co", "domain": "rentry.co", "icon": "lock"},
    {"name": "Ghostbin", "domain": "ghostbin.com", "icon": "ghost"},
    {"name": "ControlC", "domain": "controlc.com", "icon": "clipboard"},
    {"name": "GitHub Gist", "domain": "gist.github.com", "icon": "github"}
]

# Sensitive regex patterns to assess threat severity in paste snippets
SEV_CRITICAL_PATTERNS = [
    re.compile(r'(?i)(?:password|passwd|pwd)[\s:=]+[^\s]{6,}'),
    re.compile(r'(?i)api[_-]?key[\s:=]+[a-zA-Z0-9_\-]{16,}'),
    re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}'),
    re.compile(r'\b[a-f0-9]{32}:[a-f0-9]{16,}\b'), # Hash:salt
    re.compile(r'\b[a-f0-9]{64}\b') # SHA-256
]

SEV_HIGH_PATTERNS = [
    re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}:[^\s]{4,}'), # Combo list format user:pass
    re.compile(r'(?i)database\s+dump|table\s+`users`|insert\s+into'),
    re.compile(r'(?i)stealer\s+log|redline|vidar|raccoon|lumma')
]

_PASTE_CACHE: Dict[str, Dict[str, Any]] = {}

def assess_paste_severity(content: str) -> str:
    """Evaluates the risk severity of the discovered text snippet."""
    for pat in SEV_CRITICAL_PATTERNS:
        if pat.search(content):
            return "CRITICAL"
    for pat in SEV_HIGH_PATTERNS:
        if pat.search(content):
            return "HIGH"
    return "MEDIUM"

def search_duckduckgo_dork(query: str, timeout: float = 4.0) -> List[Dict[str, str]]:
    """Executes a non-intrusive query against DDG HTML endpoint to locate indexable leaks."""
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
    )
    
    results = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Extract links and snippet blocks
            blocks = re.findall(r'<div class="result__body">.*?</div>\s*</div>', html, re.DOTALL)
            if not blocks:
                raw_links = re.findall(r'href="([^"]*uddg=[^"]*)"', html)
                for lk in raw_links:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(lk).query)
                    if "uddg" in qs:
                        real_url = qs["uddg"][0]
                        results.append({"title": real_url, "url": real_url, "snippet": ""})
                return results

            for b in blocks:
                url_m = re.search(r'href="([^"]*uddg=[^"]*)"', b)
                title_m = re.search(r'<a class="result__url"[^>]*>(.*?)</a>', b, re.DOTALL)
                snip_m = re.search(r'<a class="result__snippet"[^>]*>(.*?)</a>', b, re.DOTALL)
                
                real_url = ""
                if url_m:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(url_m.group(1)).query)
                    if "uddg" in qs:
                        real_url = qs["uddg"][0]

                if real_url:
                    title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else real_url
                    snippet = re.sub(r'<[^>]+>', '', snip_m.group(1)).strip() if snip_m else ""
                    results.append({"title": title, "url": real_url, "snippet": snippet})
    except Exception:
        pass

    return results

def query_local_threat_db(term: str) -> List[Dict[str, Any]]:
    """Finds raw dump rows in local database matching the term."""
    local_findings = []
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        like_term = f"%{term}%"
        cur.execute("""
            SELECT c.username_or_email, c.plaintext_password, c.password_hash,
                   l.leak_name, l.leak_type, l.breach_date, l.severity,
                   e.full_name, e.corporate_email
            FROM credentials c
            JOIN leaks l ON c.leak_id = l.id
            LEFT JOIN employees e ON c.employee_id = e.id
            WHERE c.username_or_email LIKE ? OR e.corporate_email LIKE ?
            LIMIT 10
        """, (like_term, like_term))
        
        rows = cur.fetchall()
        for r in rows:
            mask_pass = r["plaintext_password"]
            if mask_pass and len(mask_pass) > 2:
                mask_pass = mask_pass[:2] + "*" * (len(mask_pass) - 2)
            local_findings.append({
                "service": "Internal Threat Lake",
                "title": f"Breach Archive: {r['leak_name']} ({r['breach_date']})",
                "url": f"local://breach/{urllib.parse.quote(r['leak_name'])}",
                "snippet": f"Identity: {r['username_or_email']} | Type: {r['leak_type']} | Pwd Sample: {mask_pass or 'HASH'}",
                "severity": r['severity'] or "HIGH",
                "source_type": "Curated Database Dump",
                "timestamp": r['breach_date']
            })
    except Exception as e:
        print(f"[!] Local threat DB search error: {e}")
    finally:
        if conn:
            conn.close()

    return local_findings

    return local_findings

def search_paste_leaks(target: str, max_results: int = 20) -> Dict[str, Any]:
    """
    Executes live multi-service paste reconnaissance and correlates with internal dump stores.
    """
    clean_target = target.strip().lower()
    if not clean_target:
        return {"target": "", "total_found": 0, "pastes": [], "threat_score": 0}

    cache_key = f"paste_{clean_target}"
    if cache_key in _PASTE_CACHE:
        return _PASTE_CACHE[cache_key]

    t0 = time.time()
    findings: List[Dict[str, Any]] = []

    # 1. Local database query
    local_dumps = query_local_threat_db(clean_target)
    findings.extend(local_dumps)

    # 2. Targeted Paste Dorks
    # e.g., site:pastebin.com "target", site:rentry.co "target", site:justpaste.it "target"
    dorks = [
        f'site:pastebin.com "{clean_target}"',
        f'site:justpaste.it "{clean_target}"',
        f'site:rentry.co "{clean_target}"',
        f'site:gist.github.com "{clean_target}" combolist OR password OR leak'
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(search_duckduckgo_dork, dork): dork
            for dork in dorks
        }
        for future in concurrent.futures.as_completed(future_map):
            try:
                res_list = future.result()
                for r in res_list:
                    raw_url = r["url"]
                    # Determine service name
                    srv_name = "Public Paste"
                    for ps in PASTE_SERVICES:
                        if ps["domain"] in raw_url:
                            srv_name = ps["name"]
                            break
                    
                    snippet = r.get("snippet", "")
                    sev = assess_paste_severity(snippet)
                    
                    # Highlight target in snippet
                    clean_snippet = snippet if snippet else f"Exposed reference to {clean_target} indexed by search engines."
                    
                    findings.append({
                        "service": srv_name,
                        "title": r.get("title", raw_url),
                        "url": raw_url,
                        "snippet": clean_snippet,
                        "severity": sev,
                        "source_type": "Live Web Paste",
                        "timestamp": "Recent Index"
                    })
            except Exception:
                pass

    # Deduplicate by URL
    seen_urls = set()
    unique_findings = []
    for f in findings:
        u = f.get("url", "")
        if u not in seen_urls:
            seen_urls.add(u)
            unique_findings.append(f)

    # Calculate threat severity score (0 to 100)
    critical_count = sum(1 for f in unique_findings if f["severity"] == "CRITICAL")
    high_count = sum(1 for f in unique_findings if f["severity"] == "HIGH")
    med_count = sum(1 for f in unique_findings if f["severity"] == "MEDIUM")
    
    threat_score = min(100, (critical_count * 35) + (high_count * 20) + (med_count * 10))

    result = {
        "target": clean_target,
        "total_found": len(unique_findings),
        "threat_score": threat_score,
        "threat_level": "CRITICAL" if threat_score >= 70 else ("HIGH" if threat_score >= 40 else ("ELEVATED" if threat_score > 0 else "LOW")),
        "pastes": unique_findings[:max_results],
        "query_time_sec": round(time.time() - t0, 3)
    }

    _PASTE_CACHE[cache_key] = result
    return result
