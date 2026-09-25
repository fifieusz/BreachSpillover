"""
BreachSpillover - AI Target Identity & Entity Decomposer
High-speed multilingual identity decomposition via Groq (Qwen 27B / Llama 3.3)
with intelligent offline heuristic fallback.

Decomposes raw email addresses or handles into:
- Real given names, middle names, and family surnames
- Distinction between personal names and online pseudonyms/handles
- Probable country & language of origin (for localized search dorking)
- Candidate handle permutations for multi-platform enumeration
"""

import re
import json
from typing import Dict, Any, List, Optional

from backend.ai_engine import call_groq_api, resolve_api_key, load_dotenv

# In-memory session cache for fast multi-pass decomposition
_DECOMPOSER_CACHE: Dict[str, Dict[str, Any]] = {}

def decompose_target_identity(
    email: str,
    raw_name: Optional[str] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Analyzes an email address and returns structured identity intelligence:
    full_name, first_name, last_name, is_pseudonym, country_hint, language_hint,
    candidate_usernames, and search_dorks.
    """
    clean_email = (email or "").strip().lower()
    cache_key = clean_email or (raw_name or "").strip().lower()
    if not cache_key:
        return _build_fallback_result("Target User", "target", False)

    if not force_refresh and cache_key in _DECOMPOSER_CACHE:
        return _DECOMPOSER_CACHE[cache_key]

    local_part = clean_email.split("@")[0] if "@" in clean_email else clean_email
    domain = clean_email.split("@")[1] if "@" in clean_email else "gmail.com"

    # Attempt AI decomposition via Groq
    api_key = resolve_api_key("groq")
    if api_key:
        try:
            prompt = f"""Analyze the target email: '{clean_email}' (local_part: '{local_part}', domain: '{domain}', raw_name: '{raw_name or ""}').
Determine:
1. Is this a real person's legal name or an online pseudonym/handle/alias? (e.g. 'jordanvance88' -> real name 'Jordan Vance', 'shadowwolf99' -> pseudonym/alias 'Shadowwolf').
2. If real name, split into first_name, middle_name (if any), and last_name with proper capitalization.
3. If pseudonym/alias, set is_pseudonym=true, full_name to the clean title-cased handle, first_name to null, last_name to null, and primary_handle to root stem.
4. Probable country and language of origin based on onomastic/linguistic origin (e.g. Woltjer -> Netherlands, Dutch; Dupont -> France, French; Kowalski -> Poland, Polish).
5. If domain is a company/workplace (e.g. 'vooruit.nl' -> 'Vooruit', 'cybercorp.io' -> 'Cybercorp'), extract organization name; if generic webmail (gmail/yahoo/outlook/proton), set to null.
6. Generate 6-8 natural username permutations. IMPORTANT: If a real human name is identified, ALWAYS include standalone first_name (e.g. 'alje') and standalone last_name (e.g. 'woltjer') as candidate handles for early-adopter social/vanity matching.
7. Generate 3-5 high-yield search dorks, including professional LinkedIn and corporate queries (e.g. 'site:linkedin.com/in "Alje Woltjer"', 'site:linkedin.com/in "Alje" "Vooruit"').

Return ONLY a valid JSON object matching this schema:
{{
  "is_pseudonym": bool,
  "first_name": str or null,
  "middle_name": str or null,
  "last_name": str or null,
  "full_name": str,
  "organization": str or null,
  "country_hint": str or null,
  "language_hint": str or null,
  "primary_handle": str,
  "candidate_usernames": [str],
  "search_dorks": [str]
}}"""
            sys_instruct = "You are an expert OSINT intelligence analyst and corporate onomastics specialist. Return strictly valid JSON."
            res = call_groq_api(
                prompt=prompt,
                system_instruction=sys_instruct,
                api_key=api_key,
                response_json=True,
                max_tokens=350
            )
            if res and res.get("success") and res.get("text"):
                parsed = json.loads(res["text"])
                if parsed and isinstance(parsed, dict) and parsed.get("full_name"):
                    result = {
                        "is_pseudonym": bool(parsed.get("is_pseudonym", False)),
                        "first_name": parsed.get("first_name"),
                        "middle_name": parsed.get("middle_name"),
                        "last_name": parsed.get("last_name"),
                        "full_name": parsed.get("full_name").strip(),
                        "organization": parsed.get("organization"),
                        "country_hint": parsed.get("country_hint"),
                        "language_hint": parsed.get("language_hint"),
                        "primary_handle": parsed.get("primary_handle") or local_part,
                        "candidate_usernames": [u.strip().lower() for u in parsed.get("candidate_usernames", []) if u and not re.search(r'\d{2,}$', u)],
                        "search_dorks": [d.strip() for d in parsed.get("search_dorks", []) if d]
                    }
                    _DECOMPOSER_CACHE[cache_key] = result
                    return result
        except Exception as e:
            print(f"[!] AI Target Decomposer error: {e}")

    # Offline Heuristic Fallback
    result = _heuristic_decomposition(local_part, raw_name, domain)
    _DECOMPOSER_CACHE[cache_key] = result
    return result


def _heuristic_decomposition(local: str, raw_name: Optional[str], domain: str) -> Dict[str, Any]:
    """Resilient offline heuristic decomposition when LLM is unavailable."""
    # Strip trailing birth years or random digits
    clean_stem = re.sub(r'\d+$', '', local).strip(" .-_+") or local
    parts = [p.capitalize() for p in re.split(r'[._\-\+\d]+', local) if len(p) >= 2]

    # Dutch / German van / de / der / von detection
    dutch_prefixes = ["van", "de", "der", "den", "ter", "ten", "von", "zu"]
    low_local = local.lower()

    # If raw_name is provided by investigator or detected, prioritize it over opaque email handle
    if raw_name and raw_name.strip() and raw_name.strip().lower() not in ["target user", "webmail target", "target"]:
        clean_raw_name = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50-\u2b55\u203c-\u3299]', '', raw_name).strip()
        name_parts = [p.capitalize() for p in clean_raw_name.split() if len(p) >= 2]
        if len(name_parts) >= 2:
            fn = name_parts[0]
            ln = " ".join(name_parts[1:])
            full = f"{fn} {ln}"
            is_pseudo = False
        else:
            fn = name_parts[0] if name_parts else clean_raw_name
            ln = None
            full = fn
            is_pseudo = False
    elif len(parts) >= 2:
        fn = parts[0]
        ln = " ".join(parts[1:])
        full = f"{fn} {ln}"
        is_pseudo = False
    elif any(dp in low_local for dp in dutch_prefixes):
        # e.g. jandevries -> Jan de Vries
        matched_dp = next(dp for dp in dutch_prefixes if dp in low_local)
        idx = low_local.find(matched_dp)
        if idx >= 2:
            fn = low_local[:idx].capitalize()
            ln = low_local[idx:].capitalize()
            full = f"{fn} {ln}"
            is_pseudo = False
        else:
            fn = clean_stem.capitalize()
            ln = None
            full = fn
            is_pseudo = True
    else:
        full = clean_stem.capitalize() if clean_stem else "Target User"
        fn = full
        ln = None
        is_pseudo = len(clean_stem) < 4 or any(w in clean_stem.lower() for w in ["mister", "boss", "admin", "gamer", "pro", "dark", "shadow", "cyber"])

    cand_usernames = []
    # If a real name is identified, place high-probability name permutations first
    if fn and ln:
        fn_l, ln_l = fn.lower(), ln.lower().replace(" ", "")
        cand_usernames.extend([
            f"{fn_l}{ln_l}",
            f"{fn_l}.{ln_l}",
            f"{fn_l}_{ln_l}",
            f"{fn_l}-{ln_l}",
            f"{ln_l}{fn_l}",
            f"{ln_l}.{fn_l}",
            f"{fn_l[0]}{ln_l}",
            f"{fn_l[0]}.{ln_l}",
            f"{ln_l}{fn_l[0]}",
            fn_l,
            ln_l
        ])

    cand_usernames.append(local)
    if clean_stem and clean_stem != local and len(clean_stem) >= 4 and not clean_stem.isdigit():
        cand_usernames.append(clean_stem)

    country_hint = None
    if domain.endswith(".nl"):
        country_hint = "Netherlands"
    elif domain.endswith(".no"):
        country_hint = "Norway"
    elif domain.endswith(".pl"):
        country_hint = "Poland"
    elif domain.endswith(".de"):
        country_hint = "Germany"
    elif domain.endswith(".uk"):
        country_hint = "United Kingdom"

    is_freemail = any(d in domain.lower() for d in ["gmail", "yahoo", "outlook", "hotmail", "proton", "icloud", "zoho", "mail", "live", "aol", "yandex"])
    org_hint = domain.split(".")[0].capitalize() if not is_freemail and "." in domain else None

    dorks = [f'"{full}"', f'"{full}" linkedin', f'"{full}" facebook']
    if org_hint and fn:
        dorks.append(f'"{full}" "{org_hint}"')
        dorks.append(f'site:linkedin.com/in "{full}" OR "{fn}" "{org_hint}"')
        dorks.append(f'site:linkedin.com/in/{fn.lower()}')

    return {
        "is_pseudonym": is_pseudo,
        "first_name": fn,
        "middle_name": None,
        "last_name": ln,
        "full_name": full,
        "organization": org_hint,
        "country_hint": country_hint,
        "language_hint": "Dutch" if country_hint == "Netherlands" else ("Polish" if country_hint == "Poland" else "English"),
        "primary_handle": clean_stem,
        "candidate_usernames": cand_usernames,
        "search_dorks": dorks
    }

def _build_fallback_result(name: str, handle: str, is_pseudo: bool) -> Dict[str, Any]:
    return {
        "is_pseudonym": is_pseudo,
        "first_name": name.split()[0] if name else None,
        "middle_name": None,
        "last_name": name.split()[-1] if len(name.split()) > 1 else None,
        "full_name": name,
        "country_hint": None,
        "language_hint": None,
        "primary_handle": handle,
        "candidate_usernames": [handle],
        "search_dorks": [f'"{name}"']
    }
