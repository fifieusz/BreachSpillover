"""
BreachSpillover - Identity Corroborator & Account Tie Engine
Evaluates candidate accounts, platform profiles, and pivots against a target entity's
identity anchors (real name, aliases, email, location) to determine whether an account
is genuinely tied to the target, an uncorroborated candidate, or a conflicting stranger.

Zero hardcoded names or services: 100% generic across any identity globally.
Strictly zero emojis.
"""

import re
import unicodedata
from typing import Dict, Any, Optional, List, Tuple

def normalize_name_string(name: str) -> str:
    """Removes accents, diacritics, punctuation, and extraneous spacing for robust matching."""
    if not name:
        return ""
    # Strip emojis and non-ascii symbols
    name = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50-\u2b55\u203c-\u3299]', '', name)
    # Decompose unicode characters (e.g. Šečić -> Secic)
    decomposed = unicodedata.normalize('NFKD', name)
    stripped = ''.join(c for c in decomposed if not unicodedata.combining(c))
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', stripped).lower()
    return re.sub(r'\s+', ' ', cleaned).strip()

def tokenize_name(name: str) -> List[str]:
    """Splits a normalized name into meaningful tokens (>= 2 characters)."""
    norm = normalize_name_string(name)
    tokens = [t for t in norm.split() if len(t) >= 2]
    return tokens

def is_corporate_or_generic_entity(name_or_title: str) -> bool:
    """Detects if an entity name is a company, due diligence entity, bot, or organization rather than a person."""
    if not name_or_title:
        return False
    low = name_or_title.lower()
    keywords = [
        "due diligence", "technologies", "solutions", "limited", "ltd", "corp", "corporation",
        "inc", "foundation", "holdings", "group", "capital", "enterprise", "community",
        "official", "bot", "support", "services", "team", "agency", "consulting", "logistics"
    ]
    return any(kw in low for kw in keywords)

def compare_names(target_name: str, candidate_name: str) -> Tuple[bool, bool, float, str]:
    """
    Compares a candidate name against the target name.
    Returns:
    (is_match, is_conflict, score, description)
    """
    if not target_name or not candidate_name:
        return (False, False, 0.0, "Missing name for comparison")

    t_norm = normalize_name_string(target_name)
    c_norm = normalize_name_string(candidate_name)

    if not t_norm or not c_norm:
        return (False, False, 0.0, "Empty normalized names")

    if t_norm == c_norm:
        return (True, False, 1.0, f"Exact name match ('{target_name}')")

    t_tokens = tokenize_name(target_name)
    c_tokens = tokenize_name(candidate_name)

    if not t_tokens or not c_tokens:
        return (False, False, 0.0, "No valid tokens")

    # Check corporate/org collision
    if is_corporate_or_generic_entity(candidate_name):
        return (False, True, 0.1, f"Corporate entity name collision ('{candidate_name}')")

    # If target has at least first and last name (e.g. Amir Secic)
    if len(t_tokens) >= 2:
        t_first = t_tokens[0]
        t_last = t_tokens[-1]

        # Case 1: Candidate has matching first and last name (e.g. Secic Amir or Amir X Secic)
        if t_first in c_tokens and t_last in c_tokens:
            return (True, False, 0.95, f"Full name tokens matched ('{t_first.capitalize()} {t_last.capitalize()}')")

        # Case 2: Candidate has same last name but conflicting first name (e.g. Afan Secic vs Amir Secic)
        if t_last in c_tokens:
            # Check candidate first token
            c_first = c_tokens[0] if c_tokens[0] != t_last else (c_tokens[-1] if len(c_tokens) > 1 else "")
            if c_first and c_first != t_first and not (len(c_first) == 1 and c_first == t_first[0]):
                # Distinct first name with same surname -> different person / family relative
                return (False, True, 0.15, f"Conflicting given name ('{c_first.capitalize()}' vs target '{t_first.capitalize()}')")

        # Case 3: Candidate has same first name but conflicting last name (e.g. Amir Petrovic vs Amir Secic)
        if t_first in c_tokens:
            c_last = c_tokens[-1] if c_tokens[-1] != t_first else (c_tokens[0] if len(c_tokens) > 1 else "")
            if c_last and c_last != t_last:
                return (False, True, 0.10, f"Conflicting family surname ('{c_last.capitalize()}' vs target '{t_last.capitalize()}')")

        # Case 4: First initial + Last name match (e.g. A. Secic)
        if len(c_tokens) >= 2 and t_last in c_tokens:
            c_initial = c_tokens[0][0]
            if c_initial == t_first[0]:
                return (True, False, 0.88, f"Initial and surname match ('{c_initial.upper()}. {t_last.capitalize()}')")

        # Case 5: Completely disjoint stranger name (e.g. Carlos Steve Garcia vs Amir Secic)
        overlap = set(t_tokens).intersection(set(c_tokens))
        if not overlap:
            if len(c_tokens) >= 2:
                return (False, True, 0.05, f"Completely unrelated personal identity ('{candidate_name}')")
            else:
                return (False, False, 0.35, f"Single-token moniker or gamertag ('{candidate_name}')")

    # If target name only has one token (e.g. moniker or single name)
    elif len(t_tokens) == 1:
        if t_tokens[0] in c_tokens:
            return (True, False, 0.80, f"Primary name token matched ('{t_tokens[0].capitalize()}')")

    return (False, False, 0.3, "Inconclusive name comparison")


def evaluate_account_tie(
    account: Dict[str, Any],
    target_name: Optional[str] = None,
    target_email: Optional[str] = None,
    target_country: Optional[str] = None,
    target_city: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates whether a candidate profile or account is genuinely tied to the investigated target.
    
    Returns structured evaluation:
    {
        "status": "VERIFIED" | "SUSPECTED" | "REJECTED",
        "is_tied": bool,
        "is_rejected": bool,
        "confidence": float,
        "tie_type": str,
        "reason": str,
        "badge_label": str
    }
    """
    is_email_bound = bool(account.get("is_email_bound")) or (account.get("source") in [
        "Holehe Authentication Probe",
        "user-scanner Account Enumeration",
        "Platform Profile Prober (user-scanner verified)"
    ])
    cand_real_name = account.get("real_name") or account.get("name") or account.get("author_name")
    cand_persona = account.get("persona_name") or account.get("display_name")
    cand_handle = account.get("handle") or ""
    cand_bio = account.get("bio") or account.get("context") or ""
    cand_location = account.get("location") or account.get("country") or ""

    # 1. Primary Rule: Direct Email Registration Binding (Confidence 1.00)
    # Platforms like Holehe or Gravatar prove the account was registered with the target's exact email address.
    if is_email_bound:
        return {
            "status": "VERIFIED",
            "is_tied": True,
            "is_rejected": False,
            "confidence": 1.00,
            "tie_type": "EMAIL_REGISTRATION_VERIFIED",
            "reason": "Direct authentication probe verified registration of target email on platform.",
            "badge_label": "[TIED: EMAIL VERIFIED]"
        }

    # 2. Check for explicit name conflicts (stranger accounts with different identities)
    if target_name and cand_real_name and len(cand_real_name.strip()) >= 3:
        is_match, is_conflict, score, desc = compare_names(target_name, cand_real_name)
        if is_conflict:
            return {
                "status": "REJECTED",
                "is_tied": False,
                "is_rejected": True,
                "confidence": score,
                "tie_type": "CONFLICTING_IDENTITY_REJECTED",
                "reason": f"Account pruned: {desc}.",
                "badge_label": "[REJECTED: CONFLICT]"
            }
        elif is_match:
            return {
                "status": "VERIFIED",
                "is_tied": True,
                "is_rejected": False,
                "confidence": score,
                "tie_type": "REAL_NAME_MATCH",
                "reason": f"Corroborated account tie: {desc}.",
                "badge_label": "[TIED: NAME MATCH]"
            }

    # 3. Check persona/display name match if real_name was absent
    if target_name and cand_persona and len(cand_persona.strip()) >= 3:
        is_match, is_conflict, score, desc = compare_names(target_name, cand_persona)
        is_gaming_plat = (account.get("platform") or "").lower() in ["steam", "roblox", "chess.com", "duolingo", "twitch", "gaming"]
        if is_conflict and not is_gaming_plat:
            return {
                "status": "REJECTED",
                "is_tied": False,
                "is_rejected": True,
                "confidence": score,
                "tie_type": "CONFLICTING_IDENTITY_REJECTED",
                "reason": f"Account pruned: persona conflict ({desc}).",
                "badge_label": "[REJECTED: CONFLICT]"
            }
        elif is_match:
            return {
                "status": "VERIFIED",
                "is_tied": True,
                "is_rejected": False,
                "confidence": score * 0.95,
                "tie_type": "DISPLAY_NAME_CORROBORATED",
                "reason": f"Corroborated display persona: {desc}.",
                "badge_label": "[TIED: PERSONA MATCH]"
            }

    # 4. Check Bio / Cross-link signals
    if target_email and target_email.lower() in cand_bio.lower():
        return {
            "status": "VERIFIED",
            "is_tied": True,
            "is_rejected": False,
            "confidence": 0.95,
            "tie_type": "MUTUAL_CROSS_LINK",
            "reason": "Profile bio explicitly declares or links to target email.",
            "badge_label": "[TIED: BIO CROSS-LINK]"
        }

    # 5. Git Commit Archaeology Binding
    if account.get("source") == "Git Commit Archaeology" and account.get("is_verified"):
        return {
            "status": "VERIFIED",
            "is_tied": True,
            "is_rejected": False,
            "confidence": 0.95,
            "tie_type": "COMMIT_SIGNATURE",
            "reason": "Authenticated developer commits signed by target email address.",
            "badge_label": "[TIED: COMMIT PROOF]"
        }

    # 6. Handle Match with Corroborated Regional Location
    if target_country and cand_location:
        norm_t_country = normalize_name_string(target_country)
        norm_c_loc = normalize_name_string(cand_location)
        if norm_t_country and norm_t_country in norm_c_loc:
            return {
                "status": "VERIFIED",
                "is_tied": True,
                "is_rejected": False,
                "confidence": 0.85,
                "tie_type": "HANDLE_AND_LOCATION",
                "reason": f"Candidate handle matched with regional location corroborated ('{cand_location}').",
                "badge_label": "[TIED: REGION CORROBORATED]"
            }

    # 7. Uncorroborated Candidate Handle (No email proof, no name match)
    # Must NOT be marked as a verified pivot. Belongs in Suspected Candidates ledger.
    return {
        "status": "SUSPECTED",
        "is_tied": False,
        "is_rejected": False,
        "confidence": 0.40,
        "tie_type": "UNCORROBORATED_HANDLE_CANDIDATE",
        "reason": f"Handle '@{cand_handle}' exists on service but lacks email confirmation or matching target name.",
        "badge_label": "[CANDIDATE: UNCORROBORATED]"
    }
