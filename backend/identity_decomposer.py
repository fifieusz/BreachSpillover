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

    if (clean_email.startswith("phone.") and clean_email.endswith("@osint.local")) or (clean_email.startswith("+") and "@" not in clean_email):
        digits = re.sub(r'\D', '', local_part.replace("phone.", ""))
        res = {
            "is_pseudonym": False,
            "is_telecom_target": True,
            "first_name": None,
            "middle_name": None,
            "last_name": None,
            "full_name": raw_name or f"Telecom Target +{digits}",
            "organization": "Telecom Network",
            "country_hint": None,
            "language_hint": None,
            "primary_handle": None,
            "candidate_usernames": [],
            "search_dorks": [f'"{digits}"', f'"+{digits}"']
        }
        _DECOMPOSER_CACHE[cache_key] = res
        return res

    # Attempt AI decomposition via Groq
    from backend.cardinal.llm import call_groq_api, resolve_api_key
    api_key = resolve_api_key("groq")
    if api_key:
        try:
            prompt = f"""Analyze the target email: '{clean_email}'.
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
                max_tokens=280
            )
            if res and res.get("success") and res.get("text"):
                parsed = json.loads(res["text"])
                if parsed and isinstance(parsed, dict) and parsed.get("full_name"):
                    raw_cands = parsed.get("candidate_usernames", [])
                    cleaned_cands = []
                    is_pseudo = bool(parsed.get("is_pseudonym", False))
                    for u in raw_cands:
                        if not u:
                            continue
                        cu = u.strip().lower()
                        # Reject domain extensions and email artifacts
                        if any(cu.endswith(ext) for ext in [".com", ".net", ".org", ".io", ".nl", ".de", ".uk", ".no", ".pl"]):
                            continue
                        if "@" in cu or cu.endswith("gmail") or cu.endswith("yahoo") or cu.endswith("outlook"):
                            continue
                        # If real name was identified, drop trailing random digits from name permutations
                        if not is_pseudo and re.search(r'\d{2,}$', cu):
                            continue
                        if cu not in cleaned_cands:
                            cleaned_cands.append(cu)
                    # Ensure local_part and primary_handle are present for pseudonyms
                    if is_pseudo:
                        if local_part.lower() not in cleaned_cands:
                            cleaned_cands.insert(0, local_part.lower())
                        p_h = (parsed.get("primary_handle") or "").strip().lower()
                        if p_h and p_h not in cleaned_cands:
                            cleaned_cands.insert(1, p_h)

                    result = {
                        "is_pseudonym": is_pseudo,
                        "first_name": parsed.get("first_name"),
                        "middle_name": parsed.get("middle_name"),
                        "last_name": parsed.get("last_name"),
                        "full_name": parsed.get("full_name").strip(),
                        "organization": parsed.get("organization"),
                        "country_hint": parsed.get("country_hint"),
                        "language_hint": parsed.get("language_hint"),
                        "primary_handle": parsed.get("primary_handle") or local_part,
                        "candidate_usernames": cleaned_cands,
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
    """Resilient offline heuristic decomposition powered by multilingual onomastic deconstruction."""
    from backend.onomastic_engine import deconstruct_onomastic_handle

    # 1. If raw_name is provided by investigator or detected, prioritize it
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
        onom = deconstruct_onomastic_handle(local, target_name_hint=full)
        clean_stem = onom.get("primary_handle") or re.sub(r'\d+$', '', local).strip(" .-_+") or local
        byear = onom.get("birth_year")
        age = onom.get("estimated_age")
        culture_hint = onom.get("culture_hint")
        is_temporal_spec = onom.get("is_speculative", False)
    else:
        # 2. Deconstruct via multilingual onomastic engine
        onom = deconstruct_onomastic_handle(local)
        is_pseudo = onom["is_pseudonym"]
        fn = onom["given_name"]
        ln = onom["family_name"]
        full = onom["full_name"]
        clean_stem = onom.get("primary_handle") or re.sub(r'\d+$', '', local).strip(" .-_+") or local
        byear = onom.get("birth_year")
        age = onom.get("estimated_age")
        culture_hint = onom.get("culture_hint")
        is_temporal_spec = onom.get("is_speculative", False)

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
            f"{ln_l}{fn_l[0]}"
        ])
        if byear:
            cand_usernames.extend([
                f"{fn_l}{ln_l}{byear}",
                f"{fn_l}{byear}",
                f"{ln_l}{byear}"
            ])
    elif is_pseudo:
        cand_usernames.append(local)
        if clean_stem and clean_stem != local and len(clean_stem) >= 3 and not clean_stem.isdigit():
            cand_usernames.append(clean_stem)
        m_dig = re.search(r'\d+$', local)
        if m_dig:
            digs = m_dig.group(0)
            cand_usernames.append(f"{clean_stem}_{digs}")
            cand_usernames.append(f"{clean_stem}-{digs}")
        if clean_stem.startswith("x") and len(clean_stem) > 3 and clean_stem[1].isalpha():
            stem_nox = clean_stem[1:]
            cand_usernames.append(stem_nox)
            cand_usernames.append(f"x_{stem_nox}")
            if m_dig:
                cand_usernames.append(f"{stem_nox}{m_dig.group(0)}")

    if local not in cand_usernames:
        cand_usernames.append(local)
    if clean_stem and clean_stem != local and len(clean_stem) >= 4 and not clean_stem.isdigit() and clean_stem not in cand_usernames:
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

    if is_pseudo:
        full_email_str = f"{local}@{domain}" if "@" not in local else local
        dorks = [
            f'"{full_email_str}"',
            f'"{local}" site:pastebin.com OR site:github.com OR site:rentry.co',
            f'"{clean_stem}" (site:reddit.com OR site:twitter.com OR site:twitch.tv OR site:steamcommunity.com)',
            f'"{local}" ("my name is" OR "call me" OR "email" OR "discord" OR "telegram")',
            f'"{local}"'
        ]
    else:
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
        "birth_year": byear,
        "estimated_age": age,
        "is_temporal_speculative": is_temporal_spec,
        "culture_hint": culture_hint,
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
