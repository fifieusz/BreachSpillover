"""
BreachSpillover — Password Complexity, Shannon Entropy & Global Exposure Auditor
Audits individual password strings and candidate identity permutations against:
1. HIBP k-Anonymity global breach prevalence (800M+ real passwords)
2. Information theoretic Shannon entropy & keyspace brute-force resistance
3. Lateral movement & Spillover Risk scoring against the target's identity tokens
"""

import math
import re
import concurrent.futures
from collections import Counter
from typing import Dict, Any, List, Optional
from backend.osint_scanner import check_pwned_password_frequency
from backend.hash_resolver import generate_targeted_candidates

# Thread-safe in-memory cache for HIBP k-Anonymity queries
_HIBP_CACHE: Dict[str, int] = {}

def get_cached_pwned_frequency(password: str) -> int:
    """Returns cached frequency if queried previously, else queries HIBP."""
    if not password:
        return 0
    if password in _HIBP_CACHE:
        return _HIBP_CACHE[password]
    freq = check_pwned_password_frequency(password)
    _HIBP_CACHE[password] = freq
    return freq


def calculate_entropy(password: str) -> Dict[str, Any]:
    """
    Computes Shannon character entropy and keyspace search space bits.
    """
    if not password:
        return {
            "shannon_entropy": 0.0,
            "keyspace_entropy_bits": 0.0,
            "complexity_rating": "Zero Entropy",
            "character_classes": {
                "length": 0,
                "has_lowercase": False,
                "has_uppercase": False,
                "has_digits": False,
                "has_symbols": False
            }
        }

    length = len(password)
    counts = Counter(password)
    shannon = -sum((count / length) * math.log2(count / length) for count in counts.values())

    # Keyspace pool calculation
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)

    pool = 0
    if has_lower: pool += 26
    if has_upper: pool += 26
    if has_digit: pool += 10
    if has_symbol: pool += 33
    pool = max(pool, 1)

    keyspace_bits = round(length * math.log2(pool), 1)

    if keyspace_bits < 28:
        rating = "Very Weak (Trivial Brute Force)"
    elif keyspace_bits < 40:
        rating = "Weak (Susceptible to Offline Cracking)"
    elif keyspace_bits < 56:
        rating = "Moderate (Resilient to Online Spraying)"
    elif keyspace_bits < 75:
        rating = "Strong (High Entropy)"
    else:
        rating = "Cryptographically Hardened"

    return {
        "shannon_entropy": round(shannon, 2),
        "keyspace_entropy_bits": keyspace_bits,
        "complexity_rating": rating,
        "character_classes": {
            "length": length,
            "has_lowercase": has_lower,
            "has_uppercase": has_upper,
            "has_digits": has_digit,
            "has_symbols": has_symbol
        }
    }


def classify_password_pattern(password: str) -> str:
    """
    Identifies common human password construction heuristics and patterns.
    """
    if not password:
        return "Empty"
    if password.isdigit():
        return f"Numeric PIN ({len(password)} digits)"
    if password.isalpha():
        if password.islower():
            return "Lowercase Dictionary Word"
        if password.isupper():
            return "Uppercase Monolithic"
        if password.istitle():
            return "Capitalized Single Word"
        return "Mixed Alphabetic Word"
    
    # Check for corporate template: Capital + letters + Year + Symbol (e.g. Summer2024!)
    if re.match(r'^[A-Z][a-zA-Z]+(19\d{2}|20\d{2})[!@#$%^&*()_+=\-`~\[\]{};:\'",.<>?/]$', password):
        return "Corporate Enterprise Standard (TitleCase + Year + Symbol)"
    if re.match(r'^[a-zA-Z]+(19\d{2}|20\d{2})[!@#$%^&*()_+=\-`~\[\]{};:\'",.<>?/]$', password):
        return "Word + Year + Symbol Suffix"
    if re.match(r'^[a-zA-Z]+(19\d{2}|20\d{2})$', password):
        return "Word + Year Pattern (e.g. 2019/2020 Persona)"
    if re.match(r'^[a-zA-Z]+\d+$', password):
        return "Word + Numeric Suffix"
    if re.match(r'^[a-zA-Z]+[!@#$%^&*()_+=\-`~\[\]{};:\'",.<>?/]\d+$', password):
        return "Word + Symbol + Digits"
    if re.search(r'[A-Z]', password) and re.search(r'[a-z]', password) and re.search(r'\d', password) and re.search(r'[^a-zA-Z0-9]', password):
        return "Full 4-Class Complex Pattern"

    return "Alphanumeric Pattern"


def audit_password_phrase(
    password: str,
    target_context: Optional[Dict[str, Any]] = None,
    check_hibp: bool = True
) -> Dict[str, Any]:
    """
    Performs full forensic audit of a password phrase:
    - Queries HIBP k-Anonymity (if requested)
    - Measures Shannon and keyspace entropy
    - Calculates lateral movement & Spillover Risk Score against the target identity
    """
    clean_pwd = (password or "").strip()
    if not clean_pwd:
        return {
            "password": "",
            "global_frequency": 0,
            "shannon_entropy": 0.0,
            "keyspace_entropy_bits": 0.0,
            "complexity_rating": "None",
            "pattern": "Empty",
            "spillover_risk_score": 0,
            "spillover_risk_tier": "CLEAN",
            "lateral_movement_analysis": "No password string provided."
        }

    freq = get_cached_pwned_frequency(clean_pwd) if check_hibp else 0
    entropy_info = calculate_entropy(clean_pwd)
    pattern = classify_password_pattern(clean_pwd)

    # 1. Base Risk from Global Exposure Frequency
    if freq == 0:
        base_score = 15 if entropy_info["keyspace_entropy_bits"] < 35 else 5
    elif freq < 50:
        base_score = 35
    elif freq < 1000:
        base_score = 55
    elif freq < 10000:
        base_score = 75
    else:
        base_score = 90

    # 2. Lateral Movement & Identity Target Correlation
    lateral_matches = []
    is_identity_bound = False

    if target_context:
        email = (target_context.get("email") or "").lower()
        if "@" in email:
            local = email.split("@")[0]
            if len(local) >= 3 and local in clean_pwd.lower():
                lateral_matches.append(f"email handle stem '{local}'")
                is_identity_bound = True
            for part in re.split(r'[\._\-\+]', local):
                clean_part = re.sub(r'\d+$', '', part)
                if len(clean_part) >= 3 and clean_part in clean_pwd.lower():
                    lateral_matches.append(f"token '{clean_part}'")
                    is_identity_bound = True

        name = (target_context.get("full_name") or "").lower()
        for np in name.split():
            if len(np) >= 3 and np in clean_pwd.lower():
                lateral_matches.append(f"name '{np}'")
                is_identity_bound = True

        for h in target_context.get("handles") or []:
            ch = str(h).lower().lstrip("@")
            stem = re.sub(r'\d+$', '', ch)
            if len(stem) >= 3 and stem in clean_pwd.lower():
                lateral_matches.append(f"handle '{stem}'")
                is_identity_bound = True

    lateral_matches = list(set(lateral_matches))

    # Calculate final score
    score = base_score
    if is_identity_bound:
        score = min(100, score + 35)
    if entropy_info["keyspace_entropy_bits"] < 30:
        score = min(100, score + 15)

    if score >= 85:
        tier = "CRITICAL RISK"
        color = "#ef4444"
    elif score >= 65:
        tier = "HIGH RISK"
        color = "#f97316"
    elif score >= 40:
        tier = "MEDIUM RISK"
        color = "#eab308"
    elif score >= 20:
        tier = "LOW RISK"
        color = "#38bdf8"
    else:
        tier = "SECURE / CLEAN"
        color = "#10b981"

    # Construct narrative
    if is_identity_bound and freq > 0:
        analysis = (
            f"CRITICAL LATERAL MOVEMENT VECTOR: This password string incorporates target identity tokens ({', '.join(lateral_matches)}) "
            f"and has appeared across {freq:,} global public breaches. Threat actors routinely target '{target_context.get('email', 'the victim')}' "
            f"by spraying known username combinations and permutations across external SaaS portals (e.g. Canva, Adobe, Google Workspace)."
        )
    elif is_identity_bound:
        analysis = (
            f"HIGH TARGETED DICTIONARY VULNERABILITY: Although this specific phrase was not indexed in global public breaches (0 occurrences), "
            f"it incorporates target identity tokens ({', '.join(lateral_matches)}). Rule-based adversary hashcat masks will crack this in under 2 minutes."
        )
    elif freq > 0:
        analysis = (
            f"PUBLIC EXPOSURE: This exact password appears in {freq:,} verified compromise records in the global HIBP database. "
            f"It is actively present in threat actor combolists and rockyou wordlists worldwide."
        )
    else:
        analysis = (
            f"CLEAN GLOBAL POSTURE: Zero occurrences found in the global 800M+ breach index. "
            f"Possesses {entropy_info['keyspace_entropy_bits']} bits of entropy."
        )

    return {
        "password": clean_pwd,
        "global_frequency": freq,
        "shannon_entropy": entropy_info["shannon_entropy"],
        "keyspace_entropy_bits": entropy_info["keyspace_entropy_bits"],
        "complexity_rating": entropy_info["complexity_rating"],
        "character_classes": entropy_info["character_classes"],
        "pattern": pattern,
        "spillover_risk_score": score,
        "spillover_risk_tier": tier,
        "tier_color": color,
        "is_identity_bound": is_identity_bound,
        "identity_tokens_matched": lateral_matches,
        "lateral_movement_analysis": analysis
    }


def get_target_connected_strings(
    target_context: Dict[str, Any],
    limit: int = 15
) -> List[Dict[str, Any]]:
    """
    Extracts all candidate strings connected to the target identity:
    1. Known exfiltrated credentials in local DB
    2. Targeted identity candidates (handles, 2019/2020 era permutations, stems)
    Concurrently audits them via HIBP and Shannon entropy.
    """
    email = (target_context.get("email") or "").strip().lower()
    if not email:
        return []

    priority_candidates = []
    seen = set()

    def add_cand(c):
        clean = (c or "").strip()
        if clean and clean not in seen:
            seen.add(clean)
            priority_candidates.append(clean)

    # 1. Add known passwords from DB first
    for kp in target_context.get("known_passwords") or []:
        add_cand(kp)

    # 2. Extract clean, punctuation-free base identity tokens
    local_part = email.split("@")[0] if "@" in email else email
    raw_subparts = [p.strip() for p in re.split(r'[\._\-\+]', local_part) if p.strip()]
    tokens = []
    for p in raw_subparts:
        if len(p) >= 3 and not p.isdigit():
            p_stem = re.sub(r'\d+$', '', p)
            if p_stem and len(p_stem) >= 3 and p_stem not in tokens:
                tokens.append(p_stem)
            if p not in tokens:
                tokens.append(p)
    
    stem = re.sub(r'\d+$', '', local_part).strip("._-+ ")
    if stem and stem not in tokens and len(stem) >= 3 and not stem.isdigit():
        tokens.append(stem)

    name = (target_context.get("full_name") or "").strip()
    if name:
        for n in name.split():
            clean_n = n.strip().lower()
            if len(clean_n) >= 3 and clean_n not in tokens:
                tokens.append(clean_n)

    for h in target_context.get("handles") or []:
        ch = str(h).lower().lstrip("@")
        h_stem = re.sub(r'\d+$', '', ch)
        if len(h_stem) >= 3 and h_stem not in tokens:
            tokens.append(h_stem)

    tokens = list(dict.fromkeys(tokens))  # preserve order

    # 3. High-priority candidate phrases (specifically including base stems & 2019 legacy phrases)
    key_years = ["2019", "2018", "2020", "2024", "123"]
    for t in tokens:
        add_cand(t)
        add_cand(t.capitalize())
        add_cand(f"{t}123")
        add_cand(f"{t.capitalize()}123")
        add_cand(f"{t}123!")
        add_cand(f"{t.capitalize()}123!")
        add_cand(f"{t}2019")
        add_cand(f"{t.capitalize()}2019")
        add_cand(f"{t.capitalize()}2019!")
        add_cand(f"{t}2019!")
        add_cand(f"{t}2018")
        add_cand(f"{t}2020")
        add_cand(f"{t}!")

    # Combine with any numeric sub-parts like '91'
    numeric_parts = [p for p in raw_subparts if p.isdigit()]
    for t in tokens:
        for num in numeric_parts:
            add_cand(f"{t}{num}")
            add_cand(f"{t.capitalize()}{num}")
            add_cand(f"{t}{num}!")

    # 4. Also draw from generate_targeted_candidates
    derived = generate_targeted_candidates(target_context)
    def _rank_candidate(c: str) -> int:
        score = 0
        if "." in c or "@" in c or "+" in c: score -= 50
        if len(c) > 16: score -= 30
        if len(c) < 5: score -= 10
        c_low = c.lower()
        if "2019" in c: score += 40
        if "2018" in c: score += 30
        if "2020" in c: score += 30
        if "123" in c: score += 25
        if "!" in c: score += 15
        return score

    derived.sort(key=_rank_candidate, reverse=True)
    for d in derived:
        add_cand(d)
        if len(priority_candidates) >= limit * 2:
            break

    # Select top candidates up to limit
    selected = priority_candidates[:limit]

    # Concurrently audit candidate strings
    audited = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {
            executor.submit(audit_password_phrase, cand, target_context, True): cand
            for cand in selected
        }
        for future in concurrent.futures.as_completed(future_map):
            try:
                res = future.result()
                audited.append(res)
            except Exception:
                pass

    # Sort audited strings: high risk / high frequency first
    audited.sort(key=lambda x: (x["global_frequency"], x["spillover_risk_score"]), reverse=True)
    return audited
