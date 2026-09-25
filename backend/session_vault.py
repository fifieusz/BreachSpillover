"""
BreachSpillover - Session Vault & Cookie Manager
Manages platform session cookies (.env) for zero-token authenticated extractions.
Provides live session validity checks (LinkedIn li_at, APIs) and dynamic .env updates.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("BreachSpillover.SessionVault")

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

def reload_env():
    """Dynamically parses and loads .env without requiring a server restart."""
    if not ENV_PATH.exists():
        return
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ[k] = v
    except Exception as e:
        logger.warning(f"Error reading .env: {e}")

def update_env_variable(key: str, value: str):
    """Updates or adds an environment variable in .env and os.environ."""
    clean_val = value.strip().strip('"').strip("'")
    val_str = f'"{clean_val}"' if any(c in clean_val for c in [':', ' ', '#', '"']) else clean_val
    os.environ[key] = clean_val
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={val_str}\n")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"{key}={val_str}\n")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def get_linkedin_cookie_from_sources() -> Optional[str]:
    """Retrieves LinkedIn li_at cookie from .env, storage_state.json, or memory."""
    reload_env()
    for var in ["LINKEDIN_LI_AT", "LI_AT", "LINKEDIN_COOKIE"]:
        val = os.getenv(var, "").strip().strip('"').strip("'")
        if val and len(val) > 15:
            # Strip li_at= prefix if user pasted full header
            if "li_at=" in val:
                m = re.search(r'li_at=([^;,\s]+)', val)
                if m:
                    return m.group(1)
            return val
    # Fallback to browser session storage state
    storage_state = BASE_DIR / "data" / "browser_session" / "storage_state.json"
    if storage_state.exists():
        try:
            import json
            with open(storage_state, "r", encoding="utf-8") as f:
                d = json.load(f)
            for c in d.get("cookies", []):
                if c.get("name") == "li_at" and len(c.get("value", "")) > 15:
                    return c.get("value")
        except Exception:
            pass
    return None

def get_linkedin_jsessionid_from_sources() -> Optional[str]:
    """Retrieves LinkedIn JSESSIONID (CSRF token) from .env, storage_state.json, or memory."""
    reload_env()
    for var in ["LINKEDIN_JSESSIONID", "JSESSIONID"]:
        val = os.getenv(var, "").strip().strip('"').strip("'")
        if val:
            if "JSESSIONID=" in val:
                m = re.search(r'JSESSIONID="?([^;,\s"]+)"?', val)
                if m:
                    return m.group(1)
            return val
    storage_state = BASE_DIR / "data" / "browser_session" / "storage_state.json"
    if storage_state.exists():
        try:
            import json
            with open(storage_state, "r", encoding="utf-8") as f:
                d = json.load(f)
            for c in d.get("cookies", []):
                if c.get("name") == "JSESSIONID" and c.get("value"):
                    return c.get("value")
        except Exception:
            pass
    return None

def parse_linkedin_cookie_input(raw: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parses either a raw token, a key-value pair, or an entire HTTP Cookie header.
    Extracts li_at and JSESSIONID cleanly.
    """
    if not raw:
        return None, None
    raw = raw.strip()
    
    li_at = None
    jsessionid = None
    
    # 1. Look for li_at
    if "li_at=" in raw:
        m = re.search(r'li_at=([^;,\s]+)', raw)
        if m:
            li_at = m.group(1).strip('"').strip("'")
    elif len(raw) > 25 and not raw.startswith("ajax:"):
        li_at = raw.strip('"').strip("'")
        
    # 2. Look for JSESSIONID
    if "JSESSIONID=" in raw:
        m = re.search(r'JSESSIONID="?([^;,\s"]+)"?', raw)
        if m:
            jsessionid = m.group(1).strip('"').strip("'")
    elif raw.startswith("ajax:") or ('"' in raw and "ajax:" in raw):
        jsessionid = raw.strip('"').strip("'")
        
    return li_at, jsessionid

_cached_linkedin_status: Optional[Dict[str, Any]] = None

def get_cached_linkedin_status() -> Optional[Dict[str, Any]]:
    return _cached_linkedin_status

def verify_linkedin_cookie(cookie: Optional[str] = None, jsessionid: Optional[str] = None) -> Dict[str, Any]:
    """
    Tests whether a given or configured LinkedIn li_at and JSESSIONID pair is currently valid.
    Queries LinkedIn's internal Voyager API with browser TLS fingerprinting (curl_cffi).
    Caches the validation outcome for instantaneous status retrieval.
    """
    global _cached_linkedin_status
    
    # If cookie string contains both, parse it
    parsed_li, parsed_js = parse_linkedin_cookie_input(cookie or "")
    li_at = parsed_li or cookie or get_linkedin_cookie_from_sources()
    js_token = parsed_js or jsessionid or get_linkedin_jsessionid_from_sources()

    if not li_at or len(li_at) < 15:
        res = {
            "valid": False,
            "configured": False,
            "status": "missing",
            "message": "No LinkedIn session cookie configured."
        }
        _cached_linkedin_status = res
        return res

    # Clean cookie string
    if "li_at=" in li_at:
        m = re.search(r'li_at=([^;,\s]+)', li_at)
        if m:
            li_at = m.group(1)
    li_at = li_at.strip().strip('"').strip("'")

    masked = f"{li_at[:6]}...{li_at[-4:]}" if len(li_at) > 10 else "Present"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/vnd.linkedin.normalized+json+2.1",
        "x-restli-protocol-version": "2.0.0"
    }

    clean_js = js_token.strip('"').strip("'") if js_token else None
    had_placeholder_js = False

    # If the user left the example placeholder, do NOT send it as a fake CSRF token
    if clean_js and ("1234567890123456789" in clean_js or clean_js.lower() == "ajax:1234567890123456789"):
        had_placeholder_js = True
        clean_js = None

    if clean_js:
        headers["Cookie"] = f'li_at={li_at}; JSESSIONID="{clean_js}"'
        headers["csrf-token"] = clean_js
    else:
        # DO NOT send a dummy fake JSESSIONID as that causes LinkedIn to immediately revoke the session!
        headers["Cookie"] = f"li_at={li_at}"

    try:
        from curl_cffi import requests
        # Test 1: Voyager /me API
        resp = requests.get(
            "https://www.linkedin.com/voyager/api/me",
            headers=headers,
            impersonate="chrome124",
            allow_redirects=False,
            timeout=3.5
        )

        if resp.status_code == 200:
            try:
                data = resp.json()
                first_name = ""
                last_name = ""
                occ = ""
                for inc in data.get("included", []):
                    if inc.get("$type") == "com.linkedin.voyager.identity.shared.MiniProfile" or "firstName" in inc:
                        first_name = inc.get("firstName", "")
                        last_name = inc.get("lastName", "")
                        occ = inc.get("occupation", "")
                        break
                if not first_name:
                    mp = data.get("miniProfile", {}) or data.get("data", {}).get("miniProfile", {})
                    first_name = mp.get("firstName") or str(data.get("data", {}).get("plainId", data.get("plainId", "LinkedIn Member")))
                    last_name = mp.get("lastName", "")
                    occ = mp.get("occupation", "")
                full_name = f"{first_name} {last_name}".strip()
                res = {
                    "valid": True,
                    "configured": True,
                    "status": "good",
                    "masked": masked,
                    "account_name": full_name or "LinkedIn Member",
                    "headline": occ,
                    "status_code": 200,
                    "message": f"Session Active & Verified: {full_name or 'Member'}"
                }
                _cached_linkedin_status = res
                return res
            except Exception:
                res = {
                    "valid": True,
                    "configured": True,
                    "status": "good",
                    "masked": masked,
                    "account_name": "LinkedIn Member",
                    "status_code": 200,
                    "message": "Session Active & Verified (HTTP 200)"
                }
                _cached_linkedin_status = res
                return res

        if resp.status_code == 429:
            res = {
                "valid": False,
                "configured": True,
                "status": "problem",
                "masked": masked,
                "status_code": 429,
                "message": "LinkedIn Rate Limited (HTTP 429: Too Many Requests). The IP or session has temporarily exceeded LinkedIn's request threshold. Please wait a few minutes before retrying."
            }
            _cached_linkedin_status = res
            return res

        # If 302/401/403, check redirect target & headers
        loc = resp.headers.get("location", "")
        set_cookie = resp.headers.get("set-cookie", "")
        
        if "delete me" in set_cookie:
            msg = "LinkedIn invalidated this session token. "
            if not js_token:
                msg += "LinkedIn's Voyager API requires the matching JSESSIONID from your browser cookies to authorize requests without redirecting. Please provide both li_at and JSESSIONID."
            else:
                msg += "Please log into LinkedIn in your browser and copy fresh li_at and JSESSIONID values."
            res = {
                "valid": False,
                "configured": True,
                "status": "expired",
                "masked": masked,
                "status_code": resp.status_code,
                "message": msg
            }
            _cached_linkedin_status = res
            return res

        if (not clean_js or had_placeholder_js) and resp.status_code == 302:
            placeholder_note = " (Note: LINKEDIN_JSESSIONID in .env is currently set to the example placeholder 'ajax:1234567890123456789'. Please replace it with your real JSESSIONID from LinkedIn's browser cookies)." if had_placeholder_js else ""
            res = {
                "valid": False,
                "configured": True,
                "status": "problem",
                "masked": masked,
                "status_code": 302,
                "message": f"LinkedIn returned HTTP 302. Voyager API requires the matching 'JSESSIONID' (CSRF token) alongside 'li_at'. Please copy JSESSIONID from the same Cookies table in DevTools (e.g. ajax:...){placeholder_note}"
            }
            _cached_linkedin_status = res
            return res

        if "login" in loc or "authwall" in loc or "checkpoint" in loc or resp.status_code in [401, 403]:
            res = {
                "valid": False,
                "configured": True,
                "status": "expired",
                "masked": masked,
                "status_code": resp.status_code,
                "message": "Cookie Expired or Rejected by LinkedIn. Please paste fresh cookies."
            }
            _cached_linkedin_status = res
            return res

        res = {
            "valid": False,
            "configured": True,
            "status": "problem",
            "masked": masked,
            "status_code": resp.status_code,
            "message": f"LinkedIn returned HTTP {resp.status_code}."
        }
        _cached_linkedin_status = res
        return res

    except Exception as e:
        logger.warning(f"LinkedIn session verification failed: {e}")
        res = {
            "valid": False,
            "configured": True,
            "status": "error",
            "masked": masked,
            "error": str(e),
            "message": f"Network check error: {e}"
        }
        _cached_linkedin_status = res
        return res

def save_linkedin_cookie_to_env(cookie_str: str, jsessionid_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Saves LinkedIn session cookies (li_at and optionally JSESSIONID) into .env and runtime memory.
    Also verifies the new session immediately.
    """
    parsed_li, parsed_js = parse_linkedin_cookie_input(cookie_str)
    clean_cookie = parsed_li or cookie_str.strip().strip('"').strip("'")
    clean_js = parsed_js or (jsessionid_str.strip().strip('"').strip("'") if jsessionid_str else None)

    if "li_at=" in clean_cookie:
        m = re.search(r'li_at=([^;,\s]+)', clean_cookie)
        if m:
            clean_cookie = m.group(1)

    if not clean_cookie or len(clean_cookie) < 15:
        return {
            "success": False,
            "message": "Invalid cookie format. LinkedIn li_at is typically 100+ characters starting with 'AQED...'"
        }

    os.environ["LINKEDIN_LI_AT"] = clean_cookie
    if clean_js:
        os.environ["LINKEDIN_JSESSIONID"] = clean_js

    # Persist into .env file
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated_li = False
    updated_js = False
    new_lines = []
    for line in lines:
        if line.startswith("LINKEDIN_LI_AT="):
            new_lines.append(f"LINKEDIN_LI_AT={clean_cookie}\n")
            updated_li = True
        elif line.startswith("LINKEDIN_JSESSIONID="):
            if clean_js:
                new_lines.append(f'LINKEDIN_JSESSIONID="{clean_js}"\n')
                updated_js = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if not updated_li:
        new_lines.append(f"\n# LinkedIn Investigator Session Cookie (li_at)\nLINKEDIN_LI_AT={clean_cookie}\n")
    if clean_js and not updated_js:
        new_lines.append(f'LINKEDIN_JSESSIONID="{clean_js}"\n')

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Also synchronize directly into browser_session storage_state.json
    try:
        s_dir = BASE_DIR / "data" / "browser_session"
        s_dir.mkdir(parents=True, exist_ok=True)
        state_file = s_dir / "storage_state.json"
        existing_cookies = []
        if state_file.exists():
            try:
                import json
                with open(state_file, "r", encoding="utf-8") as sf:
                    existing_cookies = json.load(sf).get("cookies", [])
            except Exception:
                pass
        
        # Remove old li_at and JSESSIONID
        new_cookies = [c for c in existing_cookies if c.get("name") not in ("li_at", "JSESSIONID")]
        new_cookies.extend([
            {
                "name": "li_at",
                "value": clean_cookie,
                "domain": ".linkedin.com",
                "path": "/",
                "expires": -1,
                "httpOnly": True,
                "secure": True,
                "sameSite": "None"
            },
            {
                "name": "li_at",
                "value": clean_cookie,
                "domain": ".www.linkedin.com",
                "path": "/",
                "expires": -1,
                "httpOnly": True,
                "secure": True,
                "sameSite": "None"
            }
        ])
        if clean_js:
            new_cookies.extend([
                {
                    "name": "JSESSIONID",
                    "value": f'"{clean_js}"',
                    "domain": ".linkedin.com",
                    "path": "/",
                    "expires": -1,
                    "httpOnly": False,
                    "secure": True,
                    "sameSite": "None"
                },
                {
                    "name": "JSESSIONID",
                    "value": f'"{clean_js}"',
                    "domain": ".www.linkedin.com",
                    "path": "/",
                    "expires": -1,
                    "httpOnly": False,
                    "secure": True,
                    "sameSite": "None"
                }
            ])
        with open(state_file, "w", encoding="utf-8") as sf:
            json.dump({"cookies": new_cookies, "origins": []}, sf, indent=2)
    except Exception as e:
        logger.warning(f"Could not sync cookies to storage_state.json: {e}")

    # Perform immediate live validation
    ver_res = verify_linkedin_cookie(clean_cookie, clean_js)
    return {
        "success": True,
        "cookie_masked": f"{clean_cookie[:6]}...{clean_cookie[-4:]}",
        "jsessionid_present": bool(clean_js),
        "verification": ver_res,
        "message": "Successfully saved LinkedIn session credentials to .env and browser session!"
    }

def get_vault_summary(check_live: bool = False) -> Dict[str, Any]:
    """Returns a full summary of all configured sessions and keys in .env."""
    reload_env()

    # 1. LinkedIn
    li_cookie = get_linkedin_cookie_from_sources()
    li_jsession = get_linkedin_jsessionid_from_sources()
    li_masked = f"{li_cookie[:6]}...{li_cookie[-4:]}" if li_cookie else None

    global _cached_linkedin_status
    if check_live and li_cookie:
        verify_linkedin_cookie(li_cookie, li_jsession)

    li_valid = False
    li_status = "missing"
    li_account = None

    if not li_cookie:
        li_status = "missing"
        li_valid = False
    elif _cached_linkedin_status:
        li_valid = _cached_linkedin_status.get("valid", False)
        li_status = "good" if li_valid else (_cached_linkedin_status.get("status") or "problem")
        li_account = _cached_linkedin_status.get("account_name")
    else:
        # Check if local browser session is active
        try:
            from backend.browser_runner import is_browser_authenticated
            b_check = is_browser_authenticated()
            if b_check.get("authenticated"):
                li_valid = True
                li_status = "good"
                li_account = "Desktop Browser Active"
            else:
                li_status = "configured"
                li_valid = False
        except Exception:
            li_status = "configured"
            li_valid = False

    # 2. Universal Web Unblocker
    scraped_key = os.getenv("SCRAPEDO_API_KEY", "").strip() or os.getenv("SCRAPER_API_KEY", "").strip()
    unblocker_masked = f"{scraped_key[:4]}...{scraped_key[-4:]}" if len(scraped_key) > 8 else ("Configured" if scraped_key else None)

    # 3. AI Engine
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    ai_configured = bool(groq_key)

    # 4. HIBP
    hibp_key = os.getenv("HIBP_API_KEY", "").strip()
    hibp_configured = bool(hibp_key)

    # 5. GitHub Session
    gh_token = os.getenv("GITHUB_TOKEN", "").strip() or os.getenv("GITHUB_SESSION", "").strip()
    gh_masked = f"{gh_token[:4]}...{gh_token[-4:]}" if len(gh_token) > 8 else ("Configured" if gh_token else None)

    # Overall cookie health: if primary session cookie (LinkedIn) is valid -> "good", otherwise "problem"
    overall_status = "good" if li_valid else "problem"

    return {
        "overall_status": overall_status,
        "is_good": li_valid,
        "has_problem": not li_valid,
        "linkedin": {
            "configured": bool(li_cookie),
            "jsessionid_configured": bool(li_jsession),
            "valid": li_valid,
            "status": li_status,
            "masked": li_masked,
            "account_name": li_account,
            "env_key": "LINKEDIN_LI_AT"
        },
        "github": {
            "configured": bool(gh_token),
            "masked": gh_masked,
            "env_key": "GITHUB_TOKEN"
        },
        "unblocker": {
            "configured": bool(scraped_key),
            "masked": unblocker_masked,
            "provider": "Scrape.do / ScraperAPI" if scraped_key else None
        },
        "ai": {
            "configured": ai_configured,
            "provider": "Groq Llama 3.3 70B Versatile" if ai_configured else None
        },
        "hibp": {
            "configured": hibp_configured
        }
    }
