import os
import json
import logging
import re
import unicodedata
from typing import Dict, Any, List, Optional, Set, Tuple

from backend.cardinal.llm import call_groq_api, resolve_api_key, load_dotenv
from backend.identity_signals import (
    normalize_handle,
    handle_stem,
    split_given_family,
    is_null_value,
    is_domain_or_url,
    detect_given_name_conflict,
    detect_slug_given_conflict,
    detect_declared_gender,
    detect_demographic_contradiction,
    normalize_gender,
    build_target_anchors,
    classify_handle,
    email_localpart,
    looks_like_image_url,
    PERSONA_ATTR_RE,
    HANDLE_ALIAS,
    HANDLE_BARE_SURNAME,
)

logger = logging.getLogger("breach_spillover.ai_cardinal")

ARBITER_MODEL = "openai/gpt-oss-20b"
ARBITER_MAX_TOKENS = 2400

def build_observation_manifest(
    seed_query: str,
    raw_breaches: Optional[List[Dict[str, Any]]] = None,
    personal_sites: Optional[List[Dict[str, Any]]] = None,
    git_commits: Optional[List[Dict[str, Any]]] = None,
    search_snippets: Optional[List[Dict[str, Any]]] = None,
    discovered_profiles: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Normalises every raw observation into one compact evidence manifest."""
    obs: Dict[str, Any] = {
        "seed": (seed_query or "").strip(),
        "breach_clues": [],
        "personal_site_clues": [],
        "git_clues": [],
        "search_snippet_clues": [],
        "profile_clues": [],
    }

    for b in (raw_breaches or [])[:15]:
        clue: Dict[str, Any] = {}
        if b.get("username"):
            clue["username"] = b["username"]
        if b.get("name") or b.get("full_name"):
            clue["name"] = b.get("name") or b.get("full_name")
        if b.get("phone"):
            clue["phone"] = b["phone"]
        if b.get("ip_address"):
            clue["ip"] = b["ip_address"]
        if b.get("breach_name") or b.get("leak_name"):
            clue["breach"] = b.get("breach_name") or b.get("leak_name")
        if clue:
            obs["breach_clues"].append(clue)

    for ps in personal_sites or []:
        meta = ps.get("site_metadata") or ps
        obs["personal_site_clues"].append({
            "url": meta.get("url"),
            "bio": meta.get("bio"),
            "city": meta.get("city"),
            "country": meta.get("country"),
            "workplace": meta.get("workplace"),
            "job_title": meta.get("job_title"),
            "secondary_emails": meta.get("secondary_emails", []),
            "phone_numbers": meta.get("phone_numbers", []),
            "linkedin_url": meta.get("linkedin_url"),
            "facebook_url": meta.get("facebook_url"),
        })

    for gc in (git_commits or [])[:10]:
        obs["git_clues"].append({
            "author_name": gc.get("author_name") or gc.get("name"),
            "author_email": gc.get("author_email") or gc.get("email"),
            "repo": gc.get("repo"),
        })

    for snip in (search_snippets or [])[:12]:
        obs["search_snippet_clues"].append({
            "title": snip.get("title"),
            "url": snip.get("url"),
            "snippet": snip.get("snippet"),
        })

    for pr in (discovered_profiles or [])[:30]:
        url = pr.get("url") or pr.get("profile_url")
        if looks_like_image_url(url):
            continue  # visual media never enters the account evidence graph
        obs["profile_clues"].append({
            "platform": pr.get("platform"),
            "url": url,
            "handle": pr.get("handle") or normalize_handle(url),
            "display_name": pr.get("display_name") or pr.get("name") or pr.get("real_name"),
            "bio": pr.get("bio") or pr.get("description") or pr.get("context"),
            "location": pr.get("location") or pr.get("country"),
            "is_email_bound": bool(pr.get("is_email_bound")),
            "is_commit_bound": bool(pr.get("is_commit_bound")),
        })
    return obs

ARBITER_SYSTEM_INSTRUCTION = (
    "You are an expert digital forensics identity arbiter. Evaluate only the factual evidence provided. "
    "Never invent accounts, names or URLs. Every URL you output must appear verbatim in the observations. "
    "Return only valid JSON."
)

ARBITER_SCHEMA = """{
  "real_name": str or null,
  "perceived_gender": "male" | "female" | "unknown",
  "pronouns": "he/him" | "she/her" | "they/them" | null,
  "aliases": [str],
  "location": {"city": str or null, "country": str or null},
  "workplace": str or null,
  "job_title": str or null,
  "education": str or null,
  "secondary_emails": [str],
  "phone_numbers": [str],
  "verified_profiles": [{"platform": str, "url": str, "handle": str, "display_name": str or null, "confidence": float, "reasoning": str}],
  "alias_personas": [{"alias": str, "reasoning": str, "accounts": [{"platform": str, "url": str, "handle": str, "reasoning": str}]}],
  "namesake_collisions": [{"platform": str, "url": str, "handle": str, "display_name": str or null, "quarantine_reason": str}],
  "speculative_probes": [{"platform": str, "url": str, "handle": str, "quarantine_reason": str}],
  "rejected_profiles": [{"url": str, "rejection_reason": str}],
  "forensic_synthesis": str
}"""


def _build_arbiter_prompt(seed: str, observations: Dict[str, Any]) -> str:
    return f"""Analyze the multi-source OSINT evidence graph collected for target seed '{seed}'.

MISSION
1. Triangulate the authentic human identity: full legal name, perceived gender, pronouns, location, employer, education.
2. Classify EVERY candidate account in profile_clues / search_snippet_clues into exactly one category:
   - verified_profiles: bound to the target by (a) direct email registration / commit-author email (is_email_bound / is_commit_bound),
     (b) an exact match of BOTH the target's given and family name with zero contradicting signals, or
     (c) an outbound link from the target's own portfolio or repository.
   - alias_personas: the target's non-legal-name personas (gamer tags, hacker handles, breach/infostealer usernames, in-game persona names).
     An alias is authentic only when it is linked to the target by evidence (appears in a breach record for the seed, a commit, a verified
     profile, or a declared nickname/persona attribute). Group every account that uses that alias under it. Do NOT treat a handle that is
     merely a common word with no linking evidence as an alias.
   - namesake_collisions: accounts belonging to a DIFFERENT human (shares the family name or handle but has a different given name,
     a contradicting gender/pronoun declaration, or a contradicting location/age/biography).
   - speculative_probes: single-signal vanity leads (name permutations, bare given names or bare family names) without email binding.
   - rejected_profiles: obvious noise (dead links, unrelated organisations, platform placeholder pages).

ZERO-CONTRADICTION RULES (absolute)
- RULE 1 (GIVEN NAME): once the target's given + family name are established, any account whose display name shares the family name but
  carries an incompatible given name is a namesake_collision. Initials and prefix diminutives of the same given name are compatible.
- RULE 2 (DEMOGRAPHIC): an account declaring pronouns or a gendered self-descriptor that contradicts the established target gender is a
  namesake_collision with a 'Demographic contradiction' quarantine_reason.
- RULE 3 (STRICT VERIFICATION): ambiguous, single-given-name, surname-only or permutation handles are NEVER verified_profiles.
- RULE 4 (MEDIA): avatars, banners and photo URLs are visual media assets, never accounts. Do not list image URLs in any category.

OBSERVATIONS
{json.dumps(observations, indent=1, default=str)}

Return ONLY a JSON object matching this schema:
{ARBITER_SCHEMA}"""

def synthesize_identity_from_observations(
    seed_query: str,
    raw_breaches: Optional[List[Dict[str, Any]]] = None,
    personal_sites: Optional[List[Dict[str, Any]]] = None,
    git_commits: Optional[List[Dict[str, Any]]] = None,
    search_snippets: Optional[List[Dict[str, Any]]] = None,
    discovered_profiles: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Cognitive Stage 1: Triangulates the true human identity behind an arbitrary seed
    (gamer tag, corporate email, or pseudonym) and categorises every candidate
    account into verified / alias persona / namesake collision / speculative probe.
    """
    clean_seed = (seed_query or "").strip()
    observations = build_observation_manifest(
        clean_seed, raw_breaches, personal_sites, git_commits, search_snippets, discovered_profiles
    )

    api_key = resolve_api_key("groq") or resolve_api_key("gemini")
    if api_key:
        try:
            res = call_groq_api(
                prompt=_build_arbiter_prompt(clean_seed, observations),
                system_instruction=ARBITER_SYSTEM_INSTRUCTION,
                api_key=api_key,
                model=ARBITER_MODEL,
                response_json=True,
                max_tokens=ARBITER_MAX_TOKENS
            )
            if res and res.get("success") and res.get("text"):
                parsed = json.loads(res["text"])
                if isinstance(parsed, dict):
                    parsed["arbiter_mode"] = "LLM_COGNITIVE"
                    return _enforce_cardinal_strictness(parsed, observations)
        except Exception as e:
            logger.warning(f"AI Cardinal synthesis exception: {e}")

    fallback_res = _fallback_local_triangulation(clean_seed, observations)
    fallback_res["arbiter_mode"] = "DETERMINISTIC_FALLBACK"
    return _enforce_cardinal_strictness(fallback_res, observations)

def _clue_context_for_url(url: str, observations: Dict[str, Any]) -> Dict[str, Any]:
    """Collects display name, bio text and binding flags for a URL from the manifest."""
    ctx = {"name": "", "bio": "", "email_bound": False, "commit_bound": False}
    if not url:
        return ctx
    for pc in observations.get("profile_clues", []):
        if pc.get("url") == url:
            ctx["bio"] += " " + str(pc.get("bio") or "")
            ctx["name"] = ctx["name"] or str(pc.get("display_name") or "")
            ctx["email_bound"] = ctx["email_bound"] or bool(pc.get("is_email_bound"))
            ctx["commit_bound"] = ctx["commit_bound"] or bool(pc.get("is_commit_bound"))
    for sc in observations.get("search_snippet_clues", []):
        if sc.get("url") == url:
            ctx["bio"] += " " + str(sc.get("snippet") or "")
    return ctx


def _infer_target_gender(parsed: Dict[str, Any], observations: Dict[str, Any]) -> str:
    """Uses the arbiter's verdict, else explicit pronouns in self-authored sources only."""
    g = normalize_gender(parsed.get("perceived_gender"))
    if g != "unknown":
        return g
    g = normalize_gender(parsed.get("pronouns"))
    if g != "unknown":
        return g
    self_authored = " ".join(str(ps.get("bio") or "") for ps in observations.get("personal_site_clues", []))
    return detect_declared_gender(self_authored, include_descriptors=False) or "unknown"


def _contradiction_verdict(
    profile: Dict[str, Any],
    real_name: str,
    target_gender: str,
    observations: Dict[str, Any],
    anchors: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    """
    Returns {"category": "namesake"|"speculative", "reason": str} when a
    profile violates a zero-contradiction rule, else None.
    """
    url = str(profile.get("url") or "")
    clue = _clue_context_for_url(url, observations)
    cand_name = str(profile.get("display_name") or "").strip() or clue["name"]
    cand_bio = " ".join([str(profile.get("bio") or ""), clue["bio"]])
    t_given = split_given_family(real_name)[0]

    given_conflict = detect_given_name_conflict(real_name, cand_name)
    if given_conflict:
        return {"category": "namesake", "reason": f"Conflicting given name ('{given_conflict.title()}' vs target '{t_given.title()}') - quarantined as suspected namesake/relative"}
    slug_conflict = detect_slug_given_conflict(real_name, url)
    if slug_conflict:
        return {"category": "namesake", "reason": f"Conflicting vanity slug ('{slug_conflict}' vs target '{t_given}') - quarantined as suspected namesake"}
    demo = detect_demographic_contradiction(target_gender, cand_bio)
    if demo:
        return {"category": "namesake", "reason": f"Demographic contradiction: {demo}"}

    handle = normalize_handle(profile.get("handle") or url)
    bound = clue["email_bound"] or clue["commit_bound"] or bool(profile.get("is_email_bound"))
    if handle and classify_handle(handle, anchors) == HANDLE_BARE_SURNAME and not bound:
        return {"category": "speculative", "reason": f"Bare surname handle '@{handle}' lacking email/commit binding - speculative vanity probe"}
    return None

def _as_account(acc: Any) -> Dict[str, Any]:
    if isinstance(acc, dict):
        return dict(acc)
    return {"url": str(acc or ""), "handle": normalize_handle(acc)}


def _validate_alias_personas(
    alias_personas: List[Any],
    real_name: str,
    target_gender: str,
    observations: Dict[str, Any],
    anchors: Dict[str, Any],
    namesakes: List[Dict[str, Any]],
    speculative: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Keeps only genuine non-name aliases; contradicting accounts are re-routed."""
    clean: Dict[str, Dict[str, Any]] = {}
    for ap in alias_personas or []:
        if isinstance(ap, str):
            ap = {"alias": ap, "accounts": []}
        if not isinstance(ap, dict):
            continue
        key = handle_stem(ap.get("alias") or ap.get("handle") or "")
        accounts = [_as_account(a) for a in (ap.get("accounts") or [])]
        accounts = [a for a in accounts if not looks_like_image_url(a.get("url"))]
        if not key or is_null_value(key) or classify_handle(key, anchors) != HANDLE_ALIAS:
            for acc in accounts:
                speculative.append(dict(acc, quarantine_reason=f"Handle '@{key}' is derived from the legal name, not an independent alias"))
            continue
        bucket = clean.setdefault(key, {"alias": key, "reasoning": ap.get("reasoning") or "", "accounts": []})
        for acc in accounts:
            verdict = _contradiction_verdict(acc, real_name, target_gender, observations, anchors)
            if verdict and verdict["category"] == "namesake":
                namesakes.append(dict(acc, quarantine_reason=verdict["reason"]))
                continue
            if acc.get("url") and not any(x.get("url") == acc["url"] for x in bucket["accounts"]):
                bucket["accounts"].append(acc)
    return list(clean.values())

def _alias_candidate(raw: Any, anchors: Dict[str, Any]) -> str:
    if not raw or is_domain_or_url(raw):
        return ""
    key = handle_stem(raw)
    if not key or len(key) < 3 or is_null_value(key) or " " in key or is_domain_or_url(key):
        return ""
    return key if classify_handle(key, anchors) == HANDLE_ALIAS else ""


def _deterministic_aliases(observations: Dict[str, Any], anchors: Dict[str, Any], bound_urls: Set[str]) -> Set[str]:
    """
    Harvests aliases ONLY from evidence linked to the seed: breach usernames,
    commit author identities, declared persona attributes, and handles of
    bound/verified accounts. Unbound probe handles are never promoted.
    """
    found: Set[str] = set()

    def _add(raw: Any) -> None:
        key = _alias_candidate(raw, anchors)
        if key and not is_domain_or_url(key):
            found.add(key)

    for bc in observations.get("breach_clues", []):
        _add(bc.get("username"))
    for gc in observations.get("git_clues", []):
        _add(email_localpart(gc.get("author_email") or ""))
        author = str(gc.get("author_name") or "").strip()
        if author and " " not in author and not is_domain_or_url(author):
            _add(author)
    for pc in observations.get("profile_clues", []):
        text = f"{pc.get('display_name') or ''} {pc.get('bio') or ''}"
        for m in PERSONA_ATTR_RE.finditer(text):
            if not is_domain_or_url(m.group(1)):
                _add(m.group(1))
        m_pers = re.search(r"persona[:\s]+['\"]?([a-zA-Z0-9_\-\.]{3,25})['\"]?", text, re.IGNORECASE)
        if m_pers and not is_domain_or_url(m_pers.group(1)):
            _add(m_pers.group(1))
        cand_raw_h = pc.get("handle")
        h_cand = cand_raw_h if (cand_raw_h and not is_domain_or_url(cand_raw_h)) else None
        if not h_cand and pc.get("url"):
            norm_u = normalize_handle(pc.get("url"))
            if norm_u and not is_domain_or_url(norm_u):
                h_cand = norm_u
        if h_cand and not is_domain_or_url(h_cand):
            if pc.get("is_email_bound") or pc.get("is_commit_bound") or (pc.get("url") and pc.get("url") in bound_urls):
                _add(h_cand)
                _add(handle_stem(h_cand))
            plat = (pc.get("platform") or "").lower()
            if any(g in plat for g in ["steam", "chess", "roblox", "telegram", "github"]):
                _add(h_cand)
                _add(handle_stem(h_cand))
    return found

def _dedupe_by_url(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[str] = set()
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        u = str(it.get("url") or "").strip().lower().rstrip("/")
        if looks_like_image_url(u):
            continue
        if u and u in seen:
            continue
        if u:
            seen.add(u)
        out.append(it)
    return out


def _enforce_cardinal_strictness(parsed: Dict[str, Any], observations: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic zero-contradiction gatekeeper applied on top of the arbiter.
    Demotes given-name conflicts and pronoun contradictions out of
    verified_profiles, validates alias personas, strips visual media, and
    keeps the legacy `suspected_profiles` contract populated.
    """
    parsed = dict(parsed or {})
    for key in ("verified_profiles", "alias_personas", "namesake_collisions", "speculative_probes",
                "rejected_profiles", "suspected_profiles", "aliases", "secondary_emails", "phone_numbers"):
        if not isinstance(parsed.get(key), list):
            parsed[key] = []

    real_name = str(parsed.get("real_name") or "").strip()
    seed = str(observations.get("seed") or "")
    anchors = build_target_anchors(real_name, seed if "@" in seed else "")
    target_gender = _infer_target_gender(parsed, observations)
    parsed["perceived_gender"] = target_gender

    namesakes = _dedupe_by_url(parsed["namesake_collisions"])
    speculative = _dedupe_by_url(parsed["speculative_probes"])
    legacy_suspected = _dedupe_by_url(parsed["suspected_profiles"])

    verified_clean: List[Dict[str, Any]] = []
    for profile in _dedupe_by_url(parsed["verified_profiles"]):
        verdict = _contradiction_verdict(profile, real_name, target_gender, observations, anchors)
        if not verdict:
            verified_clean.append(profile)
            continue
        cap = 0.65 if verdict["category"] == "namesake" else 0.50
        if verdict["reason"].startswith("Demographic"):
            cap = 0.50
        demoted = dict(profile, confidence=min(float(profile.get("confidence") or cap), cap), quarantine_reason=verdict["reason"])
        (namesakes if verdict["category"] == "namesake" else speculative).append(demoted)

    alias_personas = _validate_alias_personas(
        parsed["alias_personas"], real_name, target_gender, observations, anchors, namesakes, speculative
    )

    # Alias consolidation: arbiter aliases + alias personas + deterministic evidence
    bound_urls = {str(p.get("url")) for p in verified_clean if p.get("url")}
    consolidated: Set[str] = set()
    for al in list(parsed["aliases"]) + [ap["alias"] for ap in alias_personas]:
        key = _alias_candidate(al, anchors)
        if key:
            consolidated.add(key)
    consolidated |= _deterministic_aliases(observations, anchors, bound_urls)
    known = {ap["alias"] for ap in alias_personas}
    for al in sorted(consolidated - known):
        alias_personas.append({"alias": al, "reasoning": "Alias linked to target evidence (breach, commit, persona attribute or bound account).", "accounts": []})

    # Legacy contract: everything not verified (and not rejected) is suspected.
    alias_accounts = [dict(a, quarantine_reason=f"Account under discovered alias persona '@{ap['alias']}'") for ap in alias_personas for a in ap["accounts"]]
    for item in namesakes + speculative + alias_accounts:
        item.setdefault("quarantine_reason", "Quarantined by identity arbiter")
    verified_urls = {str(p.get("url") or "").lower().rstrip("/") for p in verified_clean}
    suspected = [s for s in _dedupe_by_url(legacy_suspected + namesakes + speculative + alias_accounts)
                 if str(s.get("url") or "").lower().rstrip("/") not in verified_urls]

    parsed.update({
        "verified_profiles": verified_clean,
        "alias_personas": alias_personas,
        "namesake_collisions": _dedupe_by_url(namesakes),
        "speculative_probes": _dedupe_by_url(speculative),
        "suspected_profiles": suspected,
        "aliases": sorted(consolidated | known),
    })
    return parsed

def _triangulate_real_name(observations: Dict[str, Any]) -> Optional[str]:
    """Prefers verified profiles (LinkedIn, Facebook), multi-token commit author names, then breach records."""
    for pc in observations.get("profile_clues", []):
        plat = (pc.get("platform") or "").lower()
        if plat in ["linkedin", "facebook", "portfolio"] or pc.get("is_email_bound") or pc.get("is_commit_bound"):
            d_name = str(pc.get("display_name") or "").strip()
            if len(split_given_family(d_name)[1]) >= 2:
                return d_name
    for gc in observations.get("git_clues", []):
        name = str(gc.get("author_name") or "").strip()
        if len(split_given_family(name)[1]) >= 2:
            return name
    for bc in observations.get("breach_clues", []):
        name = str(bc.get("name") or "").strip()
        if len(split_given_family(name)[1]) >= 2:
            return name
    for pc in observations.get("profile_clues", []):
        d_name = str(pc.get("display_name") or "").strip()
        if len(split_given_family(d_name)[1]) >= 2:
            return d_name
    for gc in observations.get("git_clues", []):
        if gc.get("author_name"):
            return str(gc["author_name"]).strip()
    return None


def _fallback_identity_attributes(observations: Dict[str, Any]) -> Dict[str, Any]:
    attrs: Dict[str, Any] = {
        "location": {"city": None, "country": None},
        "workplace": None, "job_title": None,
        "secondary_emails": [], "phone_numbers": [],
        "portfolio_links": [],
    }
    for ps in observations.get("personal_site_clues", []):
        if ps.get("city"):
            attrs["location"]["city"] = ps["city"]
        if ps.get("country"):
            attrs["location"]["country"] = ps["country"]
        attrs["workplace"] = ps.get("workplace") or attrs["workplace"]
        attrs["job_title"] = ps.get("job_title") or attrs["job_title"]
        attrs["secondary_emails"].extend(ps.get("secondary_emails") or [])
        attrs["phone_numbers"].extend(ps.get("phone_numbers") or [])
        for plat, key in (("LinkedIn", "linkedin_url"), ("Facebook", "facebook_url")):
            if ps.get(key):
                attrs["portfolio_links"].append((plat, ps[key], ps.get("url")))
    attrs["secondary_emails"] = sorted(set(attrs["secondary_emails"]))
    attrs["phone_numbers"] = sorted(set(attrs["phone_numbers"]))
    return attrs

def _fallback_local_triangulation(seed: str, observations: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic offline arbiter. Extracts the core identity, aliases and
    candidate categories from commit authors, breach logins and portfolio
    metadata when no LLM is reachable. Output schema matches the LLM arbiter.
    """
    real_name = _triangulate_real_name(observations)
    attrs = _fallback_identity_attributes(observations)
    anchors = build_target_anchors(real_name or "", seed if "@" in (seed or "") else "")
    target_gender = _infer_target_gender({}, observations)

    verified: List[Dict[str, Any]] = []
    for plat, link, site in attrs["portfolio_links"]:
        verified.append({
            "platform": plat, "url": link, "handle": normalize_handle(link), "confidence": 0.98,
            "reasoning": f"Outbound link extracted directly from the target's personal portfolio ({site}).",
        })

    alias_keys = _deterministic_aliases(observations, anchors, {v["url"] for v in verified})
    alias_map: Dict[str, Dict[str, Any]] = {k: {"alias": k, "reasoning": "Alias linked to target evidence.", "accounts": []} for k in alias_keys}
    namesakes: List[Dict[str, Any]] = []
    speculative: List[Dict[str, Any]] = []

    for pc in observations.get("profile_clues", []):
        url = pc.get("url")
        if not url or any(v["url"] == url for v in verified):
            continue
        acc = {"platform": pc.get("platform"), "url": url, "handle": pc.get("handle"), "display_name": pc.get("display_name")}
        verdict = _contradiction_verdict(acc, real_name or "", target_gender, observations, anchors)
        if verdict:
            (namesakes if verdict["category"] == "namesake" else speculative).append(dict(acc, quarantine_reason=verdict["reason"]))
            continue
        if pc.get("is_email_bound") or pc.get("is_commit_bound"):
            verified.append(dict(acc, confidence=0.95, reasoning="Account bound to target email / commit author."))
            continue
        if real_name and len(split_given_family(real_name)[1]) >= 2 and not detect_given_name_conflict(real_name, pc.get("display_name")):
            t_given, t_family = split_given_family(real_name)
            c_given, c_family = split_given_family(pc.get("display_name") or "")
            if c_given == t_given and c_family == t_family:
                verified.append(dict(acc, confidence=0.88, reasoning="Exact legal name match with zero contradictions."))
                continue
        key = handle_stem(pc.get("handle") or "")
        if key in alias_map:
            alias_map[key]["accounts"].append(acc)
            continue
        if key and classify_handle(key, anchors) not in (HANDLE_ALIAS,):
            speculative.append(dict(acc, quarantine_reason=f"Unbound name-derived handle '@{key}' - speculative probe"))

    return {
        "real_name": real_name,
        "perceived_gender": target_gender,
        "pronouns": None,
        "aliases": sorted(alias_keys),
        "location": attrs["location"],
        "workplace": attrs["workplace"],
        "job_title": attrs["job_title"],
        "education": None,
        "secondary_emails": attrs["secondary_emails"],
        "phone_numbers": attrs["phone_numbers"],
        "verified_profiles": verified,
        "alias_personas": list(alias_map.values()),
        "namesake_collisions": namesakes,
        "speculative_probes": speculative,
        "suspected_profiles": [],
        "rejected_profiles": [],
        "forensic_synthesis": f"Offline deterministic triangulation compiled for target '{seed}'.",
    }


def clean_text_symbols(val: Any) -> str:
    """Removes emojis and unprintable surrogate characters."""
    if not val:
        return ""
    return re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50-\u2b55\u203c-\u3299]', '', str(val)).strip()

def normalize_string(val: str) -> str:
    if not val:
        return ""
    val = clean_text_symbols(val)
    decomposed = unicodedata.normalize('NFKD', val)
    stripped = ''.join(c for c in decomposed if not unicodedata.combining(c))
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', stripped).lower()
    return re.sub(r'\s+', ' ', cleaned).strip()

def ai_verify_and_quarantine_candidates(
    target_info: Dict[str, Any],
    candidates: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluates candidate platform accounts against the target's identity anchors using
    high-reasoning AI (Groq gpt-oss-120b / Gemini Flash).
    
    Returns:
    (verified_profiles, suspected_quarantined_profiles, rejected_profiles)
    """
    if not candidates:
        return ([], [], [])

    # Filter out empty or duplicate candidates by URL/handle
    unique_candidates: List[Dict[str, Any]] = []
    seen_keys = set()
    for idx, cand in enumerate(candidates):
        u = (cand.get("url") or cand.get("profile_url") or "").strip()
        h = (cand.get("handle") or "").strip().lower()
        p = (cand.get("platform") or "").strip().lower()
        key = (p, h) if h else (p, u)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        c_copy = dict(cand)
        c_copy["_cid"] = f"c{idx + 1}"
        unique_candidates.append(c_copy)

    # If any candidate is ALREADY email-bound (e.g. Holehe confirmed registration),
    # mark it directly as VERIFIED without needing LLM evaluation
    direct_verified: List[Dict[str, Any]] = []
    to_evaluate: List[Dict[str, Any]] = []

    for c in unique_candidates:
        if c.get("is_email_bound"):
            c["is_verified"] = True
            c["is_suspected"] = False
            c["confidence"] = max(c.get("confidence", 0.98), 0.98)
            c["tie_type"] = "EMAIL_REGISTRATION_VERIFIED"
            c["tie_badge"] = "[TIED: EMAIL VERIFIED]"
            direct_verified.append(c)
        else:
            to_evaluate.append(c)

    if not to_evaluate:
        return (direct_verified, [], [])

    # Prepare compact candidate payloads for LLM
    target_email = (target_info.get("email") or "").strip()
    target_name = (target_info.get("full_name") or target_info.get("primary_name") or "").strip()
    target_handles = [h.lower() for h in target_info.get("primary_handles", []) if h]
    target_locations = [l for l in target_info.get("locations", []) if l]
    ground_truth = target_info.get("ground_truth_accounts", [])

    candidate_summaries = []
    for c in to_evaluate:
        summary = {
            "id": c["_cid"],
            "platform": c.get("platform", "Platform"),
            "handle": c.get("handle") or "",
            "display_name": clean_text_symbols(c.get("name") or c.get("real_name") or c.get("persona_name") or ""),
            "location": clean_text_symbols(c.get("location") or c.get("country") or ""),
            "url": c.get("url") or "",
            "provenance": c.get("source") or c.get("provenance") or "platform_probe",
            "context_notes": clean_text_symbols(c.get("context") or "")
        }
        candidate_summaries.append(summary)

    # Call AI reasoning model
    api_key = resolve_api_key("groq") or resolve_api_key("gemini")
    ai_evaluations: Dict[str, Dict[str, Any]] = {}

    authenticated_handles = target_info.get("authenticated_handles", [])

    language_hint = target_info.get("language_hint") or "Polish" if any("pl" in str(loc).lower() or "poland" in str(loc).lower() for loc in target_locations) else None

    if api_key:
        try:
            prompt = f"""You are an elite OSINT identity analyst. Your objective is to analyze investigated targets holistically as real humans, verify authentic accounts (including alt/secondary gaming accounts), quarantine ambiguous candidates without losing data, and reject false-positive stranger collisions.

TARGET IDENTITY:
- Email: {target_email or "Unknown"}
- Real Name: {target_name or "Unknown"}
- Authenticated Developer Logins / Commit Authors: {json.dumps(authenticated_handles)}
- Known / Root Handles: {json.dumps(target_handles)}
- Cultural / Language Background: {language_hint or "Unknown"}
- Discovered Physical Locations / Countries: {json.dumps(target_locations)}
- Verified Ground Truth Sources: {json.dumps(ground_truth)}

CANDIDATE ACCOUNTS:
{json.dumps(candidate_summaries, indent=2)}

INSTRUCTIONS & IDENTITY PRINCIPLES:
1. Holistic Multi-Account Person Analysis:
   - On gaming and competitive platforms (Steam, Roblox, Chess.com, Discord), users frequently maintain multiple accounts (e.g. primary account + secondary/alt/smurf account).
   - Gamers frequently use humorous, joke, or meme locations (e.g. a tropical island or Antarctica). If multiple accounts share the same quirky or unusual location and align with the target's distinctive handles or native language (e.g. bio text in the target's language, a persona name that is a diminutive of a verified author handle), they belong to the target as primary and alt accounts! Mark both as VERIFIED (with tie_badge '[TIED: PRIMARY STEAM]' or '[TIED: ALT GAMING PROFILE]').
2. Short Handle Collision Protection:
   - Short vanity URLs (<=4 chars) on massive gaming/social platforms have high vanity collision rates. If the persona display name is discordant (e.g. an entirely different first name), it is a vanity collision stranger. REJECT it.
3. Single Given-Name Handle Collision Protection:
   - On massive public developer/code/social platforms (GitHub, GitLab, DockerHub, Keybase, LinkedIn), handles that are merely a single given name (e.g. '@<given_name>') without surname or distinguishing digits are early adopter registrations. Unless the profile's real name matches the target's multi-token full name (including surname), or is directly bound by email, do NOT mark as VERIFIED. If unconfirmed, mark as 'SUSPECTED' (quarantined in drawer) or 'REJECTED' (if clearly another person).
4. Preserving Investigative Value via Quarantine:
   - If an account has some plausible signals (e.g. handle stem match, but unconfirmed persona), NEVER eliminate it if it could provide useful clues. Mark it as 'SUSPECTED' so it is quarantined in the analyst drawer with all its context, confidence score, and rationale.
5. Secondary Persona & Common Alias Quarantine Rule:
   - NEVER mark an account as 'VERIFIED' if it was discovered solely via a secondary in-game nickname, persona stem (e.g. a Steam persona display name), or single first name without direct email binding, commit author signature, or full multi-token legal name match!
   - On massive platforms (Roblox, Chess.com, Keybase, Pastebin, Linktree, Twitter), single dictionary words and short nicknames have astronomical vanity collision rates with strangers. Mark them strictly as 'SUSPECTED' (quarantined) or 'REJECTED'.
6. For each candidate (by id), assign:
   - "VERIFIED": Conclusively tied primary or alt account with explicit ground-truth binding (email, commit signature, portfolio outbound link, or full legal name + location/company).
   - "SUSPECTED": Plausible candidate or namesake that lacks conclusive tie; quarantined in drawer.
   - "REJECTED": Distinct stranger, corporate entity collision, or conflicting identity.

Return ONLY a valid JSON object matching this schema:
{{
  "evaluations": [
    {{
      "id": str,
      "status": "VERIFIED" | "SUSPECTED" | "REJECTED",
      "confidence": float,
      "tie_badge": str,
      "reasoning": str
    }}
  ]
}}"""
            sys_instruct = "You are an elite OSINT intelligence analyst specializing in person disambiguation, multi-account analysis, and false positive elimination. Return strictly valid JSON."
            
            res = call_groq_api(
                prompt=prompt,
                system_instruction=sys_instruct,
                api_key=api_key,
                model="openai/gpt-oss-120b",
                response_json=True,
                max_tokens=1800
            )
            if res and res.get("success") and res.get("text"):
                body = json.loads(res["text"])
                for ev in body.get("evaluations", []):
                    if isinstance(ev, dict) and ev.get("id"):
                        ai_evaluations[ev["id"]] = ev
        except Exception as e:
            print(f"[!] AI Correlator error: {e}")

    # Process results with resilient fallback
    verified_res = list(direct_verified)
    suspected_res = []
    rejected_res = []

    t_norm_name = normalize_string(target_name)
    t_name_tokens = set(t_norm_name.split()) if t_norm_name else set()
    t_handles_norm = set(h.lower() for h in target_handles)

    target_info_blob = json.dumps(target_info).lower()
    t_raw_gender = str(target_info.get("gender") or target_info.get("perceived_gender") or "").lower().strip()
    if t_raw_gender in ["male", "female"]:
        target_gender = t_raw_gender
    elif any(p in target_info_blob for p in ["he/him", "(he/him)", '"male"', " male ", " guy ", " man ", "he is"]):
        target_gender = "male"
    elif any(p in target_info_blob for p in ["she/her", "(she/her)", '"female"', " female ", " woman ", " girl ", "she is"]):
        target_gender = "female"
    else:
        target_gender = "unknown"

    target_is_male = target_gender == "male"
    target_is_female = target_gender == "female"
    she_indicators = ["she/her", "she / her", "her/she", "(she/her)", "she/they", "woman", "actress", "mother", "wife", "girl"]
    he_indicators = ["he/him", "he / him", "him/he", "(he/him)", "he/they", "actor", "father", "husband", "guy", "boy"]

    for c in to_evaluate:
        cid = c.get("_cid")
        ev = ai_evaluations.get(cid)

        cand_handle_clean = (c.get("handle") or "").strip().lower()
        cand_prov = str(c.get("source") or c.get("provenance") or "").lower()
        cand_disp = normalize_string(c.get("name") or c.get("real_name") or "")
        cand_tokens = set(cand_disp.split()) if cand_disp else set()
        has_name_corroboration = (len(t_name_tokens & cand_tokens) >= 2) if len(t_name_tokens) >= 2 else False
        cand_url = str(c.get("url") or c.get("profile_url") or "").lower()
        is_auth_dev = any((cand_handle_clean and cand_handle_clean == ah.lower()) or (ah.lower() in cand_url) for ah in authenticated_handles if ah)
        is_portfolio_link = any(k in cand_prov or k in cand_url for k in ["portfolio", "wix", "jouwweb", "carrd", "github.io"])
        is_secondary_persona = bool(
            ("persona" in cand_prov or "alias" in cand_prov) or 
            (bool(cand_handle_clean) and (
                len(cand_handle_clean) <= 4 or
                (cand_handle_clean in t_name_tokens and len(t_name_tokens) >= 2)
            ))
        )

        if ev and ev.get("status"):
            status = ev["status"].strip().upper()
            conf = float(ev.get("confidence", 0.70))
            reasoning = ev.get("reasoning", "")
            badge = ev.get("tie_badge") or ("[TIED: AI VERIFIED]" if status == "VERIFIED" else "[QUARANTINED: AMBIGUOUS]")

            # EVIDENTIARY GUARDRAIL 1: Override hallucinated "VERIFIED" for secondary persona stems
            if status == "VERIFIED" and is_secondary_persona and not has_name_corroboration and not is_auth_dev and not is_portfolio_link and not c.get("is_email_bound"):
                status = "SUSPECTED"
                conf = min(0.65, conf)
                badge = "[QUARANTINED: COMMON ALIAS]"
                reasoning = f"Candidate account matching secondary persona '@{c.get('handle')}'. Common alias without direct email or full-name binding; quarantined in candidate ledger."

            # EVIDENTIARY GUARDRAIL 2: Override hallucinated "VERIFIED" for Given Name Collisions (e.g. John Zwaan vs Jordin Zwaan)
            if status == "VERIFIED" and len(t_name_tokens) >= 2 and cand_tokens and len(cand_tokens) >= 2:
                t_words = [w for w in t_norm_name.split() if len(w) >= 2]
                c_words = [w for w in cand_disp.split() if len(w) >= 2]
                if len(t_words) >= 2 and len(c_words) >= 2 and t_words[-1] == c_words[-1]:
                    t_first = t_words[0]
                    c_first = c_words[0]
                    if c_first != t_first and not (c_first.startswith(t_first) or t_first.startswith(c_first)):
                        status = "SUSPECTED"
                        conf = min(0.55, conf)
                        badge = "[QUARANTINED: GIVEN NAME CONFLICT]"
                        reasoning = f"Conflicting given name ('{c_first.title()}' vs target '{t_first.title()}'). Quarantined as suspected namesake/relative."

            # EVIDENTIARY GUARDRAIL 3: Demographic & Pronoun Non-Contradiction Check
            cand_bio_low = (str(c.get("context") or "") + " " + str(c.get("bio") or "") + " " + str(c.get("context_notes") or "")).lower()

            if status == "VERIFIED" and target_is_male and any(ind in cand_bio_low for ind in she_indicators):
                status = "SUSPECTED"
                conf = min(0.50, conf)
                badge = "[QUARANTINED: PRONOUN CONFLICT]"
                reasoning = "Demographic contradiction: profile bio states 'she/her', conflicting with male target identity."
            elif status == "VERIFIED" and target_is_female and any(ind in cand_bio_low for ind in he_indicators):
                status = "SUSPECTED"
                conf = min(0.50, conf)
                badge = "[QUARANTINED: PRONOUN CONFLICT]"
                reasoning = "Demographic contradiction: profile bio states 'he/him', conflicting with female target identity."

            c["confidence"] = conf
            c["tie_badge"] = badge
            if reasoning:
                c["context"] = f"{reasoning} ({badge})"

            if status == "VERIFIED":
                c["is_verified"] = True
                c["is_suspected"] = False
                c["tie_type"] = "AI_VERIFIED_CORROBORATION"
                verified_res.append(c)
            elif status == "SUSPECTED":
                c["is_verified"] = False
                c["is_suspected"] = True
                c["tie_type"] = "UNCORROBORATED_HANDLE_CANDIDATE"
                suspected_res.append(c)
            else:
                c["is_verified"] = False
                c["is_rejected"] = True
                c["tie_type"] = "REJECTED_IDENTITY_CONFLICT"
                rejected_res.append(c)
        else:
            # Intelligent neutral fallback if AI evaluation was unavailable
            cand_handle = (c.get("handle") or "").lower().strip()
            cand_name = normalize_string(c.get("name") or c.get("real_name") or "")
            cand_tokens = set(cand_name.split()) if cand_name else set()

            is_exact_handle = cand_handle in t_handles_norm if cand_handle else False
            is_name_match = len(t_name_tokens & cand_tokens) >= 2 if len(t_name_tokens) >= 2 else False

            # Check if candidate handle is merely a single given name or surname from target_name
            is_single_name_handle = False
            if cand_handle and t_name_tokens and len(t_name_tokens) >= 2:
                if cand_handle in t_name_tokens:
                    is_single_name_handle = True

            cand_bio_low = (str(c.get("context") or "") + " " + str(c.get("bio") or "") + " " + str(c.get("context_notes") or "")).lower()
            has_pronoun_conflict = (target_is_male and any(ind in cand_bio_low for ind in she_indicators)) or (target_is_female and any(ind in cand_bio_low for ind in he_indicators))

            t_words = [w for w in t_norm_name.split() if len(w) >= 2]
            c_words = [w for w in cand_name.split() if len(w) >= 2]
            has_given_conflict = False
            if len(t_words) >= 2 and len(c_words) >= 2 and t_words[-1] == c_words[-1]:
                t_first = t_words[0]
                c_first = c_words[0]
                if c_first != t_first and not (c_first.startswith(t_first) or t_first.startswith(c_first)):
                    has_given_conflict = True

            if has_pronoun_conflict or has_given_conflict:
                c["is_verified"] = False
                c["is_suspected"] = True
                c["confidence"] = 0.50
                c["tie_badge"] = "[QUARANTINED: CONFLICT DETECTED]"
                c["tie_type"] = "UNCORROBORATED_HANDLE_CANDIDATE"
                c["context"] = f"Candidate account probe for '{cand_handle or cand_name}'. Quarantined due to demographic/name conflict."
                suspected_res.append(c)
            elif is_name_match:
                c["is_verified"] = True
                c["is_suspected"] = False
                c["confidence"] = 0.88
                c["tie_badge"] = "[TIED: CORROBORATED]"
                c["tie_type"] = "OFFLINE_FALLBACK_CORROBORATION"
                verified_res.append(c)
            elif is_exact_handle and not is_single_name_handle and len(cand_handle) >= 5:
                c["is_verified"] = True
                c["is_suspected"] = False
                c["confidence"] = 0.85
                c["tie_badge"] = "[TIED: CORROBORATED]"
                c["tie_type"] = "OFFLINE_FALLBACK_CORROBORATION"
                verified_res.append(c)
            elif is_exact_handle:
                # Single given name / surname handle or unconfirmed handle: quarantine in SUSPECTED
                c["is_verified"] = False
                c["is_suspected"] = True
                c["confidence"] = 0.45
                c["tie_badge"] = "[CANDIDATE: UNCORROBORATED]"
                c["tie_type"] = "UNCORROBORATED_HANDLE_CANDIDATE"
                c["context"] = f"Candidate handle probe for '@{cand_handle}'. Quarantined pending corroboration."
                suspected_res.append(c)
            else:
                c["is_verified"] = False
                c["is_rejected"] = True
                rejected_res.append(c)

    return (verified_res, suspected_res, rejected_res)
