import os
import re
import urllib.parse
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import (
    init_db,
    get_connection,
    get_all_employees,
    get_employee_by_email,
    get_employee_by_id,
    get_employee_credentials,
    get_employee_leaks,
    get_employee_pivots,
    get_employee_footprints,
    get_employee_relatives,
    get_global_stats,
    get_or_create_identity_profile,
    reset_identity_profile,
    get_employees_by_domain,
    get_cross_target_correlations,
)
from backend.live_osint import (
    query_domain_infrastructure,
    query_crtsh_subdomains,
    generate_corporate_email_permutations,
    check_disposable_email,
    get_breach_circulation_intel,
    generate_osint_dorks,
)
from backend.masking import (
    mask_email,
    mask_name,
    mask_password,
    mask_phone,
    mask_address,
    mask_city,
    mask_pivot_value
)
from backend.scoring import calculate_spillover_score
from backend.graph_builder import build_identity_graph
from backend.models import SearchResponse, GlobalStats

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

app = FastAPI(
    title="BreachSpillover API",
    description="Universal Digital Risk Protection & Deterministic Identity Pivoting Engine",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure database is initialized
init_db()

class ScenarioRequest(BaseModel):
    email: str
    scenario: str = "full"  # clean, partial, full

class ResetRequest(BaseModel):
    email: str

class BatchScanRequest(BaseModel):
    emails: List[str]
    audit_mode: bool = True

@app.get("/api/stats")
def get_stats():
    """Returns global threat intelligence metrics."""
    return get_global_stats()

@app.get("/api/employees")
def list_employees(audit_mode: bool = Query(True, description="Enable clear uncensored data")):
    """Returns a directory of sample monitored identities."""
    employees = get_all_employees()
    result = []
    for emp in employees:
        result.append({
            "id": emp["id"],
            "full_name": mask_name(emp["full_name"], audit_mode),
            "corporate_email": mask_email(emp["corporate_email"], audit_mode),
            "raw_email": emp["corporate_email"],
            "job_title": emp["job_title"],
            "department": emp["department"],
            "vip_level": emp["vip_level"],
            "creds_count": emp["creds_count"],
            "direct_leaks_count": emp["direct_leaks_count"],
            "address_count": emp["address_count"],
            "relatives_count": emp["relatives_count"],
            "has_high_risk": emp["creds_count"] > 0 and emp["address_count"] > 0
        })
    return result

@app.get("/api/identities")
def list_identities(audit_mode: bool = Query(True, description="Enable clear uncensored data")):
    return list_employees(audit_mode)

@app.post("/api/simulate")
def simulate_scenario(req: ScenarioRequest):
    """Explicitly seeds and evaluates a specified demo exposure scenario for an email."""
    return search_exposure(email=req.email, audit_mode=True, scenario=req.scenario)

@app.post("/api/reset")
def reset_exposure(req: ResetRequest):
    """Clears all breach records for an email and returns a clean profile."""
    reset_identity_profile(req.email)
    return search_exposure(email=req.email, audit_mode=True, scenario="clean")

DECLASS_MASTER_KEY = os.getenv("DECLASS_MASTER_KEY", "SpilloverSec#2025")

class PasscodeVerificationRequest(BaseModel):
    passcode: str

@app.post("/api/auth/verify-passcode")
def verify_declass_passcode(req: PasscodeVerificationRequest):
    """
    Validates the enterprise master declassification security passcode.
    """
    if req.passcode.strip() == DECLASS_MASTER_KEY:
        return {"success": True, "authorized": True, "message": "Security declassification authorization approved"}
    raise HTTPException(status_code=401, detail="Access Denied: Invalid Security Authorization Passcode")

@app.get("/api/search")
@app.get("/api/scan")
def search_exposure(
    email: Optional[str] = Query(None, description="Target email address to investigate (personal or corporate)"),
    query: Optional[str] = Query(None, description="Universal target query (email, username, handle, phone, hash)"),
    audit_mode: bool = True,
    scenario: Optional[str] = None,
    custom_password: Optional[str] = None,
    custom_city: Optional[str] = None,
    custom_street: Optional[str] = None,
    custom_relative: Optional[str] = None,
    known_name: Optional[str] = None,
    known_username: Optional[str] = None,
    known_phone: Optional[str] = None,
    known_city: Optional[str] = None,
    refresh: bool = False
):
    """
    Performs live OSINT pivoting and calculates the Spillover Score for an email or username handle.
    Integrates genuine breach indices, public platform footprints, and user-provided anchors.
    """
    raw_target = (email or query or "").strip()
    if not raw_target:
        raise HTTPException(status_code=400, detail="Target email or username query is required.")

    # Composite query decomposition: extract email and name if user entered combined query
    # e.g. "Amir Secic 3gbxdd@gmail.com", "3gbxdd@gmail.com (Amir Secic)", "Amir Secic <3gbxdd@gmail.com>"
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_target)
    if email_match:
        extracted_email = email_match.group(0).lower()
        remainder = raw_target.replace(email_match.group(0), '').strip(" ()<>,;:[]\"'")
        if remainder and not known_name:
            if re.search(r'[a-zA-Z]{2,}', remainder) and not remainder.startswith("+"):
                known_name = remainder.strip()
        raw_target = extracted_email

    # Universal search routing: detect if input is a handle/username or full person name (no @)
    is_domain = ("@" not in raw_target and "." in raw_target and any(raw_target.lower().endswith(tld) for tld in [".com", ".net", ".org", ".io", ".co", ".ai", ".gov", ".edu", ".pl", ".de", ".uk", ".dev", ".app"]))
    if "@" not in raw_target and not raw_target.startswith("+"):
        # Check if an existing profile matches this handle or email prefix
        conn_check = get_connection()
        cur_check = conn_check.cursor()
        cur_check.execute("""
            SELECT corporate_email FROM employees 
            WHERE LOWER(corporate_email) LIKE ? OR LOWER(full_name) = ?
            LIMIT 1
        """, (f"{raw_target.lower()}@%", raw_target.lower()))
        match_row = cur_check.fetchone()
        conn_check.close()
        if match_row:
            if not known_username:
                known_username = raw_target
            cleaned_email = match_row["corporate_email"].lower()
        elif not is_domain:
            if " " in raw_target and not known_name:
                known_name = raw_target
                cleaned_email = f"{raw_target.lower().replace(' ', '.')}@osint.local"
            else:
                if not known_username:
                    known_username = raw_target
                cleaned_email = f"{raw_target.lower()}@osint.local"
        else:
            cleaned_email = raw_target.lower()
    else:
        cleaned_email = raw_target.lower()
    
    # 0. Email & Domain Security Verification (RFC format, DNS, MX, Disposable detection)
    from backend.email_verifier import verify_email_address
    from backend.threat_intel import generate_threat_provenance_matrix
    verification = verify_email_address(cleaned_email)
    
    anchors = {
        "known_name": known_name,
        "known_username": known_username,
        "known_phone": known_phone,
        "known_city": known_city
    }

    # Retrieve profile without inventing fake leaks unless explicitly simulated
    employee = get_or_create_identity_profile(
        cleaned_email,
        scenario=scenario,
        custom_password=custom_password,
        custom_city=custom_city,
        custom_street=custom_street,
        custom_relative=custom_relative,
        anchors=anchors,
        refresh=refresh
    )

    emp_id = employee["id"]

    # Retrieve all correlated entities
    leaks = get_employee_leaks(emp_id)
    credentials = get_employee_credentials(emp_id)
    pivots = get_employee_pivots(emp_id)
    footprints = get_employee_footprints(emp_id)
    relatives = get_employee_relatives(emp_id)

    # Cross-target correlations (shared credentials, shared residences, shared phone lines)
    from backend.database import get_cross_target_correlations
    cross_correlations = get_cross_target_correlations(emp_id)

    # 1. Calculate Spillover Risk Score
    is_corp = not any(
        cleaned_email.endswith(d) for d in [
            "@gmail.com", "@yahoo.com", "@outlook.com", "@hotmail.com", "@proton.me", "@protonmail.com", "@icloud.com", "@osint.local"
        ]
    )
    spillover = calculate_spillover_score(
        leaks=leaks,
        credentials=credentials,
        pivots=pivots,
        footprints=footprints,
        relatives=relatives,
        is_corporate=is_corp
    )

    # 2. Build Interactive Vis.js Graph
    graph = build_identity_graph(
        employee=employee,
        leaks=leaks,
        credentials=credentials,
        pivots=pivots,
        footprints=footprints,
        relatives=relatives,
        audit_mode=audit_mode,
        cross_correlations=cross_correlations
    )

    # 3. Format Data Objects
    masked_emp = {
        "id": employee["id"],
        "full_name": mask_name(employee["full_name"], audit_mode),
        "corporate_email": mask_email(employee["corporate_email"], audit_mode),
        "job_title": employee["job_title"],
        "department": employee["department"],
        "vip_level": employee["vip_level"],
        "created_at": employee["created_at"]
    }

    from backend.hash_resolver import identify_hash_type

    masked_creds = []
    for cred in credentials:
        raw_hash = cred.get("password_hash")
        masked_hash = None
        hash_info = None
        if raw_hash:
            masked_hash = raw_hash if audit_mode else (raw_hash[:7] + "*" * max(0, len(raw_hash) - 7))
            hash_info = identify_hash_type(raw_hash)

        masked_creds.append({
            "id": cred["id"],
            "leak_id": cred["leak_id"],
            "leak_name": cred["leak_name"],
            "leak_type": cred["leak_type"],
            "username_or_email": mask_email(cred["username_or_email"], audit_mode),
            "plaintext_password": mask_password(cred["plaintext_password"], audit_mode),
            "password_hash": masked_hash,
            "hash_intel": hash_info,
            "password_pattern": cred["password_pattern"],
            "is_corporate_password_match": bool(cred["is_corporate_password_match"]),
            "domain_compromised": cred["domain_compromised"],
            "breach_date": cred["breach_date"],
            "severity": cred["severity"]
        })


    masked_pivots = []
    for piv in pivots:
        masked_pivots.append({
            "id": piv["id"],
            "pivot_type": piv["pivot_type"],
            "pivot_value": mask_pivot_value(piv["pivot_type"], piv["pivot_value"], audit_mode),
            "confidence_score": piv["confidence_score"],
            "context_note": piv["context_note"],
            "leak_name": piv.get("leak_name", "Correlation Engine")
        })

    masked_footprints = []
    for foot in footprints:
        masked_footprints.append({
            "id": foot["id"],
            "address_line": mask_address(foot["address_line"], audit_mode),
            "city": mask_city(foot["city"], audit_mode),
            "postal_code": foot["postal_code"] if audit_mode else foot["postal_code"][:2] + "-***",
            "country": foot["country"],
            "latitude": foot["latitude"] if audit_mode else None,
            "longitude": foot["longitude"] if audit_mode else None,
            "exposure_type": foot["exposure_type"],
            "leak_name": foot.get("leak_name", "Logistics Delivery")
        })

    masked_relatives = []
    for rel in relatives:
        masked_relatives.append({
            "id": rel["id"],
            "full_name": mask_name(rel["full_name"], audit_mode),
            "relationship": rel["relationship"],
            "contact_email": mask_email(rel["contact_email"], audit_mode),
            "contact_phone": mask_phone(rel["contact_phone"], audit_mode),
            "social_engineering_risk": rel["social_engineering_risk"],
            "shared_city": mask_city(rel.get("city"), audit_mode)
        })

    # 4. Format Leaks with exposed data classes
    import json
    from backend.osint_scanner import KNOWN_REAL_BREACHES
    formatted_leaks = []
    for lk in leaks:
        item = dict(lk)
        exp = item.get("exposed_data")
        if isinstance(exp, str):
            try:
                item["exposed_data"] = json.loads(exp)
            except Exception:
                item["exposed_data"] = [e.strip() for e in exp.split(",") if e.strip()]
        elif not exp:
            name_lower = (item.get("leak_name") or "").lower()
            matched = None
            for k, v in KNOWN_REAL_BREACHES.items():
                if k in name_lower or v.get("breach_name", "").lower() in name_lower:
                    matched = v.get("exposed_data")
                    break
            item["exposed_data"] = matched or []
        item["circulation_intel"] = get_breach_circulation_intel(item.get("leak_name", ""), item.get("exposed_data"))
        formatted_leaks.append(item)

    # 5. Generate Threat Provenance & Attacker Vectors Matrix
    threat_matrix = generate_threat_provenance_matrix(
        employee=employee,
        leaks=leaks,
        credentials=credentials,
        pivots=pivots,
        physical_footprints=footprints,
        relatives=relatives
    )

    # 6. Compile Unified Identity & Incident Evolution Timeline
    timeline_events = []
    for piv in pivots:
        if piv["pivot_type"] == "TIMELINE":
            c_note = piv.get("context_note", "")
            val = piv.get("pivot_value", "")
            year_part = val.split(":")[0].strip() if ":" in val else "Historical"
            title_part = val.split(":", 1)[1].strip() if ":" in val else val
            type_match = re.search(r'\[Category:\s*([^\]]+)\]', c_note)
            evt_type = type_match.group(1) if type_match else "Milestone"
            timeline_events.append({
                "period": year_part,
                "title": title_part,
                "description": c_note.split("[Category:")[0].strip() if "[Category:" in c_note else c_note,
                "type": evt_type,
                "badge_class": "badge-info"
            })

    for lk in formatted_leaks:
        b_date = lk.get("breach_date")
        if b_date:
            year_str = str(b_date)[:4]
            timeline_events.append({
                "period": year_str,
                "title": f"Security Incident: {lk.get('leak_name')}",
                "description": f"Exfiltrated via {lk.get('threat_actor_source', 'Breach')} ({lk.get('severity', 'HIGH')} Severity)",
                "type": "Breach Exposure",
                "badge_class": "badge-critical"
            })

    def parse_timeline_year(item):
        m = re.search(r'(\d{4})', item.get("period", ""))
        return int(m.group(1)) if m else 9999

    timeline_events.sort(key=parse_timeline_year)

    eff_domain = cleaned_email.split("@")[-1] if "@" in cleaned_email else ""
    from backend.live_osint import check_disposable_email
    disp_intel = check_disposable_email(eff_domain)

    discovered_names = set()
    if employee and employee.get("full_name") and not employee["full_name"].lower().startswith("webmail"):
        discovered_names.add(employee["full_name"])
    for p in pivots:
        if p.get("pivot_type") == "FULL_NAME":
            discovered_names.add(p.get("pivot_value", "").replace("Full Name:", "").strip())

    dorks_intel = generate_osint_dorks(cleaned_email, eff_domain, discovered_names)

    # 5. Harvest target avatars & visual assets for Image Correlation
    from backend.image_recon import harvest_target_images
    candidate_handles = []
    for p in pivots:
        if p.get("pivot_type") == "PUBLIC_PROFILE":
            val = p.get("pivot_value", "")
            if ":" in val:
                candidate_handles.append(val.split(":", 1)[1].strip())
    if known_username:
        candidate_handles.append(known_username.strip())

    discovered_images = harvest_target_images(
        email=cleaned_email,
        target_name=employee.get("full_name", ""),
        handles=candidate_handles
    )

    # 6. Extract suggested phone directories based on target name and location
    from backend.telecom_recon import get_country_directories, COUNTRY_CODE_MAP
    target_country_iso = None
    for foot in footprints:
        if foot.get("country"):
            for pfx, c_info in COUNTRY_CODE_MAP.items():
                if c_info["country"].lower() in foot["country"].lower():
                    target_country_iso = c_info["iso"]
                    break
            if target_country_iso:
                break
    suggested_phone_directories = get_country_directories(
        query=employee.get("full_name") or cleaned_email,
        country_iso=target_country_iso or "GLOBAL",
        query_type="person"
    )

    return {
        "employee": masked_emp,
        "email_verification": verification,
        "threat_provenance_matrix": threat_matrix,
        "spillover_score": spillover,
        "leaks": formatted_leaks,
        "credentials": masked_creds,
        "pivots": masked_pivots,
        "physical_footprints": masked_footprints,
        "relatives": masked_relatives,
        "graph": graph,
        "timeline": timeline_events,
        "disposable_intelligence": disp_intel,
        "osint_dorks": dorks_intel,
        "images": discovered_images,
        "suggested_phone_directories": suggested_phone_directories,
        "audit_mode": audit_mode,
        "cross_target_correlations": cross_correlations,
        "scenario": scenario or ("clean" if spillover["score"] == 0 else "full")
    }

class CombolistImportRequest(BaseModel):
    raw_text: str
    leak_name: str = "Custom Combolist Leak"
    leak_type: str = "DATABASE_LEAK"
    breach_date: Optional[str] = None
    source: str = "Web UI Ingestion"

@app.post("/api/breach/import-text")
def import_breach_combolist_text(req: CombolistImportRequest):
    """
    Direct in-memory / paste ingestion of combolist records (email:password or user:email:password)
    with instant deduplication, hashing, and relational index creation.
    """
    from import_breach import import_combolist_text
    if not req.raw_text or not req.raw_text.strip():
        raise HTTPException(status_code=400, detail="Please provide combolist lines to import.")
    result = import_combolist_text(
        raw_text=req.raw_text,
        leak_name=req.leak_name,
        leak_type=req.leak_type,
        breach_date=req.breach_date,
        source=req.source
    )
    return result

@app.post("/api/scan/batch")
def scan_batch_identities(req: BatchScanRequest):
    """
    WhatBreach Batch Processing Mode:
    Executes scans across up to 20 target emails to analyze
    group-wide attack surface, shared breach overlap, and organizational spillover risks.
    """
    raw_emails = req.emails[:20]
    if not raw_emails:
        raise HTTPException(status_code=400, detail="Please provide at least one email address to scan.")

    cleaned_list = []
    seen = set()
    for e in raw_emails:
        c = (e or "").strip().lower()
        if c and "@" in c and c not in seen:
            seen.add(c)
            cleaned_list.append(c)

    results = []
    shared_breaches_map: Dict[str, List[str]] = {}
    shared_hashes_map: Dict[str, List[str]] = {}
    total_leaks_count = 0
    max_risk_score = 0
    sum_risk_score = 0

    for email in cleaned_list:
        try:
            res = search_exposure(email=email, audit_mode=req.audit_mode)
            emp = res["employee"]
            sc = res["spillover_score"]
            leaks = res["leaks"]
            creds = res["credentials"]
            pivots = res["pivots"]
            
            score_val = sc.get("numeric_score")
            if score_val is None:
                s_str = str(sc.get("score", ""))
                score_val = 95 if "1" in s_str else (75 if "2" in s_str else (45 if "3" in s_str else (20 if "4" in s_str else 0)))
            max_risk_score = max(max_risk_score, score_val)
            sum_risk_score += score_val
            total_leaks_count += len(leaks)

            for lk in leaks:
                b_name = lk.get("leak_name", "Unknown")
                shared_breaches_map.setdefault(b_name, []).append(email)

            for cr in creds:
                h = cr.get("password_hash")
                if h and len(h) > 8:
                    shared_hashes_map.setdefault(h, []).append(email)

            results.append({
                "email": email,
                "full_name": emp.get("full_name"),
                "risk_score": score_val,
                "risk_level": sc.get("level", "LOW"),
                "leaks_count": len(leaks),
                "credentials_count": len(creds),
                "pivots_count": len(pivots),
                "top_breaches": [l["leak_name"] for l in leaks[:4]],
                "is_disposable": res.get("disposable_intelligence", {}).get("is_disposable", False)
            })
        except Exception as err:
            results.append({
                "email": email,
                "error": str(err),
                "risk_score": 0,
                "risk_level": "UNKNOWN",
                "leaks_count": 0,
                "top_breaches": []
            })

    cross_account_breaches = [
        {"breach_name": b, "affected_emails": emails, "count": len(emails)}
        for b, emails in shared_breaches_map.items() if len(emails) > 1
    ]
    cross_account_breaches.sort(key=lambda x: -x["count"])

    cross_account_hashes = [
        {"hash_fragment": h[:15] + "...", "affected_emails": emails, "count": len(emails)}
        for h, emails in shared_hashes_map.items() if len(emails) > 1
    ]

    avg_score = round(sum_risk_score / len(cleaned_list), 1) if cleaned_list else 0
    collective_level = "CRITICAL" if max_risk_score >= 80 else ("HIGH" if max_risk_score >= 60 else ("MEDIUM" if max_risk_score >= 35 else "LOW"))

    return {
        "total_targets": len(cleaned_list),
        "compromised_targets": len([r for r in results if r.get("leaks_count", 0) > 0]),
        "total_leaks_detected": total_leaks_count,
        "collective_risk_score": max_risk_score,
        "average_risk_score": avg_score,
        "collective_risk_level": collective_level,
        "shared_breaches": cross_account_breaches,
        "shared_credential_hashes": cross_account_hashes,
        "targets": results
    }

@app.get("/api/domain/recon")
def get_domain_recon(domain: str = Query(..., description="Target corporate domain (e.g. cybercorp.io)")):
    """
    EmploLeaks Corporate Attack Surface Reconnaissance:
    Enumerates subdomains, analyzes MX/SPF/DMARC mail spoofability,
    evaluates employee breach exposures, and calculates organizational attack surface risk.
    """
    clean_dom = domain.strip().lower().lstrip("@")
    if not clean_dom or "." not in clean_dom:
        raise HTTPException(status_code=400, detail="Invalid domain format.")

    # 1. DNS & Mail Routing Infrastructure
    infra = query_domain_infrastructure(f"security@{clean_dom}")
    
    # 2. Certificate Transparency & DoH Subdomain Enumeration
    subdomains = query_crtsh_subdomains(clean_dom)

    # 2b. Historical Web & Archive Reconnaissance (Wayback, AlienVault OTX, URLScan.io)
    from backend.archive_recon import query_historical_archives
    archive_recon = query_historical_archives(clean_dom)

    existing_subs = set(s["subdomain"].lower() for s in subdomains)
    for asub in archive_recon.get("discovered_subdomains", []):
        if asub.lower() not in existing_subs:
            existing_subs.add(asub.lower())
            subdomains.append({
                "subdomain": asub,
                "category": "ARCHIVED_HOST",
                "risk_level": "INFO",
                "url": f"https://{asub}",
                "description": "Historical subdomain mapped from web archive crawl index."
            })

    # 3. Known Company Employees in Database
    employees = get_employees_by_domain(clean_dom)
    total_staff = len(employees)
    breached_staff = sum(1 for e in employees if (e.get("creds_count", 0) > 0 or e.get("direct_leaks_count", 0) > 0))
    total_creds = sum(e.get("creds_count", 0) for e in employees)

    # 4. Attack Surface Risk Rating
    high_risk_portals = [s for s in subdomains if s.get("risk_level") == "HIGH"]
    sensitive_exposures = archive_recon.get("sensitive_exposures_count", 0)
    
    if breached_staff > 0 and len(high_risk_portals) > 0:
        org_risk = "CRITICAL"
        risk_summary = (
            f"Active credential stuffing & lateral movement threat! Found {len(high_risk_portals)} external login "
            f"portals (VPN/SSO/Admin) alongside {breached_staff} compromised employees with {total_creds} leaked credentials."
        )
    elif breached_staff > 0 or len(high_risk_portals) > 0 or sensitive_exposures > 0:
        org_risk = "HIGH"
        risk_summary = (
            f"Elevated exposure. {len(subdomains)} corporate subdomains mapped with {breached_staff} "
            f"compromised identities" + (f" and {sensitive_exposures} sensitive historical exposures." if sensitive_exposures > 0 else " identified.")
        )
    elif infra and infra.get("spoofable"):
        org_risk = "MEDIUM"
        risk_summary = f"Anti-spoofing deficiency: DMARC policy is {infra.get('dmarc_policy')}. Domain is vulnerable to BEC / spear phishing."
    else:
        org_risk = "LOW"
        risk_summary = "Hardened perimeter. Strict mail authentication and minimal exposed remote administrative surfaces."

    # Corporate OSINT Dorks (EmploLeaks employee harvest, secret leaks, and paste dumps)
    q_dom = urllib.parse.quote(clean_dom)

    corp_dorks = [
        {
            "category": "Employee Roster (LinkedIn)",
            "title": f"LinkedIn Staff Roster: {clean_dom}",
            "description": "Discovers current and former company employees, job titles, and departments on LinkedIn.",
            "url": f"https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22at+{q_dom}%22+OR+%22{q_dom}%22"
        },
        {
            "category": "Code Secrets & Tokens",
            "title": f"GitHub Secrets & API Keys: {clean_dom}",
            "description": "Searches public GitHub code repositories for hardcoded credentials, connection strings, and tokens.",
            "url": f"https://www.google.com/search?q=site%3Agithub.com+%22{q_dom}%22+password+OR+api_key+OR+secret+OR+.env"
        },
        {
            "category": "Pastebin Dumps",
            "title": f"Pastebin Corporate Dumps: {clean_dom}",
            "description": "Searches Pastebin and public paste repositories for leaked corporate credentials and combolists.",
            "url": f"https://www.google.com/search?q=site%3Apastebin.com+%22{q_dom}%22"
        },
        {
            "category": "GitLab Projects",
            "title": f"GitLab Public Repositories: {clean_dom}",
            "description": "Discovers public repositories and snippets on GitLab containing the corporate domain.",
            "url": f"https://gitlab.com/search?search={q_dom}&nav_source=navbar"
        }
    ]

    return {
        "domain": clean_dom,
        "infrastructure": infra,
        "subdomains": subdomains,
        "total_subdomains": len(subdomains),
        "high_risk_portals": len(high_risk_portals),
        "historical_archives": archive_recon,
        "organization_risk": {
            "level": org_risk,
            "summary": risk_summary,
            "total_staff_indexed": total_staff,
            "breached_staff_count": breached_staff,
            "total_leaked_credentials": total_creds,
            "sensitive_exposures_count": sensitive_exposures
        },
        "corporate_osint_dorks": corp_dorks,
        "employees": [
            {
                "id": e["id"],
                "full_name": e["full_name"],
                "corporate_email": e["corporate_email"],
                "job_title": e["job_title"],
                "department": e["department"],
                "vip_level": e["vip_level"],
                "creds_count": e.get("creds_count", 0),
                "direct_leaks_count": e.get("direct_leaks_count", 0)
            }
            for e in employees
        ]
    }

@app.get("/api/hash/resolve")
def resolve_hash_endpoint(hash: str, algorithm: Optional[str] = None):
    """
    WhatBreach-grade Online Rainbow Table & Hash Cracker API:
    Queries public hash-cracking lookup services and dictionary tables to resolve hashes.
    """
    from backend.hash_resolver import resolve_hash_online
    if not hash or len(hash.strip()) < 8:
        raise HTTPException(status_code=400, detail="Please provide a valid cryptographic hash string.")
    return resolve_hash_online(hash.strip(), algorithm_hint=algorithm)
class AIDossierRequest(BaseModel):
    email: str
    api_key: Optional[str] = None
    provider: Optional[str] = "groq"
    scan_data: Optional[Dict[str, Any]] = None
    force_refresh: Optional[bool] = False

class AICopilotRequest(BaseModel):
    email: str
    message: str
    history: Optional[List[Dict[str, str]]] = None
    api_key: Optional[str] = None
    provider: Optional[str] = "groq"
    scan_data: Optional[Dict[str, Any]] = None

class AITestKeyRequest(BaseModel):
    api_key: Optional[str] = None
    provider: Optional[str] = "groq"

@app.post("/api/ai/dossier")
def get_ai_dossier(req: AIDossierRequest):
    """
    Generates a structured AI Threat Dossier using Groq (Llama 3.3 70B) or Gemini,
    with an intelligent offline deterministic fallback.
    """
    from backend.ai_engine import generate_ai_threat_dossier
    scan_data = req.scan_data
    if not scan_data:
        scan_data = search_exposure(email=req.email, audit_mode=True)
    dossier = generate_ai_threat_dossier(
        scan_data=scan_data,
        api_key=req.api_key,
        provider=req.provider or "groq",
        force_refresh=req.force_refresh or False
    )
    return dossier

@app.post("/api/ai/copilot")
def query_ai_copilot(req: AICopilotRequest):
    """
    Interactive Investigator Copilot: answers target-specific threat and mitigation questions.
    """
    from backend.ai_engine import ai_copilot_chat
    scan_data = req.scan_data
    if not scan_data:
        scan_data = search_exposure(email=req.email, audit_mode=True)
    res = ai_copilot_chat(
        user_query=req.message,
        scan_data=scan_data,
        history=req.history,
        api_key=req.api_key,
        provider=req.provider or "groq"
    )
    return res

@app.post("/api/ai/test-key")
def test_ai_key(req: AITestKeyRequest):
    """
    Validates a Groq or Gemini API key with a fast 1-token probe.
    If no key is sent in the body, it checks .env or environment variables.
    """
    from backend.ai_engine import test_ai_connection, resolve_api_key
    clean_key = (req.api_key or "").strip() or resolve_api_key(req.provider or "groq")
    if not clean_key:
        raise HTTPException(status_code=400, detail="API key is required or not found in .env.")
    return test_ai_connection(api_key=clean_key, provider=req.provider or "groq")

@app.get("/api/ai/status")
def get_ai_status():
    """
    Returns server-side AI configuration state so the frontend can display
    active connection status when keys are configured in .env.
    """
    from backend.ai_engine import resolve_api_key, GROQ_DEFAULT_MODEL, GEMINI_DEFAULT_MODEL
    groq_key = resolve_api_key("groq")
    gemini_key = resolve_api_key("gemini")

    if groq_key:
        masked = groq_key[:6] + "..." + groq_key[-4:] if len(groq_key) > 10 else "***"
        return {
            "has_key": True,
            "provider": "groq",
            "model": os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL),
            "source": "env",
            "masked_key": masked
        }
    elif gemini_key:
        masked = gemini_key[:6] + "..." + gemini_key[-4:] if len(gemini_key) > 10 else "***"
        return {
            "has_key": True,
            "provider": "gemini",
            "model": GEMINI_DEFAULT_MODEL,
            "source": "env",
            "masked_key": masked
        }
    else:
        return {
            "has_key": False,
            "provider": "offline",
            "model": "offline-cti-rules",
            "source": "none",
            "masked_key": ""
        }

class TelecomReconRequest(BaseModel):
    query: str
    country_hint: Optional[str] = None

@app.post("/api/recon/telecom")
def recon_telecom_post(req: TelecomReconRequest):
    """
    Multi-country telephone & civil directory reconnaissance.
    Provides E.164 parsing, carrier detection, and direct national registry links
    for Norway, Sweden, Denmark, Poland, USA, UK, Germany, and International.
    """
    from backend.telecom_recon import query_live_international_telecom
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query (name or phone number) is required.")
    return query_live_international_telecom(req.query.strip(), req.country_hint)

@app.get("/api/recon/telecom")
def recon_telecom_get(query: str = Query(...), country: Optional[str] = None):
    from backend.telecom_recon import query_live_international_telecom
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query is required.")
    return query_live_international_telecom(query.strip(), country)

@app.get("/api/recon/reverse-phone")
def recon_reverse_phone(phone: str = Query(..., description="Phone number to reverse-lookup in any international format")):
    """
    Dedicated Reverse Phone Number Search Engine:
    Validates E.164, detects carrier network, determines line classification (Mobile/Landline/VoIP),
    generates messaging direct links (WhatsApp, Telegram), maps authoritative national directories,
    and cross-correlates internal breach databases.
    """
    from backend.telecom_recon import reverse_phone_lookup
    if not phone or not phone.strip():
        raise HTTPException(status_code=400, detail="Phone number query is required.")
    return reverse_phone_lookup(phone.strip())

@app.get("/api/recon/images")
def recon_target_images(
    email: Optional[str] = Query(None, description="Target email address"),
    name: Optional[str] = Query(None, description="Target full name"),
    handle: Optional[str] = Query(None, description="Known handle or username")
):
    """
    Harvests authentic profile pictures and avatars across Gravatar, GitHub, and Duolingo,
    and provides pre-formatted 1-click reverse visual search links.
    """
    from backend.image_recon import harvest_target_images
    handles = [handle.strip()] if handle and handle.strip() else []
    images = harvest_target_images(email=(email or "").strip(), target_name=(name or "").strip(), handles=handles)
    return {"success": True, "count": len(images), "images": images}

class ReverseImageLinkRequest(BaseModel):
    image_url: str

@app.post("/api/recon/reverse-image-urls")
def recon_reverse_image_urls(req: ReverseImageLinkRequest):
    """
    Generates 1-click reverse image search query links (Google Lens, Yandex, TinEye, Bing Visual, PimEyes)
    for an arbitrary user-supplied image URL.
    """
    from backend.image_recon import build_reverse_image_search_links
    if not req.image_url or not req.image_url.strip():
        raise HTTPException(status_code=400, detail="Image URL is required.")
    links = build_reverse_image_search_links(req.image_url.strip())
    return {"success": True, "image_url": req.image_url.strip(), "reverse_search_links": links}


# ==============================================================================
# Advanced OSINT & Graph Pivot Expansion Endpoints
# ==============================================================================

class PivotExpandRequest(BaseModel):
    node_id: str
    pivot_type: Optional[str] = None
    pivot_value: Optional[str] = None
    current_node_ids: Optional[List[str]] = None
    audit_mode: bool = True

@app.post("/api/graph/pivot-expand")
def api_graph_pivot_expand(req: PivotExpandRequest):
    """
    Executes multi-hop link expansion from an arbitrary selected graph node.
    Traverses SQLite credential reuse, incident leaks, infrastructure subdomains,
    and external OSINT handles to dynamically attach new branch nodes and edges in Vis.js.
    """
    from backend.graph_builder import build_pivot_expansion_nodes_and_edges
    if not req.node_id:
        raise HTTPException(status_code=400, detail="node_id is required.")
    return build_pivot_expansion_nodes_and_edges(
        node_id=req.node_id,
        pivot_type=req.pivot_type,
        pivot_value=req.pivot_value,
        current_node_ids=req.current_node_ids,
        audit_mode=req.audit_mode
    )

@app.get("/api/recon/wmn")
def api_recon_wmn(
    handle: str = Query(..., description="Handle or username to enumerate across 700+ platforms"),
    category: Optional[str] = Query(None, description="Optional category filter (e.g. social, tech, gaming)"),
    max_sites: int = Query(50, ge=1, le=200, description="Max sites to probe concurrently"),
    priority_only: bool = Query(False, description="Scan only top high-value priority sites")
):
    """
    WhatsMyName (WMN) Account Enumeration Engine.
    Executes concurrent multi-platform handle verification across WMN database.
    """
    from backend.wmn_engine import enumerate_handle_wmn
    clean_handle = handle.strip()
    if not clean_handle:
        raise HTTPException(status_code=400, detail="Handle is required.")
    return enumerate_handle_wmn(
        handle=clean_handle,
        category=category,
        max_sites=max_sites,
        priority_only=priority_only
    )

@app.get("/api/recon/infrastructure")
def api_recon_infrastructure(
    domain: str = Query(..., description="Target domain for passive DNS, CT logs, and MX intelligence")
):
    """
    Passive DNS, Certificate Transparency, and Mail Infrastructure Intelligence.
    Aggregates DoH DNS records, crt.sh CT logs, MX providers, and SPF/DMARC posture.
    """
    from backend.dns_recon import gather_domain_infrastructure
    clean_domain = domain.strip().lower()
    if not clean_domain:
        raise HTTPException(status_code=400, detail="Domain is required.")
    return gather_domain_infrastructure(clean_domain)

@app.get("/api/recon/pastes")
def api_recon_pastes(
    target: str = Query(..., description="Target email, domain, handle, or hash to search in public pastes"),
    max_results: int = Query(20, ge=1, le=50, description="Maximum paste records to return")
):
    """
    Live Threat Dump & Paste Aggregator Engine.
    Automates passive searches for exposed credentials, combo-lists, database dumps,
    and darkweb-mirrored paste dumps (Pastebin, JustPaste.it, Rentry, Ghostbin, GitHub Gist).
    """
    from backend.paste_recon import search_paste_leaks
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target query is required.")
    return search_paste_leaks(clean_target, max_results)


# Mount Static Assets & Frontend
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(
        str(index_file),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
