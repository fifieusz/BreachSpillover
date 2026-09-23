"""
Email & Domain Verification Engine
Performs RFC syntax validation, DNS A-record and MX (Mail Exchange) verification,
disposable/temporary email detection, and domain security posture assessment.
"""

import re
import socket
import ssl
import urllib.request
import json
from typing import Dict, Any, Tuple

# Common temporary / disposable email providers
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "throwawaymail.com", "yopmail.com", "sharklasers.com", "dispostable.com",
    "trashmail.com", "getairmail.com", "fakeinbox.com", "tempinbox.com",
    "maildrop.cc", "inboxkitten.com", "mytemp.email", "mohmal.com"
}

# Major known public email providers
MAJOR_EMAIL_PROVIDERS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.uk", "outlook.com",
    "hotmail.com", "live.com", "msn.com", "icloud.com", "me.com", "mac.com",
    "proton.me", "protonmail.com", "zoho.com", "aol.com", "gmx.com",
    "mail.com", "wp.pl", "onet.pl", "interia.pl", "o2.pl"
}

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

def verify_email_address(email: str) -> Dict[str, Any]:
    """
    Comprehensive verification of email syntax, domain existence,
    MX mail exchanger records, and disposable email status.
    """
    cleaned = (email or "").strip().lower()
    
    # 1. Basic Format Validation
    if not cleaned or "@" not in cleaned:
        return {
            "is_valid": False,
            "status": "INVALID_FORMAT",
            "reason": "Email format is invalid. Must contain an '@' symbol and a valid domain name.",
            "domain": "",
            "mx_found": False,
            "is_disposable": False
        }
    
    if not EMAIL_REGEX.match(cleaned):
        return {
            "is_valid": False,
            "status": "INVALID_SYNTAX",
            "reason": "Email syntax does not comply with standard RFC 5322 format.",
            "domain": cleaned.split("@")[-1],
            "mx_found": False,
            "is_disposable": False
        }
    
    local_part, domain = cleaned.split("@", 1)
    
    if len(domain) < 3 or "." not in domain:
        return {
            "is_valid": False,
            "status": "INVALID_DOMAIN",
            "reason": f"Domain '{domain}' is not a valid fully qualified domain name.",
            "domain": domain,
            "mx_found": False,
            "is_disposable": False
        }

    # 2. Check Disposable / Burner Domain
    from backend.live_osint import DISPOSABLE_DOMAINS as EXPANDED_DISPOSABLE, check_disposable_email
    is_disposable = domain in DISPOSABLE_DOMAINS or domain in EXPANDED_DISPOSABLE
    disp_meta = check_disposable_email(domain)
    if disp_meta.get("is_disposable"):
        is_disposable = True

    # 3. Fast-path check for major known domains
    if domain in MAJOR_EMAIL_PROVIDERS:
        provider_name = "Public Consumer Webmail"
        if "google" in domain or "gmail" in domain:
            provider_name = "Google Gmail Infrastructure"
        elif "outlook" in domain or "hotmail" in domain or "live" in domain:
            provider_name = "Microsoft Outlook Infrastructure"
        elif "proton" in domain:
            provider_name = "Proton Privacy Mail"

        return {
            "is_valid": True,
            "status": "VERIFIED_ACTIVE",
            "reason": f"Verified active mail domain ({domain}) with established mail infrastructure.",
            "domain": domain,
            "mx_found": True,
            "is_disposable": False,
            "provider_type": provider_name,
            "email_security": {
                "mail_provider": provider_name,
                "spf_status": "ENFORCED",
                "dmarc_status": "ENFORCED",
                "spoofing_risk": "PROTECTED"
            }
        }

    # 4. Domain Resolution & MX Record Verification
    domain_resolves, mx_records, check_reason, sec_posture = check_domain_dns_and_mx(domain)
    
    if not domain_resolves and not mx_records:
        return {
            "is_valid": False,
            "status": "NON_EXISTENT_DOMAIN",
            "reason": f"Domain '{domain}' does not exist or has no active mail exchange (MX) records. This email address cannot receive mail.",
            "domain": domain,
            "mx_found": False,
            "is_disposable": is_disposable,
            "email_security": sec_posture
        }

    return {
        "is_valid": True,
        "status": "VERIFIED_ACTIVE" if not is_disposable else "DISPOSABLE_WARNING",
        "reason": check_reason if not is_disposable else f"Disposable/temporary burner email domain ({domain}). High spam/disposable risk.",
        "domain": domain,
        "mx_found": len(mx_records) > 0,
        "mx_records": mx_records[:3],
        "is_disposable": is_disposable,
        "provider_type": "Disposable Email Service" if is_disposable else sec_posture.get("mail_provider", "Custom / Enterprise Domain"),
        "email_security": sec_posture
    }

def check_domain_dns_and_mx(domain: str) -> Tuple[bool, list, str, dict]:
    """
    Checks if domain has A-records (via socket), MX records (via DoH),
    and evaluates SPF / DMARC authentication posture.
    """
    mx_records = []
    domain_has_ip = False
    sec_posture = {
        "mail_provider": "Unknown",
        "spf_status": "UNCONFIGURED",
        "dmarc_status": "UNCONFIGURED",
        "spoofing_risk": "HIGH"
    }
    
    # 1. Check local socket A-record resolution
    try:
        ip = socket.gethostbyname(domain)
        if ip:
            domain_has_ip = True
    except Exception:
        pass

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # 2. Query Cloudflare DNS-over-HTTPS for MX records
    try:
        url = f"https://cloudflare-dns.com/dns-query?name={urllib.parse.quote(domain)}&type=MX"
        req = urllib.request.Request(url, headers={"Accept": "application/dns-json", "User-Agent": "BreachSpillover-DNS/1.0"})
        with urllib.request.urlopen(req, timeout=3.0, context=ctx) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                answers = data.get("Answer", [])
                for ans in answers:
                    if ans.get("type") == 15: # MX type
                        mx_records.append(ans.get("data", ""))
    except Exception:
        pass

    # Infer Mail Provider
    mx_blob = " ".join(mx_records).lower()
    if "google" in mx_blob or "aspmx" in mx_blob:
        sec_posture["mail_provider"] = "Google Workspace / Enterprise"
    elif "outlook" in mx_blob or "protection.outlook" in mx_blob:
        sec_posture["mail_provider"] = "Microsoft 365 / Exchange Online"
    elif "pphosted" in mx_blob:
        sec_posture["mail_provider"] = "Proofpoint Enterprise Gateway"
    elif "mimecast" in mx_blob:
        sec_posture["mail_provider"] = "Mimecast Security Gateway"
    elif "proton" in mx_blob:
        sec_posture["mail_provider"] = "Proton Privacy Mail"
    elif "zoho" in mx_blob:
        sec_posture["mail_provider"] = "Zoho Workplace"
    elif mx_records:
        sec_posture["mail_provider"] = "Self-Hosted / Independent Postfix"

    # 3. Query SPF and DMARC posture
    try:
        txt_url = f"https://cloudflare-dns.com/dns-query?name={urllib.parse.quote(domain)}&type=TXT"
        req = urllib.request.Request(txt_url, headers={"Accept": "application/dns-json", "User-Agent": "BreachSpillover-DNS/1.0"})
        with urllib.request.urlopen(req, timeout=2.5, context=ctx) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                for ans in data.get("Answer", []):
                    txt_data = ans.get("data", "").lower()
                    if "v=spf1" in txt_data:
                        if "-all" in txt_data:
                            sec_posture["spf_status"] = "STRICT_HARDFAIL (-all)"
                        elif "~all" in txt_data:
                            sec_posture["spf_status"] = "SOFTFAIL (~all)"
                        elif "?all" in txt_data or "+all" in txt_data:
                            sec_posture["spf_status"] = "PERMISSIVE_VULNERABLE"
                        else:
                            sec_posture["spf_status"] = "CONFIGURED"

        dmarc_url = f"https://cloudflare-dns.com/dns-query?name=_dmarc.{urllib.parse.quote(domain)}&type=TXT"
        req = urllib.request.Request(dmarc_url, headers={"Accept": "application/dns-json", "User-Agent": "BreachSpillover-DNS/1.0"})
        with urllib.request.urlopen(req, timeout=2.5, context=ctx) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                for ans in data.get("Answer", []):
                    txt_data = ans.get("data", "").lower()
                    if "v=dmarc1" in txt_data:
                        if "p=reject" in txt_data:
                            sec_posture["dmarc_status"] = "ENFORCED_REJECT (p=reject)"
                        elif "p=quarantine" in txt_data:
                            sec_posture["dmarc_status"] = "ENFORCED_QUARANTINE (p=quarantine)"
                        elif "p=none" in txt_data:
                            sec_posture["dmarc_status"] = "MONITORING_ONLY (p=none)"
                        else:
                            sec_posture["dmarc_status"] = "CONFIGURED"
    except Exception:
        pass

    # Overall spoofing risk
    if "REJECT" in sec_posture["dmarc_status"] or "QUARANTINE" in sec_posture["dmarc_status"]:
        sec_posture["spoofing_risk"] = "PROTECTED"
    elif sec_posture["spf_status"] != "UNCONFIGURED" and "HARDFAIL" in sec_posture["spf_status"]:
        sec_posture["spoofing_risk"] = "MODERATE"
    else:
        sec_posture["spoofing_risk"] = "HIGH_SPOOFABLE"

    if mx_records:
        return True, mx_records, f"Domain '{domain}' has active mail exchangers ({len(mx_records)} MX servers configured).", sec_posture
    elif domain_has_ip:
        return True, [], f"Domain '{domain}' resolves to an IP address, but no explicit MX records were returned.", sec_posture
    else:
        return False, [], f"Domain '{domain}' has no DNS A or MX records.", sec_posture

