"""
BreachSpillover - Passive DNS, Certificate Transparency & Infrastructure Recon Engine
Performs non-intrusive DNS-over-HTTPS (DoH) lookups, Certificate Transparency (crt.sh)
subdomain harvesting, Mail Exchanger (MX) intelligence, and SPF/DMARC posture grading.
"""

import json
import socket
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
import concurrent.futures
import time

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Common DoH endpoints
DOH_ENDPOINTS = [
    "https://cloudflare-dns.com/dns-query",
    "https://dns.google/resolve"
]

RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "NS", "SOA", "CAA"]

CRITICAL_PREFIXES = {
    "auth": "Identity & Access Management",
    "sso": "Single Sign-On Portal",
    "vpn": "Virtual Private Network Gateway",
    "mail": "Email Webmail / Exchange",
    "owa": "Outlook Web Access",
    "admin": "Administrative Console",
    "portal": "Corporate Portal",
    "api": "API Gateway / Endpoints",
    "dev": "Development Environment",
    "staging": "Staging / Pre-Production",
    "gitlab": "Source Code Management",
    "github": "Code Hosting",
    "jira": "Issue Tracking / Atlassian",
    "confluence": "Internal Wiki / Knowledge",
    "grafana": "Telemetry / Monitoring Dashboard",
    "kibana": "Log Intelligence Dashboard",
    "vault": "Secrets Management (HashiCorp)",
    "remote": "Remote Access Gateway",
    "citrix": "Citrix Gateway",
    "okta": "Okta SSO Gateway"
}

def query_doh(domain: str, record_type: str = "A", timeout: float = 3.0) -> List[Dict[str, Any]]:
    """Queries DNS records via Cloudflare or Google DoH with automatic fallback."""
    clean_domain = domain.strip().lower()
    
    # Try Cloudflare DoH first
    cf_url = f"https://cloudflare-dns.com/dns-query?name={urllib.parse.quote(clean_domain)}&type={record_type}"
    req = urllib.request.Request(
        cf_url,
        headers={"Accept": "application/dns-json", "User-Agent": USER_AGENT}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            answers = data.get("Answer", [])
            results = []
            for ans in answers:
                results.append({
                    "name": ans.get("name", clean_domain).rstrip("."),
                    "type": record_type,
                    "ttl": ans.get("TTL", 300),
                    "data": ans.get("data", "").strip('"')
                })
            return results
    except Exception:
        pass

    # Fallback to Google DoH
    goog_url = f"https://dns.google/resolve?name={urllib.parse.quote(clean_domain)}&type={record_type}"
    req_goog = urllib.request.Request(
        goog_url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req_goog, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            answers = data.get("Answer", [])
            results = []
            for ans in answers:
                results.append({
                    "name": ans.get("name", clean_domain).rstrip("."),
                    "type": record_type,
                    "ttl": ans.get("TTL", 300),
                    "data": ans.get("data", "").strip('"')
                })
            return results
    except Exception:
        pass

    return []

def query_certificate_transparency(domain: str, timeout: float = 4.0, max_subdomains: int = 50) -> List[Dict[str, Any]]:
    """
    Queries crt.sh Certificate Transparency logs to discover known active and historical subdomains.
    Classifies high-value attack surface targets (SSO, VPN, Admin, Dev).
    """
    clean_domain = domain.strip().lower()
    url = f"https://crt.sh/?q=%25.{urllib.parse.quote(clean_domain)}&output=json"
    
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
        }
    )

    discovered = {}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            for entry in raw_data:
                name_value = entry.get("name_value", "")
                logged_at = entry.get("entry_timestamp", "")[:10]
                issuer = entry.get("issuer_name", "")
                
                # Split multiple names if SAN contains newlines
                names = [n.strip().lower() for n in name_value.split("\n") if n.strip()]
                for name in names:
                    if name.startswith("*."):
                        name = name[2:]
                    if not name.endswith(clean_domain) or name == clean_domain:
                        continue
                    
                    if name not in discovered:
                        sub_prefix = name.replace(f".{clean_domain}", "").split(".")[0]
                        category = CRITICAL_PREFIXES.get(sub_prefix, "General Subdomain")
                        is_critical = sub_prefix in CRITICAL_PREFIXES
                        
                        discovered[name] = {
                            "subdomain": name,
                            "prefix": sub_prefix,
                            "category": category,
                            "critical_asset": is_critical,
                            "first_seen": logged_at,
                            "issuer": issuer.split(",")[0] if issuer else "Unknown CA"
                        }
                        if len(discovered) >= max_subdomains:
                            break
                if len(discovered) >= max_subdomains:
                    break
    except Exception:
        # Fallback heuristic subdomains if crt.sh times out
        common_prefixes = ["mail", "vpn", "sso", "portal", "admin", "dev", "api", "remote", "autodiscover"]
        for p in common_prefixes:
            sub = f"{p}.{clean_domain}"
            discovered[sub] = {
                "subdomain": sub,
                "prefix": p,
                "category": CRITICAL_PREFIXES.get(p, "Infrastructure"),
                "critical_asset": True,
                "first_seen": "Heuristic Enumeration",
                "issuer": "N/A"
            }

    subdomain_list = list(discovered.values())
    subdomain_list.sort(key=lambda s: (not s["critical_asset"], s["subdomain"]))
    return subdomain_list

def analyze_mail_posture(domain: str, mx_records: List[Dict[str, Any]], txt_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyzes MX mail routing providers, SPF policy, and DMARC enforcement."""
    clean_domain = domain.strip().lower()
    
    # Identify MX provider
    mx_hosts = [r["data"].lower() for r in mx_records]
    mx_blob = " ".join(mx_hosts)
    
    provider = "Custom / On-Premises Mail Gateway"
    risk_level = "MODERATE"
    
    if "google" in mx_blob or "aspmx" in mx_blob:
        provider = "Google Workspace (Gmail Enterprise)"
        risk_level = "LOW"
    elif "outlook" in mx_blob or "protection.outlook.com" in mx_blob:
        provider = "Microsoft 365 / Exchange Online"
        risk_level = "LOW"
    elif "pphosted" in mx_blob or "proofpoint" in mx_blob:
        provider = "Proofpoint Enterprise Protection"
        risk_level = "MINIMAL"
    elif "mimecast" in mx_blob:
        provider = "Mimecast Secure Email Gateway"
        risk_level = "MINIMAL"
    elif "proton" in mx_blob:
        provider = "ProtonMail Professional"
        risk_level = "LOW"
    elif "barracuda" in mx_blob:
        provider = "Barracuda Email Security Gateway"
        risk_level = "LOW"
    elif not mx_records:
        provider = "No Mail Exchanger Detected (Non-Mailable)"
        risk_level = "HIGH"

    # Analyze SPF
    spf_record = None
    for txt in txt_records:
        val = txt.get("data", "")
        if val.startswith("v=spf1"):
            spf_record = val
            break
            
    spf_status = "Missing (Spoofing Vulnerable)"
    if spf_record:
        if "-all" in spf_record:
            spf_status = "Hard Fail (-all, Strict Enforcement)"
        elif "~all" in spf_record:
            spf_status = "Soft Fail (~all, Permissive Acceptance)"
        elif "?all" in spf_record or "+all" in spf_record:
            spf_status = "Neutral / Open Relay (?all/+all, Insecure)"

    # Query DMARC
    dmarc_records = query_doh(f"_dmarc.{clean_domain}", "TXT", timeout=2.5)
    dmarc_record = None
    dmarc_policy = "None / Missing"
    dmarc_enforced = False
    
    for r in dmarc_records:
        val = r.get("data", "")
        if val.startswith("v=DMARC1"):
            dmarc_record = val
            if "p=reject" in val:
                dmarc_policy = "Reject (Maximum Anti-Spoofing Protection)"
                dmarc_enforced = True
            elif "p=quarantine" in val:
                dmarc_policy = "Quarantine (Spam Folder Isolation)"
                dmarc_enforced = True
            elif "p=none" in val:
                dmarc_policy = "None (Monitoring Only, No Rejection)"
                dmarc_enforced = False
            break

    return {
        "provider": provider,
        "mx_count": len(mx_records),
        "mx_servers": [r["data"] for r in mx_records],
        "spf_present": spf_record is not None,
        "spf_record": spf_record,
        "spf_status": spf_status,
        "dmarc_present": dmarc_record is not None,
        "dmarc_record": dmarc_record,
        "dmarc_policy": dmarc_policy,
        "dmarc_enforced": dmarc_enforced,
        "phishing_susceptibility": "LOW" if dmarc_enforced else ("MEDIUM" if spf_record else "HIGH")
    }

def gather_domain_infrastructure(domain: str) -> Dict[str, Any]:
    """
    Aggregates full passive DNS infrastructure, Certificate Transparency subdomains,
    and mail security posture in parallel threads.
    """
    clean_domain = domain.strip().lower().lstrip("http://").lstrip("https://").split("/")[0]
    if not clean_domain:
        return {"error": "Invalid domain"}

    t0 = time.time()
    results: Dict[str, Any] = {
        "domain": clean_domain,
        "dns_records": {},
        "subdomains": [],
        "subdomains_count": 0,
        "critical_subdomains_count": 0,
        "mail_posture": {},
        "query_time_sec": 0.0
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_dns = {
            executor.submit(query_doh, clean_domain, rtype): rtype
            for rtype in ["A", "AAAA", "MX", "TXT", "NS", "SOA"]
        }
        future_ct = executor.submit(query_certificate_transparency, clean_domain)

        # Collect DNS answers
        for future in concurrent.futures.as_completed(future_dns):
            rtype = future_dns[future]
            try:
                results["dns_records"][rtype] = future.result()
            except Exception:
                results["dns_records"][rtype] = []

        # Collect Subdomains
        try:
            subdomains = future_ct.result()
            results["subdomains"] = subdomains
            results["subdomains_count"] = len(subdomains)
            results["critical_subdomains_count"] = sum(1 for s in subdomains if s.get("critical_asset"))
        except Exception:
            results["subdomains"] = []

    # Mail Security Posture Analysis
    mx_recs = results["dns_records"].get("MX", [])
    txt_recs = results["dns_records"].get("TXT", [])
    results["mail_posture"] = analyze_mail_posture(clean_domain, mx_recs, txt_recs)
    results["query_time_sec"] = round(time.time() - t0, 3)

    return results
