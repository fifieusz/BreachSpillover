"""
Threat Intelligence & Forensic Data Provenance Engine
Analyzes where each piece of sensitive data was exfiltrated from,
how an adversary discovers your identity (name, phone, address, family, passwords),
and details every potential cyber and physical threat vector.
"""

from typing import List, Dict, Any

def generate_threat_provenance_matrix(
    employee: Dict[str, Any],
    leaks: List[Dict[str, Any]],
    credentials: List[Dict[str, Any]],
    pivots: List[Dict[str, Any]],
    physical_footprints: List[Dict[str, Any]],
    relatives: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Constructs an exhaustive threat provenance report breaking down:
    - Data Asset (Name, Password, Phone, Address, Relatives, Purchases)
    - Source Incident (Where it was leaked)
    - Exfiltration Technique (How it was taken)
    - Attacker Capability & Threat Vectors (What an attacker can do with it)
    - Specific Mitigation Action
    """
    matrix = []

    # 1. Identity Handle & User Profile
    is_personal = employee.get("job_title") == "Personal Account" or any(
        employee.get("corporate_email", "").endswith(d) for d in [
            "@gmail.com", "@yahoo.com", "@outlook.com", "@hotmail.com", "@proton.me", "@protonmail.com", "@icloud.com"
        ]
    )
    if employee.get("full_name") and employee.get("full_name") != "Target User":
        source_leaks = [l["leak_name"] for l in leaks if any(k in l["leak_name"].lower() for k in ["suno", "canva", "stealer", "shopsphere", "adobe"])]
        origin_str = ", ".join(source_leaks) if source_leaks else "Public Service Breach / Ingested Threat Dump"
        
        asset_title = "Online Handle / Username" if is_personal else "Full Legal Name"
        asset_val = employee['corporate_email'].split('@')[0] if is_personal else employee["full_name"]

        matrix.append({
            "asset_category": "Personal Identity (PII)",
            "asset_name": asset_title,
            "extracted_value": asset_val,
            "origin_incident": origin_str,
            "exfiltration_method": "User registration database dump & platform profile exfiltration.",
            "attacker_capability": "Spear Phishing & Identity Impersonation",
            "threat_severity": "MEDIUM",
            "threat_description": (
                f"An adversary connects '{employee['corporate_email']}' with your identifier '{asset_val}'. "
                "Allows crafting hyper-personalized phishing messages impersonating known platforms, banks, or services, "
                "substantially bypassing human skepticism."
            ),
            "remediation": "Exercise heightened caution on incoming emails/messages addressing you by this identifier. Verify sender email headers."
        })

    # 2. Compromised Credentials & Passwords
    for cred in credentials:
        is_plaintext = bool(cred.get("plaintext_password"))
        is_corp = bool(cred.get("is_corporate_password_match"))
        pwd_val = cred.get("plaintext_password") or cred.get("password_hash") or "Secret Exfiltrated"
        pattern = cred.get("password_pattern") or "Cryptographic Hash"

        if is_plaintext:
            sev = "CRITICAL"
            att_cap = "Immediate Credential Stuffing & Account Takeover (SSO/VPN)"
            desc = (
                f"Plaintext password was captured by malware (Infostealer) from browser memory vaults. "
                "Attackers use automated credential stuffing bots (OpenBullet/SilverBullet) to test this exact password "
                "across Google, Microsoft 365, corporate VPNs, and banking portals within minutes."
            )
            remed = "IMMEDIATE ACTION REQUIRED: Change passwords across all accounts sharing this phrase. Revoke active browser sessions."
        else:
            sev = "HIGH" if "md5" in pattern.lower() or "sha1" in pattern.lower() else "MEDIUM"
            att_cap = "Offline GPU Cluster Hash Cracking"
            desc = (
                f"Password hash ({pattern}) was dumped from {cred['leak_name']}. "
                "While salted hashes (like Bcrypt) require extensive GPU computation, legacy or weak hashes are cracked "
                "almost instantly using precomputed rainbow tables or dictionary attacks."
            )
            remed = "Ensure you do not use this password or variations of it on other platforms. Switch to passkeys and hardware MFA."

        matrix.append({
            "asset_category": "Authentication Secret",
            "asset_name": "Compromised Password / Hash",
            "extracted_value": pwd_val,
            "origin_incident": cred["leak_name"],
            "exfiltration_method": "Browser SQLite vault exfiltration (stealers) or database SQL injection breach.",
            "attacker_capability": att_cap,
            "threat_severity": sev,
            "threat_description": desc,
            "remediation": remed
        })

    # 3. Mobile Phone Numbers
    phone_pivots = [p for p in pivots if "phone" in p.get("pivot_type", "").lower()]
    for p in phone_pivots:
        matrix.append({
            "asset_category": "Telecommunications",
            "asset_name": "Direct Mobile Phone Number",
            "extracted_value": p["pivot_value"],
            "origin_incident": p.get("leak_name", "Service Registration Records (e.g. Suno / Stealer Cache)"),
            "exfiltration_method": "2FA telephone enrollment field exfiltrated from sign-up database.",
            "attacker_capability": "SIM-Swapping, Smishing & WhatsApp Takeover",
            "threat_severity": "HIGH",
            "threat_description": (
                f"Your phone number ({p['pivot_value']}) was linked to your digital identity. "
                "Attackers can execute SIM-swap fraud by social engineering telecom representatives to port your number, "
                "or flood you with smishing (SMS phishing) links posing as package delivery, tax agencies, or bank 2FA requests."
            ) if p.get("pivot_value") else "Phone number exposed.",
            "remediation": "Set a telecom account PIN with your mobile carrier to block unauthorized SIM swaps. Switch 2FA from SMS to authenticator apps (TOTP) or YubiKey."
        })

    # 4. Financial & Payment Profiles (Stripe / Purchases)
    payment_pivots = [p for p in pivots if "payment" in p.get("pivot_type", "").lower() or "purchase" in p.get("pivot_type", "").lower()]
    for p in payment_pivots:
        matrix.append({
            "asset_category": "Financial Telemetry",
            "asset_name": "Payment Records & Partial Card Data",
            "extracted_value": p["pivot_value"],
            "origin_incident": p.get("leak_name", "Suno Stripe Billing Records"),
            "exfiltration_method": "Payment gateway billing records & invoice ledger exfiltration.",
            "attacker_capability": "Financial Vishing & Credit Card Fraud Verification",
            "threat_severity": "HIGH",
            "threat_description": (
                f"Transaction ledgers and partial card data ({p['pivot_value']}) were exposed. "
                "Attackers call you posing as bank fraud investigators, citing your real transaction dates and card last-4 digits "
                "to trick you into approving fraudulent wire transfers or revealing full CVV codes."
            ),
            "remediation": "Monitor bank statements closely. Never confirm banking authorization codes or full card numbers over unsolicited phone calls."
        })

    # 5. Physical Residential Address
    for foot in physical_footprints:
        matrix.append({
            "asset_category": "Physical Location",
            "asset_name": "Residential Home Address",
            "extracted_value": f"{foot['address_line']}, {foot['city']}, {foot['country']}",
            "origin_incident": foot.get("leak_name", "Courier Delivery / Billing Database (e.g. Suno Stripe)"),
            "exfiltration_method": "E-commerce order shipping address or billing invoice record breach.",
            "attacker_capability": "Physical Doxing, Stalking, SWATing & Extortion",
            "threat_severity": "CRITICAL",
            "threat_description": (
                f"Your physical home residence ({foot['address_line']}, {foot['city']}) was unmasked. "
                "Adversaries can correlate this with public voter records or satellite imagery for physical reconnaissance, "
                "send threatening blackmail letters directly to your mailbox, or execute dangerous emergency SWATing hoaxes."
            ),
            "remediation": "Do not publicize physical routines on social media. For public service registrations, use P.O. boxes or commercial drop-off lockers."
        })

    # 6. Household Relatives & Social Engineering
    for rel in relatives:
        matrix.append({
            "asset_category": "Social Engineering Vector",
            "asset_name": f"Household Contact ({rel['relationship']})",
            "extracted_value": rel["full_name"],
            "origin_incident": "Address Sharing Correlation & Co-habitant OSINT Pivot",
            "exfiltration_method": "Relational cross-referencing of residents sharing the same delivery address and last name.",
            "attacker_capability": "Grandparent / Emergency Kidnap Extortion Scam",
            "threat_severity": "HIGH",
            "threat_description": (
                f"Adversary mapped your close contact '{rel['full_name']}' ({rel['relationship']}) sharing your address. "
                "Attackers target family members with AI voice-cloned emergency calls or fake arrest scenarios, "
                "demanding immediate bail/cryptocurrency transfer while pretending you are in grave danger."
            ),
            "remediation": "Establish an internal family 'safe word' or verification protocol with your loved ones to confirm emergency calls before acting."
        })

    return matrix
