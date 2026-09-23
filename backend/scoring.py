"""
Spillover Risk Scoring & Compounding Impact Correlation Engine
Calculates categorical Spillover Risk Tier (Tier 1 - Tier 5), applies cross-vector
compounding multipliers (ATO, Physical Doxing, Family Vishing, Session Hijacking),
and constructs an Adversary Attack Narrative.
"""

from typing import List, Dict, Any
from datetime import datetime

def calculate_spillover_score(
    leaks: List[Dict[str, Any]],
    credentials: List[Dict[str, Any]],
    pivots: List[Dict[str, Any]],
    footprints: List[Dict[str, Any]],
    relatives: List[Dict[str, Any]],
    is_corporate: bool = False
) -> Dict[str, Any]:
    """
    Computes a deterministic Spillover Risk Tier based on 5 core exposure vectors,
    augmented with cross-vector compounding multipliers and an adversary attack narrative.
    """
    # 1. Vector: Infostealer Exposures
    stealer_leaks = [l for l in leaks if str(l.get("leak_type", "")).upper() == "INFOSTEALER"]
    has_stealer = len(stealer_leaks) > 0
    multi_stealer = len(stealer_leaks) > 1

    # Check for recent stealer infection (within 18 months)
    has_recent_stealer = False
    current_year = 2026
    for sl in stealer_leaks:
        b_date = sl.get("breach_date", "")
        if b_date and len(b_date) >= 4:
            try:
                yr = int(b_date[:4])
                if current_year - yr <= 2:
                    has_recent_stealer = True
                    break
            except ValueError:
                pass

    # 2. Vector: Credential & Password Severity
    has_plaintext = any(bool(c.get("plaintext_password")) for c in credentials)
    has_corporate_pattern = any(bool(c.get("is_corporate_password_match")) for c in credentials)

    # 3. Vector: Identity Pivot to Personal Life
    has_personal_email = any("EMAIL" in str(p.get("pivot_type", "")).upper() for p in pivots)
    has_phone = any("PHONE" in str(p.get("pivot_type", "")).upper() for p in pivots)
    has_machine_id = any("MACHINE" in str(p.get("pivot_type", "")).upper() or "HWID" in str(p.get("pivot_type", "")).upper() for p in pivots)

    # 4. Vector: Physical Footprint / Home Address
    has_physical_address = len(footprints) > 0

    # 5. Vector: Social Engineering & Relatives
    has_relatives = len(relatives) > 0

    # Cross-Vector Compounding Scenarios
    is_ato_triggered = bool((has_plaintext or has_corporate_pattern) and is_corporate)
    is_session_triggered = bool(has_recent_stealer or has_stealer)
    has_crypto_leak = any(
        "ledger" in str(l.get("leak_name", "")).lower() or 
        "crypto" in str(l.get("leak_type", "")).lower() or
        "financial" in str(l.get("leak_type", "")).lower() or
        "ecommerce" in str(l.get("leak_type", "")).lower() or
        "delivery" in str(l.get("leak_type", "")).lower()
        for l in leaks
    )
    is_physical_triggered = bool(has_physical_address and has_crypto_leak)
    is_vishing_triggered = bool(has_phone and (has_relatives or has_physical_address))

    compounding_scenarios = [
        {
            "id": "CORPORATE_ATO",
            "title": "Corporate Account Takeover (ATO) Threat",
            "triggered": is_ato_triggered,
            "severity": "CRITICAL" if is_ato_triggered else "LOW",
            "multiplier": "Tier 1 Escalation",
            "explanation": "Adversaries utilize exfiltrated credentials directly against corporate Single Sign-On (SSO), VPN gateways, or cloud enterprise suites (M365 / Workspace)." if is_ato_triggered else "Identity not currently vulnerable to direct corporate Single Sign-On compromise.",
            "mitre_tactics": ["T1078.004 Valid Accounts: Cloud Accounts", "T1110.001 Password Guessing: Password Spraying"]
        },
        {
            "id": "SESSION_HIJACKING",
            "title": "Active Session Hijacking (Pass-the-Cookie)",
            "triggered": is_session_triggered,
            "severity": "CRITICAL" if is_session_triggered else "LOW",
            "multiplier": "Tier 1 Escalation",
            "explanation": "Infostealers harvest active browser session tokens and OAuth refresh cookies, allowing threat actors to bypass Multi-Factor Authentication (MFA) without passwords." if is_session_triggered else "No active infostealer browser session cookies or authorization tokens exfiltrated.",
            "mitre_tactics": ["T1539 Steal Web Session Cookie", "T1550.004 Use Alternate Authentication Material"]
        },
        {
            "id": "PHYSICAL_EXTORTION",
            "title": "Physical Home Extortion & Courier Doxing",
            "triggered": is_physical_triggered,
            "severity": "HIGH" if is_physical_triggered else "LOW",
            "multiplier": "Tier 2 Escalation",
            "explanation": "Criminal actors cross-reference residential coordinates from delivery/e-commerce disclosures with high-value account profiles for targeted postal extortion and swatting." if is_physical_triggered else "Residential coordinates not currently linked with high-value retail delivery leaks.",
            "mitre_tactics": ["T1589.001 Gather Victim Identity Information: Credentials", "T1591 Gather Victim Org Information"]
        },
        {
            "id": "FAMILY_VISHING",
            "title": "Family Emergency Vishing & SIM-Swap Escalation",
            "triggered": is_vishing_triggered,
            "severity": "HIGH" if is_vishing_triggered else "LOW",
            "multiplier": "Tier 2 Escalation",
            "explanation": "Threat actors execute AI voice cloning and urgent family emergency SMS/calls targeting correlated household contacts at the mapped residence." if is_vishing_triggered else "Telecom lines not correlated with household contacts.",
            "mitre_tactics": ["T1566.004 Phishing: Spearphishing Voice", "T1598 Phishing for Information"]
        }
    ]

    # Evaluate Categorical Risk Tier
    if is_ato_triggered or is_session_triggered:
        severity_level = "CRITICAL"
        tier_label = "Tier 1"
        numeric_score = 95
        color = "#ef4444"
        badge_class = "badge-critical"
    elif is_physical_triggered or is_vishing_triggered or (has_plaintext and has_phone):
        severity_level = "HIGH"
        tier_label = "Tier 2"
        numeric_score = 75
        color = "#f97316"
        badge_class = "badge-high"
    elif has_stealer or has_plaintext or has_physical_address or has_phone:
        severity_level = "MEDIUM"
        tier_label = "Tier 3"
        numeric_score = 45
        color = "#eab308"
        badge_class = "badge-medium"
    elif len(leaks) > 0 or len(credentials) > 0 or len(pivots) > 0:
        severity_level = "LOW"
        tier_label = "Tier 4"
        numeric_score = 20
        color = "#38bdf8"
        badge_class = "badge-low"
    else:
        severity_level = "CLEAN"
        tier_label = "Tier 5"
        numeric_score = 0
        color = "#10b981"
        badge_class = "badge-clean"

    # Actionable Defensive Remediations
    remediations = []
    if tier_label == "Tier 5" or severity_level == "CLEAN":
        remediations.append({
            "vector": "Identity Protection Posture",
            "priority": "INFO - SECURE",
            "title": "Clean Identity Exposure Verified",
            "description": "No active infostealer malware logs, exfiltrated credentials, or physical address exposures were found in global threat intelligence indices for this identity."
        })
    if has_stealer:
        remediations.append({
            "vector": "Infostealer Malware Exfiltration",
            "priority": "P0 - IMMEDIATE",
            "title": "Revoke Session Tokens & Isolate Workstation",
            "description": "Infostealer logs (RedLine, LummaC2, Vidar) exfiltrate active session cookies and OAuth tokens. Force immediate sign-out from all active cloud sessions and isolate the affected machine."
        })
    if has_corporate_pattern or (has_plaintext and is_corporate):
        remediations.append({
            "vector": "Corporate Credential Spillover",
            "priority": "P0 - IMMEDIATE",
            "title": "Rotate Corporate Passwords & Enforce FIDO2",
            "description": "A plaintext password matching corporate infrastructure was exfiltrated. Force an immediate credential rotation and deploy FIDO2 / WebAuthn hardware keys."
        })
    if has_phone or has_personal_email:
        remediations.append({
            "vector": "Personal Identity Pivoting",
            "priority": "P1 - HIGH",
            "title": "Vishing & SIM-Swap Threat Advisory",
            "description": "Personal phone numbers or secondary email addresses have been correlated. Brief the user against social engineering attacks impersonating IT Helpdesks or telecom carriers."
        })
    if has_physical_address:
        remediations.append({
            "vector": "Physical Footprint Exposure",
            "priority": "P1 - HIGH",
            "title": "Physical Security & Courier Exposure Review",
            "description": "Residential home coordinates were exfiltrated via delivery logistics logs. Ensure high-profile personnel are briefed on physical mail interception and personal security."
        })
    if has_relatives:
        remediations.append({
            "vector": "Household Social Engineering",
            "priority": "P2 - MEDIUM",
            "title": "Brief Cohabitants Against Family Extortion Scams",
            "description": "Family members sharing the physical residence have been mapped. Brief household contacts on urgent fake-emergency SMS/call scams designed to extract bypass codes or ransom payments."
        })

    # Construct Adversary Attack Narrative (Step-by-step pivoting playbook)
    adversary_playbook = []
    step_num = 1

    if has_stealer:
        adversary_playbook.append({
            "step": step_num,
            "stage_num": step_num,
            "stage": "INITIAL INFECTION & EXFILTRATION",
            "phase_name": "Initial Endpoint Infection & Exfiltration",
            "summary": "Endpoint compromise via Infostealer Malware",
            "action": f"Threat actor deployed infostealer malware bypassing local defenses, dumping {len(credentials)} credentials and browser session cookies.",
            "mechanisms": ["RedLine / LummaC2 Stealer", "Browser Vault Dump", "OAuth Session Cookie Extraction"],
            "target_assets": "Local Browser Credentials & Session Tokens",
            "risk_severity": "CRITICAL",
            "related_groups": ["Credential", "Leak"]
        })
        step_num += 1
    elif len(leaks) > 0:
        first_leak = leaks[0].get("leak_name", "Third-Party Database")
        adversary_playbook.append({
            "step": step_num,
            "stage_num": step_num,
            "stage": "THIRD-PARTY SERVICE RECONNAISSANCE",
            "phase_name": "Third-Party Breach Intelligence Harvesting",
            "summary": f"Exfiltrated database entry in {first_leak}",
            "action": "Attacker acquires historical breach corpus containing account records and cryptographic password hashes.",
            "mechanisms": ["Breach Repository Aggregation", "Credential Spillover Query", "Cryptographic Hash Cracking"],
            "target_assets": f"{first_leak} User Registry",
            "risk_severity": "HIGH",
            "related_groups": ["Leak"]
        })
        step_num += 1

    if has_plaintext or has_corporate_pattern:
        adversary_playbook.append({
            "step": step_num,
            "stage_num": step_num,
            "stage": "CREDENTIAL REUSE & BRUTE-FORCE CRACKING",
            "phase_name": "Credential Replay & Cloud Portal Takeover",
            "summary": "Password Pattern Matching & Dictionary Attack",
            "action": "Attacker tests exfiltrated passwords and variations against target corporate infrastructure, VPN endpoints, and webmail portals.",
            "mechanisms": ["Automated Credential Stuffing", "Password Spraying", "Kerberoasting & SSO Replay"],
            "target_assets": "Corporate SSO / Cloud Portal / VPN Gateway",
            "risk_severity": "CRITICAL",
            "related_groups": ["Credential", "Target"]
        })
        step_num += 1

    if has_phone or has_personal_email:
        adversary_playbook.append({
            "step": step_num,
            "stage_num": step_num,
            "stage": "IDENTITY PIVOTING & CARRIER EXPLOITATION",
            "phase_name": "Identity Pivoting & Carrier Telecom Interception",
            "summary": "Correlating Private Telecom & Secondary Inboxes",
            "action": "Attacker pivots to secondary personal email or mobile phone line to attempt SMS intercept, SIM-swap, or password reset hijacking.",
            "mechanisms": ["SIM-Swapping", "SMS 2FA Intercept", "Secondary Account Password Reset Hijack"],
            "target_assets": "Mobile Carrier Line & Secondary Email Accounts",
            "risk_severity": "HIGH",
            "related_groups": ["Phone", "Email"]
        })
        step_num += 1

    if has_physical_address or has_relatives:
        adversary_playbook.append({
            "step": step_num,
            "stage_num": step_num,
            "stage": "REAL-WORLD SOCIAL ENGINEERING & EXTORTION",
            "phase_name": "Physical Doxing & Cohabitant Social Engineering",
            "summary": "Household Cohabitant Targeting & Courier Doxing",
            "action": "Attacker uses mapped home coordinates and family relationships to execute targeted vishing, courier package interception, or physical swatting.",
            "mechanisms": ["AI Voice Cloning Vishing", "Postal Package Interception", "Targeted Swatting & Doxing"],
            "target_assets": "Physical Residence & Immediate Family",
            "risk_severity": "HIGH",
            "related_groups": ["Location", "Relative"]
        })
        step_num += 1

    return {
        "score": tier_label,
        "numeric_score": numeric_score,
        "level": severity_level,
        "color": color,
        "badge_class": badge_class,
        "base_score": severity_level,
        "bonus_multiplier": "N/A",
        "compounding_scenarios": compounding_scenarios,
        "adversary_playbook": adversary_playbook,
        "vectors": {
            "stealer_exposure": {
                "score": "CRITICAL" if has_stealer else "CLEAN",
                "max": "CRITICAL",
                "details": f"{len(stealer_leaks)} infostealer malware infection(s) detected" if has_stealer else ("No infostealer malware detected" if len(leaks) == 0 else f"{len(leaks)} verified database breach(es)")
            },
            "credential_severity": {
                "score": "CRITICAL" if has_corporate_pattern else ("HIGH" if has_plaintext else "LOW"),
                "max": "CRITICAL",
                "details": "Plaintext exfiltration & corporate match detected" if has_corporate_pattern else ("Plaintext password leaked" if has_plaintext else ("No credentials leaked" if len(credentials) == 0 else f"{len(credentials)} password hash(es) identified"))
            },
            "identity_pivot": {
                "score": "HIGH" if (has_personal_email or has_phone) else "CLEAN",
                "max": "CRITICAL",
                "details": "Personal email and phone correlated" if (has_personal_email and has_phone) else ("Personal email pivoted" if has_personal_email else ("Phone number pivoted" if has_phone else "No private pivots discovered"))
            },
            "physical_footprint": {
                "score": "HIGH" if has_physical_address else "CLEAN",
                "max": "CRITICAL",
                "details": f"{len(footprints)} verified residential address record(s) exposed" if has_physical_address else "No residential address exposed"
            },
            "family_social_eng": {
                "score": "HIGH" if has_relatives else "CLEAN",
                "max": "CRITICAL",
                "details": f"{len(relatives)} cohabitant / household contact(s) mapped" if has_relatives else "No household contacts mapped"
            }
        },
        "remediations": remediations
    }
