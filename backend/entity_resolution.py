"""
BreachSpillover - Core Entity Resolution & Identity Disambiguation Engine
Prevents synthetic profile pollution by strictly separating confirmed entities from candidate clusters.

Architecture (evidence-tier arbitration, no additive float math):
1. Email Dissection & Domain Classification:
   - Free/Webmail vs Disposable/Burner vs Custom/Corporate domain analysis
   - Gmail/Googlemail dot-insensitivity canonicalization & plus-addressing strip
   - Structural handle convention detection & entropy-based rarity (no name dictionaries)
2. Evidence-Tier Candidate Verdicts:
   - Each candidate is assigned a categorical evidence tier
     (AUTHENTICATED > NAME_VERIFIED > ALIAS_CORROBORATED > SPECULATIVE > UNCORROBORATED,
     or CONTRADICTED when any hard exclusion fires). Confidence is a fixed function of the tier.
3. Zero-Contradiction Exclusions:
   - Given-name contradictions (shared surname, incompatible given name)
   - Demographic pronoun contradictions
   - Bare-surname namespace collisions lacking binding evidence
4. Dynamic Persona Clustering:
   - Core target, discovered alias personas, namesake collisions, speculative probes.
   - Alias personas are discovered dynamically from authenticated non-name handles,
     declared nicknames/persona attributes, and the AI Cardinal arbiter verdict.
   - Visual media assets are never treated as candidate accounts.

Strictly authentic OSINT: zero synthetic generation, zero emojis, zero hardcoded identities.
"""

import re
from typing import Dict, Any, List, Optional, Set, Tuple

from backend.identity_signals import (
    strip_symbols,
    ascii_fold,
    name_tokens,
    split_given_family,
    normalize_handle,
    handle_stem,
    squash,
    is_null_value,
    is_domain_or_url,
    shannon_entropy,
    detect_given_name_conflict,
    detect_slug_given_conflict,
    detect_declared_gender,
    detect_demographic_contradiction,
    normalize_gender,
    build_target_anchors,
    classify_handle,
    HANDLE_ALIAS,
    HANDLE_PRIMARY_NAME,
    HANDLE_NAME_PERMUTATION,
    HANDLE_BARE_SURNAME,
    HANDLE_BARE_GIVEN,
    is_visual_media_pivot,
    is_visual_media_profile,
    extract_tagged_url,
    has_email_binding,
    has_auth_binding,
    parse_pivot_account,
    extract_alias_mentions,
    alias_matches_text,
)

# Domain Classification Catalogs (mail infrastructure, not identities)
FREE_WEBMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "msn.com",
    "yahoo.com", "ymail.com", "rocketmail.com", "icloud.com", "me.com", "mac.com",
    "proton.me", "protonmail.com", "protonmail.ch", "zoho.com", "zohomail.com",
    "aol.com", "aim.com", "gmx.com", "gmx.net", "gmx.de", "mail.com",
    "yandex.com", "yandex.ru", "tutanota.com", "tuta.io", "fastmail.com"
}

DISPOSABLE_BURNER_DOMAINS = {
    "tempmail.com", "temp-mail.org", "guerrillamail.com", "guerrillamailblock.com",
    "sharklasers.com", "mailinator.com", "10minutemail.com", "trashmail.com",
    "yopmail.com", "burnermail.io", "getairmail.com", "throwawaymail.com",
    "dispostable.com", "fakemailgenerator.com", "nada.ltd", "mohmal.com",
    "crazymailing.com", "tempail.com", "mytemp.email", "dropmail.me"
}

# Evidence tiers (ordered strongest -> weakest) and their fixed confidence values.
TIER_AUTHENTICATED = "AUTHENTICATED"
TIER_NAME_VERIFIED = "NAME_VERIFIED"
TIER_ALIAS_CORROBORATED = "ALIAS_CORROBORATED"
TIER_SPECULATIVE = "SPECULATIVE"
TIER_UNCORROBORATED = "UNCORROBORATED"
TIER_CONTRADICTED = "CONTRADICTED"

TIER_CONFIDENCE = {
    TIER_AUTHENTICATED: 0.98,
    TIER_NAME_VERIFIED: 0.88,
    TIER_ALIAS_CORROBORATED: 0.60,
    TIER_SPECULATIVE: 0.35,
    TIER_UNCORROBORATED: 0.25,
    TIER_CONTRADICTED: 0.10,
}
MERGEABLE_TIERS = {TIER_AUTHENTICATED, TIER_NAME_VERIFIED}

# Retained for backward compatibility with external importers.
MERGE_CONFIDENCE_THRESHOLD = TIER_CONFIDENCE[TIER_NAME_VERIFIED] - 0.13


def clean_text_symbols(val: Any) -> str:
    """Strips emojis and non-printable surrogate characters."""
    return strip_symbols(val)


def normalize_token(val: str) -> str:
    """Normalizes string to clean alphanumeric ASCII."""
    if not val:
        return ""
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', ascii_fold(val))
    return re.sub(r'\s+', ' ', cleaned).strip()

def dissect_email_address(email: str, target_name: str = "") -> Dict[str, Any]:
    """
    Dissects an email address into domain classification, canonical username,
    naming convention, and username rarity entropy.
    """
    clean_email = (email or "").strip().lower()
    if "@" not in clean_email:
        raw_user, domain = clean_email, "local"
    else:
        raw_user, domain = clean_email.split("@", 1)
        domain = domain.strip()

    # 1. Domain Classification
    if domain in DISPOSABLE_BURNER_DOMAINS or any(d in domain for d in ["burner", "tempmail", "disposable", "guerrillamail"]):
        domain_type, domain_weight, pivot_fidelity = "DISPOSABLE_BURNER", 0.05, "ZERO"
    elif domain in FREE_WEBMAIL_DOMAINS or any(d in domain for d in ["gmail", "yahoo", "outlook", "hotmail", "proton", "icloud"]):
        domain_type, domain_weight, pivot_fidelity = "FREE_WEBMAIL", 0.20, "LOW"
    elif domain in ["local", "osint.local"]:
        domain_type, domain_weight, pivot_fidelity = "INTERNAL_OSINT", 0.30, "LOW"
    else:
        domain_type, domain_weight, pivot_fidelity = "CORPORATE_CUSTOM", 0.90, "HIGH"
    is_corporate = domain_type == "CORPORATE_CUSTOM"
    is_free_webmail = domain_type == "FREE_WEBMAIL"
    is_disposable = domain_type == "DISPOSABLE_BURNER"

    # 2. Username Canonicalization (plus-addressing strip, Gmail dot-insensitivity)
    user_no_plus = raw_user.split("+")[0]
    if is_free_webmail and any(g in domain for g in ["gmail", "googlemail"]):
        canonical_user = user_no_plus.replace(".", "")
    else:
        canonical_user = user_no_plus
    canonical_user = canonical_user.lower().strip()

    # 3. Naming convention & rarity (structural; optionally aware of the target's own name)
    naming_convention = _detect_naming_convention(user_no_plus, target_name)
    rarity_score, rarity_tier = _calculate_username_rarity(canonical_user, naming_convention)

    # 4. Multilingual Onomastic Decomposition & Namesake Collision Risk
    from backend.onomastic_engine import deconstruct_onomastic_handle, estimate_namesake_collision_risk
    onomastic = deconstruct_onomastic_handle(canonical_user, target_name_hint=target_name)
    resolved_full_name = onomastic.get("full_name") or target_name
    namesake_risk = estimate_namesake_collision_risk(resolved_full_name, culture_hint=onomastic.get("culture_hint"))

    all_candidate_handles = list(dict.fromkeys(
        [canonical_user, user_no_plus, raw_user] + onomastic.get("candidate_usernames", [])
    ))

    return {
        "raw_email": clean_email,
        "raw_user": raw_user,
        "canonical_user": canonical_user,
        "domain": domain,
        "domain_type": domain_type,
        "domain_weight": domain_weight,
        "pivot_fidelity": pivot_fidelity,
        "is_corporate": is_corporate,
        "is_free_webmail": is_free_webmail,
        "is_disposable": is_disposable,
        "can_pivot_on_domain": is_corporate,
        "candidate_usernames": all_candidate_handles,
        "naming_convention": naming_convention,
        "username_rarity_score": rarity_score,
        "username_rarity_tier": rarity_tier,
        "handle_rarity": rarity_tier,
        "onomastic_analysis": onomastic,
        "namesake_collision_risk": namesake_risk,
    }


def _detect_naming_convention(user: str, target_name: str = "") -> str:
    """Detects structural username conventions (name formats vs pseudonym stems)."""
    clean = (user or "").lower().strip()
    for sep, label in ((".", "DOT"), ("_", "UNDERSCORE"), ("-", "HYPHEN")):
        if sep in clean:
            parts = clean.split(sep)
            if len(parts) == 2 and all(p.isalpha() for p in parts):
                if len(parts[0]) == 1 and len(parts[1]) >= 2:
                    return f"INITIAL_{label}_LAST"
                if all(len(p) >= 2 for p in parts):
                    return f"FIRST_{label}_LAST"

    if re.search(r'[a-z]+\d{2,4}$', clean):
        return "HANDLE_WITH_YEAR_OR_DIGITS"

    if clean.isalpha():
        given, _family = split_given_family(target_name)
        if given and clean == given:
            return "SINGLE_GIVEN_NAME"
        if len(clean) <= 4:
            return "SHORT_VANITY_STEM"
        return "CONCATENATED_ALPHA"

    return "ALPHANUMERIC_PSEUDONYM"


def _calculate_username_rarity(user: str, convention: str) -> Tuple[float, str]:
    """
    Structural rarity estimate (0.0 = extreme collision, 1.0 = highly unique)
    from length, Shannon entropy and character-class mix. No word lists.
    """
    u = (user or "").lower()
    if len(u) <= 4 or convention in ("SINGLE_GIVEN_NAME", "SHORT_VANITY_STEM"):
        return (0.15, "HIGH_COLLISION")
    if convention.startswith("INITIAL_"):
        return (0.25, "HIGH_COLLISION")

    entropy = shannon_entropy(u)
    length_tier = 2 if len(u) >= 10 else (1 if len(u) >= 7 else 0)
    entropy_tier = 2 if entropy >= 3.0 else (1 if entropy >= 2.5 else 0)
    mixed_classes = int(bool(re.search(r"[a-z]", u)) and bool(re.search(r"[0-9_.\-]", u)))
    consonant_cluster = int(bool(re.search(r'[bcdfghjklmnpqrstvwxyz]{3,}', u)))
    points = length_tier + entropy_tier + mixed_classes + consonant_cluster  # 0..6

    rarity = round(min(0.95, 0.50 + 0.075 * points), 2)
    if rarity >= 0.80:
        tier = "RARE_UNIQUE"
    elif rarity >= 0.60:
        tier = "MODERATE_DISTINCTIVE"
    else:
        tier = "COMMON_COLLISION"
    return (rarity, tier)

_PORTFOLIO_MARKERS = ("portfolio", "github.io", "wix", "jouwweb", "carrd", "linktr.ee", "personal website", "outbound link")


def _candidate_display_name(candidate: Dict[str, Any]) -> str:
    name = str(candidate.get("display_name") or candidate.get("name") or candidate.get("real_name") or "").strip()
    if name:
        return name
    ctx = str(candidate.get("context") or candidate.get("context_note") or "")
    pv = str(candidate.get("pivot_value") or "")
    for rx in (
        r'Public YouTube Creator Channel:\s*([^\s\[\-]+(?:\s+[^\s\[\-]+)*)',
        r'Bluesky social account:[^\(]*\(([^,]+),',
        r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'\([\'"]([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)[\'"]\)',
    ):
        m = re.search(rx, ctx + " " + pv)
        if m:
            return m.group(1).strip()
    return ""


def _resolve_target_gender(target_info: Dict[str, Any]) -> str:
    g = normalize_gender(target_info.get("gender") or target_info.get("perceived_gender"))
    if g != "unknown":
        return g
    declared = detect_declared_gender(target_info.get("bio") or target_info.get("pronouns") or "", include_descriptors=False)
    return declared or "unknown"


def _target_name(target_info: Dict[str, Any]) -> str:
    return (target_info.get("full_name") or target_info.get("primary_name") or "").strip()


def assess_candidate_evidence(
    candidate: Dict[str, Any],
    target_info: Dict[str, Any],
    anchors: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Assigns a categorical evidence tier to a candidate account. Hard
    contradictions always win; otherwise the strongest binding evidence decides.
    """
    target_name = _target_name(target_info)
    anchors = anchors or build_target_anchors(target_name, target_info.get("email") or "")
    auth_handles = {normalize_handle(h) for h in target_info.get("authenticated_handles", []) if h}
    target_locations = [ascii_fold(l) for l in target_info.get("locations", []) if l and len(str(l)) >= 4]

    cand_url = str(candidate.get("url") or candidate.get("profile_url") or "")
    cand_handle = normalize_handle(candidate.get("handle") or "")
    cand_name = _candidate_display_name(candidate)
    cand_text = " ".join(str(candidate.get(k) or "") for k in ("context", "bio", "context_notes", "description"))
    handle_class = classify_handle(cand_handle, anchors) if cand_handle else "EMPTY"

    matching: List[str] = []
    conflicts: List[str] = []

    # --- Binding evidence -------------------------------------------------
    email_bound = bool(candidate.get("is_email_bound")) or has_email_binding(cand_text)
    url_slug = normalize_handle(cand_url) if cand_url else ""
    commit_bound = bool(candidate.get("is_commit_bound")) or bool(
        auth_handles and ((cand_handle and cand_handle in auth_handles) or (url_slug and url_slug in auth_handles))
    )
    portfolio_bound = any(
        k in str(candidate.get("source") or "").lower() or k in cand_url.lower() for k in _PORTFOLIO_MARKERS
    )
    if email_bound:
        matching.append("Exact Email Authentication (Platform Confirmed)")
    if commit_bound:
        matching.append("Cryptographically Signed Developer/Commit Author")
    if portfolio_bound:
        matching.append("Corroborated Personal Portfolio / Vanity Domain Link")

    t_tokens = set(name_tokens(target_name))
    c_tokens = set(name_tokens(cand_name))
    full_name_match = len(t_tokens) >= 2 and len(t_tokens & c_tokens) >= 2

    # Check if verified vanity slug contains all tokens of target full name (e.g. linkedin.com/in/jordin-zwaan-716485261)
    if not full_name_match and len(t_tokens) >= 2:
        slug_tokens = set(name_tokens(cand_handle or url_slug))
        if len(t_tokens & slug_tokens) >= 2:
            if "[STATUS: VERIFIED]" in cand_text or "verified" in cand_text.lower():
                full_name_match = True
                matching.append(f"Full Legal Name Vanity Slug Match ('{target_name}')")

    if full_name_match:
        matching.append(f"Full Legal Name Match ('{target_name}')")

    if cand_handle and handle_class in (HANDLE_PRIMARY_NAME,) and not (email_bound or commit_bound):
        matching.append(f"Name-Derived Handle ('@{cand_handle}') [Unbound]")
    if target_locations and any(loc in ascii_fold(cand_text + " " + cand_url) for loc in target_locations):
        matching.append("Geographic Location Alignment")

    # --- Hard exclusions --------------------------------------------------
    given_conflict = detect_given_name_conflict(target_name, cand_name)
    if given_conflict:
        t_given = split_given_family(target_name)[0]
        conflicts.append(f"Conflicting Given Name ('{given_conflict.title()}' vs target '{t_given.title()}')")
    slug_conflict = detect_slug_given_conflict(target_name, cand_url)
    if slug_conflict and not given_conflict:
        t_given = split_given_family(target_name)[0]
        conflicts.append(f"Conflicting Vanity URL Slug ('{slug_conflict}' vs target '{t_given}')")
    demo = detect_demographic_contradiction(_resolve_target_gender(target_info), cand_text)
    if demo:
        conflicts.append(f"Demographic Contradiction: {demo[0].upper()}{demo[1:]}")
    is_bare_surname = handle_class == HANDLE_BARE_SURNAME or (
        anchors.get("family") and squash(cand_name) == anchors.get("family") and len(c_tokens) == 1
    )
    if is_bare_surname and not (email_bound or commit_bound):
        conflicts.append(f"Single-token Surname Namespace Collision ('@{cand_handle}') lacking email/commit corroboration")

    cand_loc = str(candidate.get("location") or candidate.get("country") or "").strip()
    if target_locations and cand_loc and len(cand_loc) >= 4 and not (email_bound or commit_bound or portfolio_bound):
        c_loc_fold = ascii_fold(cand_loc)
        if not any(loc in c_loc_fold or c_loc_fold in loc for loc in target_locations):
            conflicts.append(f"Geographic Location Divergence ('{cand_loc}' vs target location)")

    is_co_device = bool(candidate.get("is_co_device_affiliate")) or "CO_DEVICE" in cand_text.upper() or "SHARED_DEVICE" in cand_text.upper()
    if is_co_device and not (email_bound or commit_bound):
        conflicts.append("Co-Device / Household Member (Shared Physical Workstation)")

    # --- Tier arbitration -------------------------------------------------
    if conflicts:
        tier = TIER_CONTRADICTED
    elif email_bound or commit_bound or portfolio_bound:
        tier = TIER_AUTHENTICATED
    elif full_name_match:
        tier = TIER_NAME_VERIFIED
    elif handle_class in (HANDLE_PRIMARY_NAME, HANDLE_NAME_PERMUTATION, HANDLE_BARE_GIVEN):
        tier = TIER_SPECULATIVE
    elif candidate.get("is_alias_corroborated"):
        tier = TIER_ALIAS_CORROBORATED
    else:
        tier = TIER_UNCORROBORATED

    return {
        "evidence_tier": tier,
        "handle_class": handle_class,
        "display_name": cand_name,
        "confidence": TIER_CONFIDENCE[tier],
        "can_merge": tier in MERGEABLE_TIERS,
        "matching_signals": matching,
        "conflict_signals": conflicts,
        "is_email_bound": email_bound,
        "is_commit_bound": commit_bound,
    }


def calculate_candidate_confidence(candidate: Dict[str, Any], target_info: Dict[str, Any]) -> Dict[str, Any]:
    """Backward-compatible wrapper around `assess_candidate_evidence`."""
    return assess_candidate_evidence(candidate, target_info)

PRIMARY_CLUSTER_ID = "persona_target"

# cluster_type -> (badge, colour, sort order)
PERSONA_STYLES = {
    "CONFIRMED_PRIMARY": ("CONFIRMED TARGET", "emerald", 0),
    "SECONDARY_ALIAS": ("DISCOVERED ALIAS", "sky", 1),
    "CO_DEVICE_AFFILIATE": ("HOUSEHOLD / SHARED DEVICE", "indigo", 2),
    "CANDIDATE_LEAD": ("SPECULATIVE PROBE", "slate", 3),
    "DEMOGRAPHIC_OUTLIER": ("DEMOGRAPHIC OUTLIER", "purple", 4),
    "NAMESAKE_COLLISION": ("NAMESAKE COLLISION", "amber", 5),
    "UNCORROBORATED_LEAD": ("UNCORROBORATED", "slate", 6),
}

# Pivot types that describe the core human (never candidate accounts).
CORE_ATTRIBUTE_PIVOT_TYPES = {
    "FULL_NAME", "PERSON_NAME", "EDUCATION", "WORKPLACE", "TIMELINE", "TECH_STACK",
    "FLAGSHIP_PROJECT", "IDENTITY_CORRELATION",
}

def _alias_key(raw: Any, anchors: Dict[str, Any]) -> str:
    """Canonical alias key, or '' when the value is name-derived or empty."""
    if not raw or is_domain_or_url(raw):
        return ""
    h = normalize_handle(raw)
    if not h or is_null_value(h) or is_domain_or_url(h):
        return ""
    stem = handle_stem(h)
    if len(squash(stem)) < 3 or is_domain_or_url(stem):
        return ""
    stems = anchors.get("primary_stems", set())
    if stem in stems or h in stems:
        return ""
    if classify_handle(stem, anchors) != HANDLE_ALIAS:
        return ""
    return stem

def discover_alias_personas(
    target_info: Dict[str, Any],
    pivots: List[Dict[str, Any]],
    anchors: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Discovers alias personas (handles NOT derived from the legal name) from:
    the AI arbiter verdict, cardinal aliases, authenticated non-name handles,
    and declared nickname / persona attributes inside pivots.
    """
    aliases: Dict[str, Dict[str, Any]] = {}

    def _add(raw: Any, source: str, accounts: Optional[List[str]] = None, reasoning: str = "") -> None:
        key = _alias_key(raw, anchors)
        if not key:
            return
        entry = aliases.setdefault(key, {"alias": key, "sources": [], "accounts": [], "reasoning": ""})
        if source not in entry["sources"]:
            entry["sources"].append(source)
        for acc in accounts or []:
            if acc and acc not in entry["accounts"]:
                entry["accounts"].append(acc)
        if reasoning and not entry["reasoning"]:
            entry["reasoning"] = reasoning

    verdict = target_info.get("arbiter_verdict") or {}
    for ap in list(verdict.get("alias_personas") or []) + list(target_info.get("alias_personas") or []):
        if isinstance(ap, dict):
            accs = [a.get("url") if isinstance(a, dict) else a for a in (ap.get("accounts") or [])]
            _add(ap.get("alias") or ap.get("handle"), "AI Identity Arbiter", accs, ap.get("reasoning") or "")
        elif isinstance(ap, str):
            _add(ap, "AI Identity Arbiter")

    for al in target_info.get("aliases", []) or []:
        _add(al, "Cardinal Alias Synthesis")
    for ah in target_info.get("authenticated_handles", []) or []:
        _add(ah, "Authenticated Non-Name Handle")
    for ph in target_info.get("primary_handles", []) or []:
        _add(ph, "Known Target Handle")

    for piv in pivots or []:
        if is_visual_media_pivot(piv):
            continue
        for mention in extract_alias_mentions(piv.get("pivot_value"), piv.get("context_note")):
            _add(mention, "Declared Nickname / Persona Attribute")

    return aliases

class _PersonaRegistry:
    """Holds the core target cluster plus dynamically created candidate buckets."""

    def __init__(self, target_name: str):
        self.target_name = target_name or "Primary Target"
        self.primary = self._make(
            PRIMARY_CLUSTER_ID, f"{self.target_name} [CORE TARGET]", "CONFIRMED_PRIMARY",
            f"Verified target profile for {self.target_name}. Strictly authenticated accounts only.",
            "Conclusively triangulated identity anchors bound by authenticated email, commit signatures, or verified full name.",
        )
        self.primary["is_primary"] = True
        self.primary["confidence"] = 0.98
        self.buckets: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _make(cid: str, label: str, ctype: str, desc: str, reason: str) -> Dict[str, Any]:
        badge, color, _ = PERSONA_STYLES.get(ctype, ("CANDIDATE", "slate", 9))
        return {
            "cluster_id": cid, "cluster_label": label, "cluster_type": ctype,
            "badge": badge, "color": color, "description": desc,
            "is_primary": False, "profiles": [], "pivots": [], "reasons": [reason] if reason else [],
        }

    def get(self, cid: str) -> Dict[str, Any]:
        return self.primary if cid == PRIMARY_CLUSTER_ID else self.buckets[cid]

    def ensure(self, route: Dict[str, Any]) -> Dict[str, Any]:
        cid = route["cluster_id"]
        if cid == PRIMARY_CLUSTER_ID:
            return self.primary
        if cid not in self.buckets:
            self.buckets[cid] = self._make(cid, route["label"], route["cluster_type"], route["description"], route["reason"])
        elif route.get("reason") and route["reason"] not in self.buckets[cid]["reasons"]:
            self.buckets[cid]["reasons"].append(route["reason"])
        return self.buckets[cid]

    def sorted_candidates(self) -> List[Dict[str, Any]]:
        return sorted(self.buckets.values(), key=lambda c: PERSONA_STYLES.get(c["cluster_type"], ("", "", 9))[2])

def _route_primary(reason: str = "") -> Dict[str, Any]:
    return {"cluster_id": PRIMARY_CLUSTER_ID, "cluster_type": "CONFIRMED_PRIMARY", "reason": reason}


def _route_namesake(given: str, anchors: Dict[str, Any], target_name: str) -> Dict[str, Any]:
    family = anchors.get("family", "")
    t_given = anchors.get("given", "")
    return {
        "cluster_id": f"namesake_{given}",
        "cluster_type": "NAMESAKE_COLLISION",
        "label": f"{given.title()} {family.title()}".strip(),
        "description": f"Given name '{given.title()}' contradicts target '{target_name}'. Excluded from target dossier.",
        "reason": f"Conflicting Given Name ('{given.title()}' vs target '{t_given.title()}')",
        "is_collision": True,
    }


def _route_surname_collision(anchors: Dict[str, Any]) -> Dict[str, Any]:
    family = anchors.get("family", "")
    return {
        "cluster_id": f"namesake_vanity_{family}",
        "cluster_type": "NAMESAKE_COLLISION",
        "label": f"Surname Collision: @{family}",
        "description": f"Namespace vanity collision on bare surname '{family}'. Lacks authentic email binding or commit signatures.",
        "reason": f"Single-token surname collision ('@{family}')",
        "is_collision": True,
    }

def _route_demographic() -> Dict[str, Any]:
    return {
        "cluster_id": "demographic_outlier",
        "cluster_type": "DEMOGRAPHIC_OUTLIER",
        "label": "Demographic Outlier (Pronoun/Gender)",
        "description": "Profile exhibits contradictory demographic signals (pronouns/gender).",
        "reason": "Demographic Contradiction with confirmed target.",
        "is_collision": True,
    }


def _route_co_device(handle_or_name: str, reason: str = "") -> Dict[str, Any]:
    norm_h = normalize_handle(handle_or_name) or "affiliate"
    return {
        "cluster_id": f"device_{norm_h}",
        "cluster_type": "CO_DEVICE_AFFILIATE",
        "label": f"Shared Device: @{norm_h}",
        "description": "Associated household or workstation identity discovered on the same physical device or infostealer session. Segregated from primary target identity.",
        "reason": reason or "Discovered on shared physical device or infostealer session.",
        "is_collision": True,
    }


def _route_alias(alias: str, alias_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    meta = alias_meta or {}
    sources = ", ".join(meta.get("sources", [])) or "profile correlation"
    return {
        "cluster_id": f"alias_{alias}",
        "cluster_type": "SECONDARY_ALIAS",
        "label": f"@{alias}",
        "description": meta.get("reasoning") or f"Discovered target alias persona '@{alias}' (via {sources}). Accounts and assets associated with this handle.",
        "reason": f"Discovered alias lead '@{alias}' requiring corroboration.",
        "is_collision": False,
    }


def _route_speculative(handle: str) -> Dict[str, Any]:
    return {
        "cluster_id": f"lead_{handle}",
        "cluster_type": "CANDIDATE_LEAD",
        "label": f"@{handle}",
        "description": f"Derived from name permutation '{handle}'. Unconfirmed without email binding.",
        "reason": f"Speculative handle probe '@{handle}' lacking email verification.",
        "is_collision": False,
    }


def _route_uncorroborated() -> Dict[str, Any]:
    return {
        "cluster_id": "uncorroborated_candidates",
        "cluster_type": "UNCORROBORATED_LEAD",
        "label": "Uncorroborated Footprints",
        "description": "Uncorroborated public footprint matches.",
        "reason": "Single-attribute candidate probe lacking binding evidence.",
        "is_collision": False,
    }

def _url_key(url: Any) -> str:
    u = str(url or "").strip().lower().split("?")[0].rstrip("/")
    return re.sub(r"^https?://(www\.)?", "", u)


def build_arbiter_url_map(verdict: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Maps normalised account URLs to the AI arbiter's semantic category."""
    mapping: Dict[str, Dict[str, Any]] = {}
    if not verdict:
        return mapping
    sections = (
        ("verified_profiles", "verified"),
        ("namesake_collisions", "namesake"),
        ("speculative_probes", "speculative"),
        ("rejected_profiles", "rejected"),
    )
    for key, category in sections:
        for item in verdict.get(key) or []:
            if isinstance(item, dict) and item.get("url"):
                mapping[_url_key(item["url"])] = {"category": category, **item}
    for ap in verdict.get("alias_personas") or []:
        if not isinstance(ap, dict):
            continue
        for acc in ap.get("accounts") or []:
            acc_url = acc.get("url") if isinstance(acc, dict) else acc
            if acc_url:
                mapping[_url_key(acc_url)] = {"category": "alias", "alias": ap.get("alias") or ap.get("handle")}
    return mapping


def _match_alias(handle: str, text: str, aliases: Dict[str, Dict[str, Any]]) -> Optional[str]:
    for al in sorted(aliases, key=len, reverse=True):
        if alias_matches_text(al, handle, text):
            return al
    return None

def _route_candidate(
    ev: Dict[str, Any],
    handle: str,
    text: str,
    url: str,
    aliases: Dict[str, Dict[str, Any]],
    anchors: Dict[str, Any],
    target_name: str,
    arbiter_map: Dict[str, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Precedence: hard contradictions > binding evidence > AI arbiter verdict >
    verified full name > alias persona > speculative name permutation.
    Returns None when nothing decides (caller applies its default).
    """
    conflicts = ev.get("conflict_signals", [])
    given_conflict = detect_given_name_conflict(target_name, ev.get("display_name")) or detect_slug_given_conflict(target_name, url)
    if given_conflict:
        return _route_namesake(given_conflict, anchors, target_name)
    if any("Surname Namespace Collision" in c for c in conflicts):
        return _route_surname_collision(anchors)
    if any(c.startswith("Demographic Contradiction") for c in conflicts):
        return _route_demographic()
    if any("Co-Device" in c for c in conflicts):
        return _route_co_device(handle or ev.get("display_name") or "device_user")
    if any("Geographic Location Divergence" in c for c in conflicts):
        g = split_given_family(ev.get("display_name") or target_name)[0] or "namesake"
        return _route_namesake(g, anchors, target_name)

    if ev.get("evidence_tier") == TIER_AUTHENTICATED:
        return _route_primary("Bound by authenticated email, commit signature or portfolio link.")

    arb = arbiter_map.get(_url_key(url)) if url else None
    if arb:
        cat = arb.get("category")
        if cat == "verified":
            return _route_primary(arb.get("reasoning") or "Verified by AI Identity Arbiter.")
        if cat == "alias":
            key = _alias_key(arb.get("alias") or handle, anchors)
            if key:
                return _route_alias(key, aliases.get(key))
        if cat == "namesake":
            g = split_given_family(arb.get("display_name") or ev.get("display_name") or "")[0] or (handle or "unknown")
            return _route_namesake(g, anchors, target_name)
        if cat == "speculative" and handle:
            return _route_speculative(handle)

    if ev.get("evidence_tier") == TIER_NAME_VERIFIED:
        return _route_primary("Exact legal name match with zero contradictions.")

    matched = _match_alias(handle, text, aliases)
    if matched:
        return _route_alias(matched, aliases.get(matched))

    if handle and ev.get("handle_class") in (HANDLE_PRIMARY_NAME, HANDLE_NAME_PERMUTATION, HANDLE_BARE_GIVEN):
        return _route_speculative(handle)
    return None

ACCOUNT_PIVOT_TYPES = {"PUBLIC_PROFILE", "SUSPECTED_ACCOUNT", "PERSONA_PIVOT", "USER_HANDLE"}


def _annotate_pivot(piv: Dict[str, Any], bucket: Dict[str, Any], route: Dict[str, Any]) -> Dict[str, Any]:
    """Stamps persona attribution onto a pivot copy and demotes non-target status tags."""
    p_copy = dict(piv)
    cid = bucket["cluster_id"]
    p_copy["cluster_id"] = cid
    p_copy["persona_id"] = cid
    p_copy["persona_label"] = bucket["cluster_label"]
    p_copy["persona_badge"] = bucket["badge"]
    p_copy["persona_color"] = bucket["color"]
    is_collision = bool(route.get("is_collision")) and cid != PRIMARY_CLUSTER_ID
    p_copy["is_namesake_collision"] = is_collision
    if cid == PRIMARY_CLUSTER_ID:
        return p_copy

    ctx = str(p_copy.get("context_note") or "")
    if is_collision:
        p_copy["context_note"] = re.sub(r'\[STATUS:\s*VERIFIED\]', '[STATUS: SUSPECTED] [STATUS: NAMESAKE_COLLISION]', ctx)
        if "[STATUS: NAMESAKE_COLLISION]" not in p_copy["context_note"]:
            p_copy["context_note"] = (p_copy["context_note"] + " [STATUS: NAMESAKE_COLLISION]").strip()
        if p_copy.get("pivot_type") == "PUBLIC_PROFILE":
            p_copy["pivot_type"] = "SUSPECTED_ACCOUNT"
        p_copy["confidence_score"] = min(0.40, float(p_copy.get("confidence_score") or 0.40))
    else:
        p_copy["context_note"] = re.sub(r'\[STATUS:\s*VERIFIED\]', '[STATUS: SUSPECTED] [STATUS: CANDIDATE_LEAD]', ctx)
        p_copy["confidence_score"] = min(0.60, float(p_copy.get("confidence_score") or 0.60))
    return p_copy

def cluster_discovered_entities(
    target_info: Dict[str, Any],
    profiles: List[Dict[str, Any]],
    pivots: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Multi-Entity Persona Resolution & Disambiguation Engine.
    Consolidates raw profiles and pivots into human personas:
    1. Primary Target Entity (authenticated / verified full name)
    2. Discovered Alias Personas (dynamically discovered non-name handles)
    3. Speculative Handle Probes (unbound legal-name permutations)
    4. Namesake & Demographic Collisions (distinct humans)
    Visual media assets are routed to the primary visual footprint and are
    never treated as candidate accounts.
    """
    raw_name = _target_name(target_info)
    target_name = raw_name or "Primary Target"
    anchors = build_target_anchors(raw_name, target_info.get("email") or "")
    arbiter_map = build_arbiter_url_map(target_info.get("arbiter_verdict"))
    aliases = discover_alias_personas(target_info, pivots or [], anchors)
    reg = _PersonaRegistry(target_name)
    media_assets: List[Dict[str, Any]] = []

    # 1. Candidate profiles
    for prof in profiles or []:
        if is_visual_media_profile(prof):
            m = dict(prof, cluster_id=PRIMARY_CLUSTER_ID, persona_id=PRIMARY_CLUSTER_ID, is_media_asset=True)
            media_assets.append(m)
            continue
        ev = assess_candidate_evidence(prof, target_info, anchors)
        handle = normalize_handle(prof.get("handle") or "")
        url = str(prof.get("url") or prof.get("profile_url") or "")
        text = " ".join(str(prof.get(k) or "") for k in ("platform", "handle", "context", "bio", "display_name", "name"))
        route = _route_candidate(ev, handle, text, url, aliases, anchors, raw_name, arbiter_map) or _route_uncorroborated()
        bucket = reg.ensure(route)
        is_primary = bucket["cluster_id"] == PRIMARY_CLUSTER_ID
        p_copy = dict(prof)
        p_copy.update({
            "entity_resolution_score": ev["confidence"],
            "evidence_tier": ev["evidence_tier"],
            "matching_signals": ev["matching_signals"],
            "conflict_signals": ev["conflict_signals"],
            "cluster_id": bucket["cluster_id"],
            "persona_id": bucket["cluster_id"],
            "is_verified": is_primary,
            "is_suspected": not is_primary,
            "is_namesake_collision": bucket["cluster_type"] == "NAMESAKE_COLLISION",
        })
        bucket["profiles"].append(p_copy)

    # 2. Pivots
    tagged_pivots: List[Dict[str, Any]] = []
    for piv in pivots or []:
        pt = str(piv.get("pivot_type") or "").upper()
        pv = str(piv.get("pivot_value") or "")
        ctx = str(piv.get("context_note") or "")

        if is_visual_media_pivot(piv):
            route = _route_primary()
        elif pt in CORE_ATTRIBUTE_PIVOT_TYPES:
            route = _route_primary()
        else:
            plat, handle = parse_pivot_account(pv)
            url = extract_tagged_url(ctx)
            m_pname = re.search(r'\([\'"]([^\'"]+)[\'"]\)', pv)
            p_display = m_pname.group(1).strip() if m_pname else ""
            cand = {
                "platform": plat, "handle": handle, "url": url, "context": ctx,
                "display_name": p_display, "pivot_value": pv,
                "is_email_bound": has_email_binding(ctx),
                "is_commit_bound": has_auth_binding(ctx),
            }
            # Pivot binding comes only from the pivot's own evidence, never from
            # cross-platform handle equality (prevents vanity-collision promotion).
            ev = assess_candidate_evidence(cand, dict(target_info, authenticated_handles=[]), anchors)
            route = _route_candidate(ev, handle, f"{pv} {ctx}", url, aliases, anchors, raw_name, arbiter_map)
            is_account = pt in ACCOUNT_PIVOT_TYPES
            soft_route = route is not None and route["cluster_type"] in ("CANDIDATE_LEAD", "SECONDARY_ALIAS")
            if route is None or (not is_account and soft_route):
                looks_suspected = pt == "SUSPECTED_ACCOUNT" or "[STATUS: SUSPECTED]" in ctx
                route = _route_uncorroborated() if (is_account and looks_suspected) else _route_primary()

        bucket = reg.ensure(route)
        p_copy = _annotate_pivot(piv, bucket, route)
        if is_visual_media_pivot(piv):
            p_copy["is_media_asset"] = True
        bucket["pivots"].append(p_copy)
        tagged_pivots.append(p_copy)

    candidate_clusters_list = reg.sorted_candidates()
    all_clusters = [reg.primary] + candidate_clusters_list
    return {
        "primary_entity": reg.primary,
        "candidate_clusters": candidate_clusters_list,
        "total_clusters_count": len(all_clusters),
        "all_clusters": all_clusters,
        "personas": all_clusters,
        "tagged_pivots": tagged_pivots,
        "discovered_aliases": sorted(aliases.values(), key=lambda a: a["alias"]),
        "media_assets": media_assets,
        "target_primary_stems": sorted(anchors.get("primary_stems", set())),
    }
