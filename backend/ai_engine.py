"""
BreachSpillover AI Threat Intelligence Engine
Provides zero-dependency high-speed LLM integration via Groq (Meta Llama 3.3 70B)
and Google Gemini Flash REST APIs, with an intelligent offline heuristic fallback.
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent

def load_dotenv(dotenv_path: Optional[Path] = None) -> None:
    """
    Zero-dependency .env loader. Loads key=value pairs from the project root .env into os.environ.
    """
    if dotenv_path is None:
        dotenv_path = BASE_DIR / ".env"
    if not dotenv_path.is_file():
        return
    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    if key and (key not in os.environ or not os.environ[key]):
                        os.environ[key] = val
    except Exception:
        pass

# Automatically load environment variables on import
load_dotenv()

def resolve_api_key(provider: str = "groq", explicit_key: Optional[str] = None) -> str:
    """
    Resolves the appropriate API key from:
    1. Explicit key passed via UI / request
    2. Hot-reloaded .env file from project root
    3. os.environ environment variables
    """
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    load_dotenv()
    prov = (provider or "groq").lower().strip()
    if prov == "gemini":
        return os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GROQ_API_KEY", "").strip()
    return os.getenv("GROQ_API_KEY", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()

USER_AGENT = "BreachSpillover-AI/1.0"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GEMINI_DEFAULT_MODEL = "gemini-1.5-flash"


def call_groq_api(
    prompt: str,
    system_instruction: str,
    api_key: str,
    model: str = GROQ_DEFAULT_MODEL,
    temperature: float = 0.2,
    response_json: bool = False
) -> Dict[str, Any]:
    """
    Direct REST caller for Groq's high-speed inference engine (300-500 tok/sec).
    Automatically handles model fallback if a requested model is deprecated or inaccessible.
    Uses standard Python urllib with zero third-party dependencies.
    """
    clean_key = (api_key or "").strip()
    if not clean_key:
        raise ValueError("Groq API key is required.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {clean_key}",
        "User-Agent": USER_AGENT
    }

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]

    candidate_models = [model]
    for m in ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "groq/compound"]:
        if m not in candidate_models:
            candidate_models.append(m)

    last_error = "Unknown error"
    for candidate in candidate_models:
        payload: Dict[str, Any] = {
            "model": candidate,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(GROQ_API_URL, data=req_data, headers=headers, method="POST")

        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                elapsed = time.time() - start_time
                if resp.status == 200:
                    body = json.loads(resp.read().decode("utf-8"))
                    choice = body.get("choices", [{}])[0]
                    text = choice.get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "text": text,
                        "latency_seconds": round(elapsed, 2),
                        "model": candidate,
                        "provider": "groq"
                    }
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_msg)
                last_error = err_json.get("error", {}).get("message", err_msg)
            except Exception:
                last_error = err_msg or str(e)

            # If model is deprecated (400) or missing (404), try next candidate model
            if e.code in (400, 404) and ("decommission" in last_error.lower() or "not exist" in last_error.lower() or "access" in last_error.lower()):
                continue
            return {"success": False, "error": f"Groq API Error ({e.code}): {last_error}"}
        except Exception as e:
            return {"success": False, "error": f"Connection error to Groq: {str(e)}"}

    return {"success": False, "error": f"Groq API Error: {last_error}"}


def call_gemini_api(
    prompt: str,
    system_instruction: str,
    api_key: str,
    model: str = GEMINI_DEFAULT_MODEL,
    temperature: float = 0.2
) -> Dict[str, Any]:
    """
    Direct REST caller for Google Gemini REST API.
    Uses standard Python urllib with zero third-party dependencies.
    """
    clean_key = (api_key or "").strip()
    if not clean_key:
        raise ValueError("Google Gemini API key is required.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={clean_key}"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"System Context: {system_instruction}\n\nUser Request: {prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 2048
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            elapsed = time.time() - start_time
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                candidates = body.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                    return {
                        "success": True,
                        "text": text,
                        "latency_seconds": round(elapsed, 2),
                        "model": model,
                        "provider": "gemini"
                    }
                return {"success": False, "error": "Gemini returned empty response candidate."}
            return {"success": False, "error": f"Gemini HTTP {resp.status}"}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        return {"success": False, "error": f"Gemini API Error ({e.code}): {err_msg}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error to Gemini: {str(e)}"}


def test_ai_connection(api_key: str, provider: str = "groq") -> Dict[str, Any]:
    """
    Fast 1-token connection probe to validate an API key and measure latency.
    """
    prov = (provider or "groq").lower().strip()
    if prov == "gemini":
        return call_gemini_api(
            prompt="Respond with 'PONG'",
            system_instruction="You are a health probe. Reply with PONG.",
            api_key=api_key
        )
    else:
        return call_groq_api(
            prompt="Respond with 'PONG'",
            system_instruction="You are a health probe. Reply with PONG.",
            api_key=api_key,
            model=GROQ_DEFAULT_MODEL
        )


def build_target_forensic_context(scan_data: Dict[str, Any]) -> str:
    """
    Distills scan data into an information-dense, structured forensic context
    for LLM reasoning.
    """
    emp = scan_data.get("employee", {})
    score = scan_data.get("spillover_score", {})
    leaks = scan_data.get("leaks", [])
    creds = scan_data.get("credentials", [])
    pivots = scan_data.get("pivots", [])
    foots = scan_data.get("physical_footprints", [])
    rels = scan_data.get("relatives", [])
    ev = scan_data.get("email_verification", {})

    lines = [
        f"TARGET EMAIL: {emp.get('corporate_email')}",
        f"IDENTIFIED REAL NAME: {emp.get('full_name')}",
        f"JOB TITLE / ROLE: {emp.get('job_title')}",
        f"DEPARTMENT / ORG: {emp.get('department')}",
        f"OVERALL SPILLOVER SCORE: {score.get('score')}/100 ({score.get('level')} RISK)",
        f"EMAIL SECURITY POSTURE: {ev.get('status')} • Provider: {ev.get('provider_type') or ev.get('email_security', {}).get('mail_provider', 'N/A')}",
        "",
        "--- EXFILTRATED LEAKS & MALWARE ---"
    ]

    if not leaks:
        lines.append("No database leaks or infostealer compromises detected.")
    else:
        for l in leaks:
            lines.append(f"- Leak: {l.get('leak_name')} ({l.get('leak_type')}) • Severity: {l.get('severity')} • Date: {l.get('breach_date')} • Malware: {l.get('malware_family', 'N/A')} • Data: {l.get('exposed_data')}")

    lines.append("\n--- COMPROMISED CREDENTIALS ---")
    if not creds:
        lines.append("No credentials exfiltrated.")
    else:
        for c in creds:
            lines.append(f"- Service: {c.get('domain_compromised')} • Plaintext: {c.get('plaintext_password') or 'HASHED'} • Pattern: {c.get('password_pattern')} • Corporate Policy Match: {c.get('is_corporate_password_match')}")

    persona_pivots = [p for p in pivots if p.get("pivot_type") == "PERSONA_PIVOT"]
    if persona_pivots:
        lines.append("\n--- DISCOVERED CROSS-PLATFORM ALIASES & RECURSIVE PERSONA PIVOTS ---")
        for pp in persona_pivots:
            lines.append(f"- {pp.get('pivot_value')} (Confidence: {pp.get('confidence_score')}) — {pp.get('context_note')}")

    lines.append("\n--- CORROBORATED & SUSPECTED PLATFORM PIVOTS ---")
    if not pivots:
        lines.append("No pivots found.")
    else:
        for p in pivots:
            if p.get("pivot_type") == "PERSONA_PIVOT":
                continue
            p_type = p.get("pivot_type")
            p_val = p.get("pivot_value")
            c_note = p.get("context_note")
            conf = p.get("confidence_score")
            lines.append(f"- [{p_type}] {p_val} (Confidence: {conf}) — {c_note}")

    lines.append("\n--- GEOSPATIAL & RESIDENTIAL FOOTPRINTS ---")
    if not foots:
        lines.append("No residential addresses mapped.")
    else:
        for f in foots:
            lines.append(f"- Address: {f.get('address_line')}, {f.get('city')}, {f.get('country')} (Exposure: {f.get('exposure_type')})")

    lines.append("\n--- HOUSEHOLD RELATIVES & CO-HABITANTS ---")
    if not rels:
        lines.append("No household relatives detected.")
    else:
        for r in rels:
            lines.append(f"- Cohabitant: {r.get('full_name')} ({r.get('relationship')}) • Phone: {r.get('contact_phone')} • Social Eng Risk: {r.get('social_engineering_risk')}")

    return "\n".join(lines)


SYSTEM_PROMPT_DOSSIER = """You are BreachSpillover AI, an elite Cyber Threat Intelligence (CTI) & OSINT forensic analyst.
Your mission is to analyze digital footprint data for a target identity and synthesize a structured, intelligence-grade Threat Dossier.

You must return valid, parseable JSON strictly conforming to this exact JSON schema:
{
  "executive_summary": "High-level forensic synthesis of who this person is, their real-world identity, company/institution, and overall compromise posture (2-3 crisp paragraphs).",
  "threat_level_verdict": "CRITICAL / HIGH / MODERATE / LOW with a 1-sentence analytical justification.",
  "persona_disambiguation": [
    {
      "platform": "Platform Name (e.g. Steam, Reddit, Chess.com, GitHub)",
      "handle_or_identifier": "@username or identifier",
      "status": "VERIFIED_AUTHENTIC / SUSPECTED_ALIAS / UNLIKELY_COLLISION",
      "probability_score": 0.85,
      "reasoning": "Explicit OSINT evidence justifying why this account matches or does not match the target's verified ground truth."
    }
  ],
  "adversary_attack_simulation": {
    "spear_phishing_pretext": "Specific, highly targeted spear-phishing pretext an APT or social engineer would craft using the target's real employer, university, or code projects.",
    "credential_stuffing_blast_radius": "Analysis of password reuse blast radius against corporate gateways, SSO, and private accounts.",
    "household_social_engineering_vector": "How an adversary could exploit cohabitants or residential data for vishing or physical access."
  },
  "credential_mutation_analysis": {
    "base_pattern_detected": "e.g. Word+Year+Symbol (Sarpsborg2022!) or None",
    "mutation_risk_score": 80,
    "mutation_risk_verdict": "HIGH / MODERATE / LOW with analytical justification of predictability",
    "corporate_cross_reuse_assessment": "Specific risk of this pattern crossing over to corporate SSO, VPN, or email",
    "defensive_hardening_guidance": "Concrete actionable password hygiene and MFA controls to stop credential stuffing"
  },
  "prioritized_remediations": [
    "1. Immediate tactical containment action.",
    "2. Credential hygiene action.",
    "3. OSINT/Privacy de-listing action."
  ]
}
Analyze persona evolution, alias history, and recursive cross-platform pivots (e.g. usernames shifting across platforms, gaming nicknames such as Steam personas like 'Poes', bio mentions, or alternate handles).
Explicitly detail in the executive_summary and persona_disambiguation how these aliases connect to the target identity.
Maintain rigorous professional terminology (APT, OSINT, CTI, credential stuffing, pivot analysis). Avoid generic boilerplate."""


def generate_heuristic_fallback_dossier(scan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic rule-based intelligence synthesizer that operates 100% offline
    without requiring external API keys.
    """
    emp = scan_data.get("employee", {})
    email = emp.get("corporate_email", "")
    full_name = emp.get("full_name", "")
    has_name = bool(full_name and full_name != "Target User" and not full_name.lower().startswith("webmail"))
    display_name = full_name if has_name else email
    job = emp.get("job_title", "Individual")
    dept = emp.get("department", "Personal Account")
    score_obj = scan_data.get("spillover_score", {})
    score = score_obj.get("score", 0)
    level = score_obj.get("level", "MODERATE")

    leaks = scan_data.get("leaks", [])
    creds = scan_data.get("credentials", [])
    pivots = scan_data.get("pivots", [])
    foots = scan_data.get("physical_footprints", [])
    rels = scan_data.get("relatives", [])

    # Extract platforms from pivots
    platforms_detected = []
    persona_list = []
    for p in pivots:
        pval = str(p.get("pivot_value", ""))
        ptype = str(p.get("pivot_type", ""))
        cnote = str(p.get("context_note", ""))
        conf = float(p.get("confidence_score") or 0.85)

        if ":" in pval:
            plat = pval.split(":")[0].strip()
            handle = pval.split(":")[-1].strip()
        else:
            plat = ptype.replace("ACCOUNT", "").replace("_", " ").title().strip()
            handle = pval

        platforms_detected.append(plat)
        status = "VERIFIED_AUTHENTIC" if conf >= 0.85 else "SUSPECTED_ALIAS"
        persona_list.append({
            "platform": plat,
            "handle_or_identifier": handle,
            "status": status,
            "probability_score": conf,
            "reasoning": cnote or f"Indexed during multi-platform OSINT enumeration with {int(conf*100)}% corroboration confidence."
        })

    # Summary synthesis
    summary_parts = []
    if has_name:
        summary_parts.append(
            f"Target has been definitively resolved as {display_name} ({email}). "
            f"Ground-truth correlation links this identity to developer artifacts and online service footprints."
        )
    else:
        summary_parts.append(
            f"Target identifier {email} presents a pseudonymous profile without an explicit public name in initial registration headers. "
            f"Multi-hop pivoting was deployed to isolate developer commits and authentication fingerprints."
        )

    if leaks or creds:
        stealers = [l for l in leaks if l.get("leak_type") == "INFOSTEALER"]
        if stealers:
            summary_parts.append(
                f"CRITICAL COMPROMISE: Target appears in active infostealer malware exfiltrations ({', '.join(s.get('malware_family', 'Stealer') for s in stealers)}), "
                f"indicating complete local endpoint compromise where browser session cookies and passwords were harvested."
            )
        else:
            summary_parts.append(
                f"Credential exposure identified across {len(leaks)} database disclosures. "
                f"{len(creds)} exfiltrated credential records were recovered with verifiable password patterns."
            )
    else:
        summary_parts.append(
            "Zero credential compromises or infostealer malware footprints were identified in active threat archives. "
            "Exposure surface is currently confined to open-web digital breadcrumbs."
        )

    if foots or rels:
        summary_parts.append(
            f"Geospatial intelligence established residential presence in {', '.join(f.get('city', 'Location') for f in foots)} "
            f"with {len(rels)} correlated household contacts, introducing physical and social engineering attack vectors."
        )

    persona_pivots = [p for p in pivots if p.get("pivot_type") == "PERSONA_PIVOT"]
    if persona_pivots:
        alias_names = [p.get("pivot_value", "").replace("Discovered Alias: ", "").strip() for p in persona_pivots]
        summary_parts.append(
            f"Recursive OSINT pivoting resolved alternate candidate personas: {', '.join(alias_names)}, "
            f"uncovering active cross-platform identity transitions across gaming and developer networks."
        )

    # Attack simulation
    spear_phish = (
        f"Adversary targeting {display_name} would spoof a communication from {dept} or a software dependency update "
        f"referencing their verified online profile on {platforms_detected[0] if platforms_detected else 'Git'}. "
        f"Lure would exploit familiar developer tools or administrative account resets."
    )
    stuffing = (
        f"Exfiltrated password patterns show reuse risk across corporate login portals and email infrastructure. "
        f"Automated credential stuffing attacks against corporate VPN/SSO portals pose immediate risk if passwords match corporate policy."
    )
    household = (
        f"Identified cohabitants ({', '.join(r.get('full_name', 'Contact') for r in rels) if rels else 'residential records'}) "
        f"provide an indirect lateral entrypoint via telephone vishing or spear-phishing posing as utility, courier, or emergency contacts."
    )

    remediations = [
        "Enforce immediate password revocation across all corporate and personal accounts with mandatory hardware FIDO2/MFA.",
        "Perform full malware triage and OS reinstall on any endpoint suspected of infostealer compromise.",
        "Submit privacy opt-out / de-listing requests to public directories (e.g. 1881.no) to suppress physical and mobile telemetry."
    ]

    # Heuristic credential mutation analysis
    mutation_score = 45
    mutation_pattern = "Standard Word + Year / Symbol Mutation"
    if creds:
        c0 = creds[0]
        p_plain = c0.get("plaintext_password") or ""
        p_pat = c0.get("password_pattern") or ""
        if p_plain:
            mutation_pattern = f"Observed Pattern: {p_pat or 'Word+Number'}"
            mutation_score = 85 if c0.get("is_corporate_password_match") else 70
        else:
            mutation_pattern = "Cryptographic Hash Exposed (Reverse Dictionary Target)"
            mutation_score = 60

    mutation_analysis = {
        "base_pattern_detected": mutation_pattern,
        "mutation_risk_score": mutation_score,
        "mutation_risk_verdict": f"{'HIGH' if mutation_score >= 70 else 'MODERATE'} — Predictable character substitution and year-increment rolling elevates lateral attack feasibility.",
        "corporate_cross_reuse_assessment": "Reused root passwords across personal and enterprise accounts permit automated dictionary variations against corporate VPN gateways.",
        "defensive_hardening_guidance": "Mandate FIDO2/WebAuthn phishing-resistant MFA, enforce 16+ character non-dictionary passphrases, and invalidate all existing active sessions."
    }

    return {
        "executive_summary": " ".join(summary_parts),
        "threat_level_verdict": f"{level} RISK — Threat score evaluated at {score}/100 based on multi-vector exposure indexing.",
        "persona_disambiguation": persona_list[:8],
        "adversary_attack_simulation": {
            "spear_phishing_pretext": spear_phish,
            "credential_stuffing_blast_radius": stuffing,
            "household_social_engineering_vector": household
        },
        "credential_mutation_analysis": mutation_analysis,
        "prioritized_remediations": remediations,
        "is_ai_generated": False,
        "provider": "deterministic_heuristic",
        "engine_label": "Deterministic CTI Heuristic Synthesizer (Offline Mode)"
    }


# Zero-redundancy In-Memory Dossier Cache (1-hour TTL)
_DOSSIER_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

def get_cached_dossier(email: str, max_age_seconds: float = 3600.0) -> Optional[Dict[str, Any]]:
    key = (email or "").lower().strip()
    if key in _DOSSIER_CACHE:
        ts, data = _DOSSIER_CACHE[key]
        if time.time() - ts < max_age_seconds:
            cached = dict(data)
            cached["cached"] = True
            return cached
    return None

def set_cached_dossier(email: str, dossier: Dict[str, Any]) -> None:
    key = (email or "").lower().strip()
    if key:
        _DOSSIER_CACHE[key] = (time.time(), dossier)


def generate_ai_threat_dossier(
    scan_data: Dict[str, Any],
    api_key: Optional[str] = None,
    provider: str = "groq",
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Main entrypoint for generating an intelligence-grade AI threat dossier.
    Checks zero-cost in-memory cache first to eliminate redundant API requests.
    Attempts live LLM query via Groq (or Gemini) if API key is provided,
    falling back cleanly to the heuristic synthesizer.
    """
    emp = scan_data.get("employee", {})
    email = emp.get("corporate_email", "")

    if not force_refresh and email:
        cached = get_cached_dossier(email)
        if cached:
            return cached

    prov = (provider or "groq").lower().strip()
    clean_key = resolve_api_key(prov, api_key)

    if not clean_key:
        fallback = generate_heuristic_fallback_dossier(scan_data)
        fallback["notice"] = "Running in offline deterministic mode. Configure a free Groq or Gemini API key in [⚙️ AI SETTINGS] to unlock full LLM reasoning."
        if email:
            set_cached_dossier(email, fallback)
        return fallback

    forensic_text = build_target_forensic_context(scan_data)
    prompt = (
        "Generate a comprehensive, analytical Threat Dossier for the following scanned target forensic data.\n\n"
        f"{forensic_text}\n\n"
        "Return ONLY the requested JSON object matching the schema."
    )

    try:
        if prov == "gemini":
            res = call_gemini_api(prompt=prompt, system_instruction=SYSTEM_PROMPT_DOSSIER, api_key=clean_key)
        else:
            res = call_groq_api(prompt=prompt, system_instruction=SYSTEM_PROMPT_DOSSIER, api_key=clean_key, response_json=True)

        if res.get("success") and res.get("text"):
            raw_text = res["text"].strip()
            # Clean markdown wrappers if present
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
            parsed["is_ai_generated"] = True
            parsed["provider"] = res.get("provider", prov)
            parsed["model"] = res.get("model", GROQ_DEFAULT_MODEL)
            parsed["latency_seconds"] = res.get("latency_seconds")
            parsed["engine_label"] = f"{res.get('provider', prov).upper()} ({res.get('model')}) • Generated in {res.get('latency_seconds')}s"
            if email:
                set_cached_dossier(email, parsed)
            return parsed
        else:
            # Fall back to heuristic with error note
            fallback = generate_heuristic_fallback_dossier(scan_data)
            fallback["notice"] = f"AI request failed ({res.get('error')}). Reverted to deterministic CTI heuristic dossier."
            if email:
                set_cached_dossier(email, fallback)
            return fallback

    except Exception as e:
        fallback = generate_heuristic_fallback_dossier(scan_data)
        fallback["notice"] = f"AI parsing error ({str(e)}). Reverted to deterministic CTI heuristic dossier."
        if email:
            set_cached_dossier(email, fallback)
        return fallback


def ai_copilot_chat(
    user_query: str,
    scan_data: Dict[str, Any],
    history: Optional[List[Dict[str, str]]] = None,
    api_key: Optional[str] = None,
    provider: str = "groq"
) -> Dict[str, Any]:
    """
    Powers the interactive Investigator Copilot chat drawer.
    Answers real-time questions about the target's compromise posture, OPSEC de-listing,
    or attack chains.
    """
    prov = (provider or "groq").lower().strip()
    clean_key = resolve_api_key(prov, api_key)

    forensic_text = build_target_forensic_context(scan_data)
    system_instruction = (
        "You are BreachSpillover Copilot, an expert OSINT and cybersecurity investigator assistant. "
        "You are assisting a security researcher or SOC analyst investigating the following target profile:\n\n"
        f"{forensic_text}\n\n"
        "Answer the investigator's question concisely, accurately, and professionally. "
        "Reference specific findings from the scan data (passwords, leaks, usernames, 1881 records, cities, relatives). "
        "Provide actionable, defensive, and OPSEC-focused advice. Use markdown for readability."
    )

    if not clean_key:
        # Smart offline heuristic responder
        q_low = (user_query or "").lower()
        emp = scan_data.get("employee", {})
        score = scan_data.get("spillover_score", {}).get("score", 0)

        if "password" in q_low or "cred" in q_low:
            creds = scan_data.get("credentials", [])
            reply = f"**Credential Analysis for {emp.get('corporate_email')}:**\n\n"
            if creds:
                reply += f"- **Exfiltrated Records:** Found {len(creds)} credential dump(s).\n"
                reply += f"- **Base Pattern:** `{creds[0].get('password_pattern')}`\n"
                reply += f"- **Corporate Policy Collision:** {creds[0].get('is_corporate_password_match')}\n\n"
                reply += "**Mitigation:** Immediately initiate an enterprise-wide password reset and audit SSO logins for anomalous geolocations."
            else:
                reply += "No passwords have been exfiltrated in tracked threat dumps. Keep MFA active."
        elif "1881" in q_low or "norway" in q_low or "phone" in q_low or "address" in q_low:
            reply = (
                "**Scandinavian Registry (1881.no) & Residential Footprint:**\n\n"
                "In Norway, Opplysningen 1881 publishes civilian numbers by default unless reserved in Brønnøysundregistrene.\n\n"
                "**Removal Procedure:**\n"
                "1. Log into **Vipps / Altinn** and update the National Population Register (Folkeregisteret) privacy reservation.\n"
                "2. Visit **1881.no/kontakt-oss** and submit a reservation request to purge mobile telephone and residential address indices."
            )
        elif "risk" in q_low or "score" in q_low:
            reply = (
                f"The target currently has an overall Spillover Risk Score of **{score}/100**.\n\n"
                "This score is calculated across 5 deterministic vectors: Infostealers, Credentials, Identity Pivots, Physical Footprints, and Household Social Engineering."
            )
        else:
            reply = (
                f"**BreachSpillover Copilot (Offline Mode):**\n\n"
                f"Target `{emp.get('corporate_email')}` is currently indexed with an exposure score of **{score}/100**.\n\n"
                "- **Resolved Identity:** " + (emp.get('full_name') or 'N/A') + "\n"
                f"- **Verified Leaks:** {len(scan_data.get('leaks', []))}\n"
                f"- **Correlated Pivots:** {len(scan_data.get('pivots', []))}\n\n"
                "*(Tip: To enable full conversational LLM reasoning, enter your free Groq or Gemini API key in [⚙️ AI SETTINGS].)*"
            )

        return {
            "success": True,
            "reply": reply,
            "provider": "deterministic_copilot",
            "model": "offline-cti-rules"
        }

    # Live LLM query
    if prov == "gemini":
        res = call_gemini_api(prompt=user_query, system_instruction=system_instruction, api_key=clean_key)
    else:
        res = call_groq_api(prompt=user_query, system_instruction=system_instruction, api_key=clean_key)

    if res.get("success") and res.get("text"):
        return {
            "success": True,
            "reply": res["text"],
            "provider": res.get("provider", prov),
            "model": res.get("model", GROQ_DEFAULT_MODEL),
            "latency_seconds": res.get("latency_seconds")
        }
    else:
        return {
            "success": False,
            "error": res.get("error", "Failed to query AI engine."),
            "reply": f"[ERROR] AI Copilot: {res.get('error', 'Unknown error')}. Please verify API key configuration in AI Settings."
        }
