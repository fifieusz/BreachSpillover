"""
BreachSpillover - Multilingual Onomastic Deconstruction & Temporal Engine
High-precision target-agnostic unpunctuated handle deconstruction, compound name splitting,
birth-year/age cohort extraction, and namesake collision risk quantification.

Addresses the de-anonymization challenge when investigating opaque or unpunctuated
webmail handles (e.g. 'islamzerdab', 'hakimazer1974', 'hakima1974', 'jandevries', 'aljewoltjer')
by deconstructing them into onomastic hypotheses and extracting temporal markers.
Strictly authentic OSINT: zero synthetic generation, zero emojis, resilient offline operation.
"""

import re
import datetime
from typing import Dict, Any, List, Optional, Tuple, Set

# Current reference year for age estimation
CURRENT_YEAR = 2026

# High-frequency global given names across linguistic / cultural families
# Used purely for morphological boundary detection in unpunctuated handles
GLOBAL_GIVEN_NAMES: Dict[str, Dict[str, Any]] = {
    # Arabic / North African / Middle Eastern
    "islam": {"gender": "male", "culture": "Arabic / North African"},
    "hakim": {"gender": "male", "culture": "Arabic / North African"},
    "hakima": {"gender": "female", "culture": "Arabic / North African"},
    "karim": {"gender": "male", "culture": "Arabic / North African"},
    "karima": {"gender": "female", "culture": "Arabic / North African"},
    "tariq": {"gender": "male", "culture": "Arabic / North African"},
    "samir": {"gender": "male", "culture": "Arabic / North African"},
    "samira": {"gender": "female", "culture": "Arabic / North African"},
    "omar": {"gender": "male", "culture": "Arabic / Middle Eastern"},
    "ali": {"gender": "male", "culture": "Arabic / Middle Eastern"},
    "youssef": {"gender": "male", "culture": "Arabic / North African"},
    "yousef": {"gender": "male", "culture": "Arabic / Middle Eastern"},
    "ahmed": {"gender": "male", "culture": "Arabic / North African"},
    "ahmad": {"gender": "male", "culture": "Arabic / Middle Eastern"},
    "mohamed": {"gender": "male", "culture": "Arabic / North African"},
    "mohammed": {"gender": "male", "culture": "Arabic / Middle Eastern"},
    "mustafa": {"gender": "male", "culture": "Arabic / Turkish"},
    "rachid": {"gender": "male", "culture": "North African / Berber"},
    "mourad": {"gender": "male", "culture": "Arabic / North African"},
    "nabil": {"gender": "male", "culture": "Arabic / North African"},
    "sofiane": {"gender": "male", "culture": "North African / Algerian"},
    "soufiane": {"gender": "male", "culture": "North African / Moroccan"},
    "amine": {"gender": "male", "culture": "Arabic / North African"},
    "djessir": {"gender": "male", "culture": "North African / Berber"},
    "farid": {"gender": "male", "culture": "Arabic / North African"},
    "fatima": {"gender": "female", "culture": "Arabic / North African"},
    "leila": {"gender": "female", "culture": "Arabic / North African"},
    "yasmina": {"gender": "female", "culture": "Arabic / North African"},
    "amina": {"gender": "female", "culture": "Arabic / North African"},
    "meriem": {"gender": "female", "culture": "North African"},
    "salima": {"gender": "female", "culture": "Arabic / North African"},

    # Dutch / Flemish / Frisian
    "jan": {"gender": "male", "culture": "Dutch / Germanic"},
    "alje": {"gender": "male", "culture": "Dutch / Frisian"},
    "pieter": {"gender": "male", "culture": "Dutch"},
    "klaas": {"gender": "male", "culture": "Dutch"},
    "willem": {"gender": "male", "culture": "Dutch"},
    "hendrik": {"gender": "male", "culture": "Dutch"},
    "maarten": {"gender": "male", "culture": "Dutch"},
    "thijs": {"gender": "male", "culture": "Dutch"},
    "lars": {"gender": "male", "culture": "Scandinavian / Dutch"},
    "sander": {"gender": "male", "culture": "Dutch"},
    "femke": {"gender": "female", "culture": "Dutch / Frisian"},
    "anke": {"gender": "female", "culture": "Dutch"},
    "sanne": {"gender": "female", "culture": "Dutch"},
    "jordan": {"gender": "male", "culture": "English / European"},

    # Polish / Slavic
    "filip": {"gender": "male", "culture": "Polish / Slavic"},
    "piotr": {"gender": "male", "culture": "Polish / Slavic"},
    "pawel": {"gender": "male", "culture": "Polish / Slavic"},
    "tomasz": {"gender": "male", "culture": "Polish / Slavic"},
    "michal": {"gender": "male", "culture": "Polish / Slavic"},
    "krzysztof": {"gender": "male", "culture": "Polish / Slavic"},
    "marcin": {"gender": "male", "culture": "Polish / Slavic"},
    "jakub": {"gender": "male", "culture": "Polish / Slavic"},
    "kamil": {"gender": "male", "culture": "Polish / Slavic"},
    "anna": {"gender": "female", "culture": "Polish / European"},
    "katarzyna": {"gender": "female", "culture": "Polish / Slavic"},
    "agnieszka": {"gender": "female", "culture": "Polish / Slavic"},
    "magdalena": {"gender": "female", "culture": "Polish / Slavic"},

    # Germanic / Scandinavian
    "alex": {"gender": "unknown", "culture": "Pan-European"},
    "alexander": {"gender": "male", "culture": "Pan-European"},
    "johann": {"gender": "male", "culture": "Germanic"},
    "stefan": {"gender": "male", "culture": "Germanic / Slavic"},
    "lukas": {"gender": "male", "culture": "Germanic / Slavic"},
    "erik": {"gender": "male", "culture": "Scandinavian / Germanic"},
    "magnus": {"gender": "male", "culture": "Scandinavian"},
    "henrik": {"gender": "male", "culture": "Scandinavian"},

    # Romance / French / Spanish / Italian
    "jean": {"gender": "male", "culture": "French"},
    "pierre": {"gender": "male", "culture": "French"},
    "lucas": {"gender": "male", "culture": "French / Spanish"},
    "antoine": {"gender": "male", "culture": "French"},
    "carlos": {"gender": "male", "culture": "Spanish / Portuguese"},
    "marco": {"gender": "male", "culture": "Italian / Spanish"},
    "david": {"gender": "male", "culture": "Pan-European / Biblical"},
    "daniel": {"gender": "male", "culture": "Pan-European / Biblical"},
}

# Known patronymic / toponymic name particles
NAME_PARTICLES: Set[str] = {
    "van", "de", "der", "den", "ter", "ten", "von", "zu",
    "bin", "ben", "al", "el", "fitz", "mc", "mac", "o"
}

# Gamer / online pseudonym vocabulary tokens that indicate an alias, not a personal name
PSEUDO_STEM_WORDS: Set[str] = {
    "mister", "boss", "admin", "gamer", "pro", "dark", "shadow", "cyber",
    "phantom", "ninja", "hacker", "ghost", "master", "dragon", "knight",
    "sniper", "killer", "player", "stealth", "beast", "demon", "warrior",
    "god", "king", "lord", "zero", "void", "snipe", "rush", "viper", "toxic"
}

# High-frequency global surnames across linguistic families
GLOBAL_FAMILY_SURNAMES: Set[str] = {
    # Arabic / North African / Middle Eastern
    "azer", "azar", "zerdab", "khelil", "bensaid", "mansouri", "saidi", "boussaid",
    "belkacem", "brahim", "amrani", "hadj", "bouzid", "cherif", "daoud", "slimani",
    "touati", "zitouni", "hamdi", "benaissa", "zerrouki", "meddah", "bouazza", "benali",
    "abbasi", "rahmani", "kaddour", "allali", "madani", "mekki", "zaidi", "yahiaoui",
    # European / Slavic / Dutch
    "woltjer", "kowalski", "niewiadomski", "novak", "jansen", "bakker", "smit",
    "mueller", "schmidt", "schneider", "fischer", "weber", "meyer", "wagner",
    "becker", "schulz", "hoffmann", "koch", "richter", "klein", "wolf", "schroeder"
}

def extract_handle_temporal_anchor(handle: str) -> Dict[str, Any]:
    """
    Extracts 4-digit and 2-digit birth-year suffixes from an email localpart or handle.
    Calculates estimated age cohort based on reference year 2026.
    
    Example:
    'hakimazer1974' -> birth_year=1974, estimated_age=52, clean_stem='hakimazer'
    'hakima1974'    -> birth_year=1974, estimated_age=52, clean_stem='hakima'
    'filipos91'     -> birth_year=1991, estimated_age=35, clean_stem='filipos'
    'xmister795'    -> birth_year=None, clean_stem='xmister'
    """
    raw = (handle or "").strip().lower()
    local = raw.split("@")[0] if "@" in raw else raw

    # 1. Check for 4-digit birth year at end (1930 - 2015)
    m4 = re.search(r'(19[3-9]\d|200\d|201[0-5])$', local)
    if m4:
        byear = int(m4.group(1))
        stem = local[:m4.start()].strip(" .-_+")
        return {
            "has_birth_year": True,
            "birth_year": byear,
            "estimated_age": CURRENT_YEAR - byear,
            "year_format": "YYYY",
            "confidence": "HIGH",
            "is_speculative": False,
            "clean_stem": stem or local,
            "raw_handle": raw
        }

    # 2. Check for 2-digit year at end (e.g. 50-99 -> 1950-1999, 00-15 -> 2000-2015)
    # Require stem of length >= 3 to avoid clipping short handles
    m2 = re.search(r'([3-9]\d|0\d|1[0-5])$', local)
    if m2 and len(local[:m2.start()].strip(" .-_+")) >= 3:
        yy = int(m2.group(1))
        stem = local[:m2.start()].strip(" .-_+")

        # Multi-number check: if the preceding stem still contains digits (e.g. "123" in "filipos123.91"),
        # or if the handle contains multiple numeric groups, it represents an arbitrary number/PIN/sequence, NOT a birth year!
        if re.search(r'\d', stem):
            stem_clean = re.sub(r'\d+$', '', stem).strip(" .-_+")
            return {
                "has_birth_year": False,
                "birth_year": None,
                "estimated_age": None,
                "year_format": None,
                "confidence": "NONE",
                "clean_stem": stem_clean or local,
                "raw_handle": raw,
                "is_arbitrary_numeric": True
            }

        # Exclude typical number patterns like 00, 01, 07 if handle looks like gamer tag
        byear = 1900 + yy if yy >= 30 else 2000 + yy
        # Avoid treating random gamer numbers like 99, 77 as birth years if stem has pseudo words
        if not any(pw in stem for pw in PSEUDO_STEM_WORDS):
            return {
                "has_birth_year": True,
                "birth_year": byear,
                "estimated_age": CURRENT_YEAR - byear,
                "year_format": "YY",
                "confidence": "SPECULATIVE",
                "is_speculative": True,
                "clean_stem": stem or local,
                "raw_handle": raw
            }

    # Fallback: strip any trailing digits
    stem_no_digits = re.sub(r'\d+$', '', local).strip(" .-_+")
    return {
        "has_birth_year": False,
        "birth_year": None,
        "estimated_age": None,
        "year_format": None,
        "clean_stem": stem_no_digits or local,
        "raw_handle": raw
    }


def deconstruct_onomastic_handle(
    handle: str,
    target_name_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deconstructs an unpunctuated handle into given name and family surname components.
    
    Examples:
    - 'islamzerdab@gmail.com' -> Given: 'Islam', Family: 'Zerdab', Full: 'Islam Zerdab'
    - 'hakimazer1974@gmail.com' -> Given: 'Hakim', Family: 'Azer', Full: 'Hakim Azer', Year: 1974
    - 'hakima1974@gmail.com' -> Given: 'Hakima', Family: None, Full: 'Hakima', Year: 1974
    - 'jandevries@gmail.com' -> Given: 'Jan', Family: 'de Vries', Full: 'Jan de Vries'
    - 'xmister795@gmail.com' -> Pseudonym: 'Xmister795', Full: 'Xmister795', is_pseudonym=True
    """
    clean_h = (handle or "").strip().lower()
    local = clean_h.split("@")[0] if "@" in clean_h else clean_h

    # Extract temporal anchor (birth year)
    temporal = extract_handle_temporal_anchor(local)
    clean_stem = temporal["clean_stem"]

    # 1. Punctuation split: if handle has delimiters (dots, underscores, hyphens)
    parts = [p for p in re.split(r'[._\-+]+', clean_stem) if len(p) >= 2]
    if len(parts) >= 2 and all(p.isalpha() for p in parts):
        given = parts[0].capitalize()
        family = " ".join(p.capitalize() for p in parts[1:])
        full = f"{given} {family}"
        return _build_onomastic_result(
            given=given,
            family=family,
            full=full,
            is_pseudo=False,
            temporal=temporal,
            culture_hint=_infer_culture(given.lower(), family.lower()),
            method="DELIMITED_SPLIT"
        )

    # 2. Check for Dutch/German particles (e.g. 'jandevries' -> 'Jan de Vries', 'aljewoltjer' -> 'Alje Woltjer')
    low_stem = clean_stem.lower()
    for part in ["devries", "vander", "vande", "vanden", "van", "de"]:
        if part in low_stem:
            idx = low_stem.find(part)
            before = low_stem[:idx]
            after = low_stem[idx + len(part):]
            if idx >= 2 and (len(after) >= 3 or part in ["devries"]):
                # Avoid false-positive particle matching on Slavic/French roots (e.g. 'ivan', 'sylvan')
                if part == "van" and (before.endswith("i") or before.endswith("syl")):
                    continue
                given = before.capitalize()
                if part == "devries":
                    family = "de Vries"
                else:
                    family = f"{part} {after.capitalize()}".strip()
                full = f"{given} {family}"
                return _build_onomastic_result(
                    given=given,
                    family=family,
                    full=full,
                    is_pseudo=False,
                    temporal=temporal,
                    culture_hint="Dutch / Flemish",
                    method="PARTICLE_SPLIT"
                )

    # 3. Check for Gamer / Online Pseudonym markers
    if any(pw in low_stem for pw in PSEUDO_STEM_WORDS) or (low_stem.startswith("x") and len(low_stem) >= 4 and any(pw in low_stem[1:] for pw in PSEUDO_STEM_WORDS)):
        return _build_onomastic_result(
            given=None,
            family=None,
            full=clean_stem.capitalize(),
            is_pseudo=True,
            temporal=temporal,
            culture_hint=None,
            method="PSEUDONYM_DETECTED"
        )

    # 4. Unpunctuated Morphological Given Name Search
    # Gather all valid given name + surname candidate splits and score them
    candidate_splits = []
    for name_len in range(3, min(12, len(low_stem)) + 1):
        cand_g = low_stem[:name_len]
        cand_s = low_stem[name_len:]

        if cand_g in GLOBAL_GIVEN_NAMES:
            given_meta = GLOBAL_GIVEN_NAMES[cand_g]
            # Case 4a: Exact match of entire stem is a single given name (e.g. 'hakima')
            if not cand_s:
                candidate_splits.append({
                    "score": 100,
                    "given": cand_g.capitalize(),
                    "family": None,
                    "full": cand_g.capitalize(),
                    "culture": given_meta.get("culture"),
                    "gender": given_meta.get("gender"),
                    "method": "SINGLE_GIVEN_NAME"
                })
            elif len(cand_s) >= 3 and cand_s.isalpha():
                vowels = sum(1 for c in cand_s if c in "aeiouy")
                if vowels >= 1:
                    score = 50
                    # Bonus if the surname is in known surnames catalog
                    if cand_s in GLOBAL_FAMILY_SURNAMES:
                        score += 50
                    # Bonus for standard surname length (4-10 characters)
                    if 4 <= len(cand_s) <= 8:
                        score += 15
                    # If surname starts with vowel following given name ending in consonant (e.g. hakim + azer)
                    if cand_g[-1] not in "aeiou" and cand_s[0] in "aeiou":
                        score += 10
                    # Slight penalty for very short 3-letter surnames unless known
                    if len(cand_s) == 3 and cand_s not in GLOBAL_FAMILY_SURNAMES:
                        score -= 20

                    candidate_splits.append({
                        "score": score,
                        "given": cand_g.capitalize(),
                        "family": cand_s.capitalize(),
                        "full": f"{cand_g.capitalize()} {cand_s.capitalize()}",
                        "culture": given_meta.get("culture"),
                        "gender": given_meta.get("gender"),
                        "method": "COMPOUND_ONOMASTIC_SPLIT"
                    })

    if candidate_splits:
        # Sort by score descending; if tied, prefer known family surname, then longer surname
        candidate_splits.sort(
            key=lambda x: (
                x["score"],
                1 if (x.get("family") or "").lower() in GLOBAL_FAMILY_SURNAMES else 0,
                len(x.get("family") or "")
            ),
            reverse=True
        )
        best = candidate_splits[0]
        return _build_onomastic_result(
            given=best["given"],
            family=best["family"],
            full=best["full"],
            is_pseudo=False,
            temporal=temporal,
            culture_hint=best.get("culture"),
            perceived_gender=best.get("gender"),
            method=best["method"]
        )

    # 5. Check if target_name_hint provides corroboration for splitting
    if target_name_hint and target_name_hint.strip() and " " in target_name_hint.strip():
        parts_h = [p.capitalize() for p in target_name_hint.split() if len(p) >= 2]
        if len(parts_h) >= 2:
            return _build_onomastic_result(
                given=parts_h[0],
                family=" ".join(parts_h[1:]),
                full=f"{parts_h[0]} {' '.join(parts_h[1:])}",
                is_pseudo=False,
                temporal=temporal,
                culture_hint=_infer_culture(parts_h[0].lower(), parts_h[-1].lower()),
                method="INVESTIGATOR_ANCHOR_MATCH"
            )

    # Fallback: Treat as moniker or handle
    is_short = len(clean_stem) < 4
    return _build_onomastic_result(
        given=clean_stem.capitalize() if not is_short else None,
        family=None,
        full=clean_stem.capitalize() if clean_stem else "Target User",
        is_pseudo=is_short,
        temporal=temporal,
        culture_hint=None,
        method="FALLBACK_MONIKER"
    )


def _infer_culture(given: str, family: str) -> Optional[str]:
    """Infers cultural / linguistic origin from given and family tokens."""
    if given in GLOBAL_GIVEN_NAMES:
        return GLOBAL_GIVEN_NAMES[given].get("culture")
    if any(dp in family for dp in ["van", "de", "der", "vries"]):
        return "Dutch / Flemish"
    if family.endswith(("ski", "ska", "wicz", "ak", "ek", "yk")):
        return "Polish / Slavic"
    if family.endswith(("ov", "ova", "ev", "in")):
        return "Slavic / Eastern European"
    if family.endswith(("ez", "es")):
        return "Hispanic / Iberian"
    return None


def _build_onomastic_result(
    given: Optional[str],
    family: Optional[str],
    full: str,
    is_pseudo: bool,
    temporal: Dict[str, Any],
    culture_hint: Optional[str] = None,
    perceived_gender: Optional[str] = None,
    method: str = "OFFLINE_HEURISTIC"
) -> Dict[str, Any]:
    """Builds a standardized structured onomastic intelligence record."""
    clean_stem = temporal.get("clean_stem", "")
    byear = temporal.get("birth_year")
    age = temporal.get("estimated_age")

    candidate_handles = []
    if given and family:
        g_low = given.lower()
        f_low = family.lower().replace(" ", "")
        candidate_handles.extend([
            f"{g_low}{f_low}",
            f"{g_low}.{f_low}",
            f"{g_low}_{f_low}",
            f"{f_low}{g_low}",
            f"{g_low[0]}{f_low}",
            f"{g_low[0]}.{f_low}",
            f"{f_low}_{g_low}",
        ])
        if byear:
            candidate_handles.extend([
                f"{g_low}{f_low}{byear}",
                f"{g_low}{byear}",
                f"{f_low}{byear}"
            ])
    elif given:
        g_low = given.lower()
        candidate_handles.append(g_low)
        if byear:
            candidate_handles.append(f"{g_low}{byear}")

    if clean_stem and clean_stem not in candidate_handles:
        candidate_handles.append(clean_stem)
    raw_h = temporal.get("raw_handle", "").split("@")[0]
    if raw_h and raw_h not in candidate_handles:
        candidate_handles.insert(0, raw_h)

    # Search dorks tailored to decomposed entity
    search_dorks = []
    if not is_pseudo and given and family:
        search_dorks.extend([
            f'"{full}"',
            f'"{full}" linkedin',
            f'"{full}" ("algeria" OR "france" OR "morocco" OR "tunisia")' if "North African" in (culture_hint or "") else f'"{full}" facebook',
            f'site:linkedin.com/in "{full}"'
        ])
    elif not is_pseudo and given:
        search_dorks.extend([
            f'"{given}" "{temporal.get("raw_handle")}"',
            f'"{temporal.get("raw_handle")}"'
        ])
    else:
        search_dorks.extend([
            f'"{temporal.get("raw_handle")}"',
            f'"{clean_stem}" site:github.com OR site:pastebin.com',
            f'"{clean_stem}" ("my name is" OR "call me" OR "email" OR "discord")'
        ])

    return {
        "is_onomastic_compound": bool(given and family),
        "given_name": given,
        "family_name": family,
        "full_name": full,
        "birth_year": byear,
        "estimated_age": age,
        "perceived_gender": perceived_gender or ("female" if given and given.lower().endswith("a") and given.lower() in GLOBAL_GIVEN_NAMES and GLOBAL_GIVEN_NAMES[given.lower()]["gender"] == "female" else ("male" if given and given.lower() in GLOBAL_GIVEN_NAMES and GLOBAL_GIVEN_NAMES[given.lower()]["gender"] == "male" else "unknown")),
        "culture_hint": culture_hint,
        "is_pseudonym": is_pseudo,
        "primary_handle": clean_stem,
        "candidate_usernames": list(dict.fromkeys(candidate_handles)),
        "search_dorks": search_dorks,
        "decomposition_method": method
    }


def estimate_namesake_collision_risk(
    full_name: str,
    culture_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates the probability that distinct humans share this exact full name.
    
    Provides explicit investigative guidance for segregating candidate profiles
    into the Namesake Quarantine Ledger rather than merging them into the target dossier.
    """
    name_clean = (full_name or "").strip()
    tokens = [t.lower() for t in name_clean.split() if len(t) >= 2]

    if len(tokens) < 2:
        return {
            "risk_tier": "EXTREME_COLLISION",
            "collision_score": 0.95,
            "requires_strict_disambiguation": True,
            "reason": "Single name token or moniker. High global namespace collisions."
        }

    first, last = tokens[0], tokens[-1]
    
    # Ultra-common given names
    common_firsts = {"mohamed", "mohammed", "ahmed", "ali", "john", "david", "jan", "alex", "michael"}
    # Ultra-common surnames
    common_lasts = {"smith", "ali", "khan", "jansen", "kowalski", "garcia", "martinez", "de jong"}

    is_common_first = first in common_firsts
    is_common_last = last in common_lasts

    if is_common_first and is_common_last:
        risk = "CRITICAL_COLLISION"
        score = 0.90
        reason = f"Both given name '{first.capitalize()}' and surname '{last.capitalize()}' are high-frequency global names. Dozens of distinct individuals share this exact name."
    elif is_common_first or is_common_last:
        risk = "HIGH_COLLISION"
        score = 0.65
        reason = f"Name contains high-frequency token ('{first.capitalize() if is_common_first else last.capitalize()}'). Strict email or location corroboration required before attribution."
    else:
        risk = "MODERATE_DISTINCTIVE"
        score = 0.35
        reason = f"Compound name '{name_clean}' exhibits distinctive onomastic combination. Moderate uniqueness globally."

    return {
        "risk_tier": risk,
        "collision_score": score,
        "requires_strict_disambiguation": score >= 0.50,
        "reason": reason,
        "disambiguation_guidance": (
            "Profiles found matching this name that lack verified email binding or identical cryptographic keys "
            "must be segregated into the Namesake Candidates ledger (tab-suspected) to prevent false-positive contamination."
        )
    }
