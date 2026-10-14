"""
BreachSpillover - Session Vault & Cookie Manager
Manages platform session cookies (.env) for zero-token authenticated extractions.
Provides live session validity checks (LinkedIn li_at, APIs) and dynamic .env updates.
"""

import os
import re
import time
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
        new_env = {}
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    new_env[k] = v
        for tracked in [
            "SCRAPEDO_API_KEY", "SCRAPER_API_KEY", "SCRAPE_DO_TOKEN", 
            "LINKEDIN_LI_AT", "LINKEDIN_JSESSIONID", "FACEBOOK_C_USER", "FACEBOOK_XS",
            "LEAKCHECK_API_KEY", "BREACHDIRECTORY_API_KEY", "DEHASHED_API_KEY", 
            "DEHASHED_EMAIL", "SNUSBASE_API_KEY", "HIBP_API_KEY", "INTELX_API_KEY", "HASHES_COM_API_KEY"
        ]:
            if tracked in new_env:
                os.environ[tracked] = new_env[tracked]
            elif tracked in os.environ:
                del os.environ[tracked]
        for k, v in new_env.items():
            os.environ[k] = v
    except Exception as e:
        logger.warning(f"Error reading .env: {e}")

def update_env_variable(key: str, value: str):
    """Updates or adds an environment variable in .env and os.environ."""
    global _cached_linkedin_status, _cached_facebook_status
    if "LINKEDIN" in key:
        _cached_linkedin_status = None
    elif "FACEBOOK" in key:
        _cached_facebook_status = None

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
_cached_linkedin_time: float = 0.0

def get_cached_linkedin_status() -> Optional[Dict[str, Any]]:
    return _cached_linkedin_status

def verify_linkedin_cookie(cookie: Optional[str] = None, jsessionid: Optional[str] = None) -> Dict[str, Any]:
    """
    Tests whether a given or configured LinkedIn li_at and JSESSIONID pair is currently valid.
    Queries LinkedIn's internal Voyager API with browser TLS fingerprinting (curl_cffi).
    Caches the validation outcome for instantaneous status retrieval.
    """
    global _cached_linkedin_status, _cached_linkedin_time
    
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
        _cached_linkedin_time = time.time()
        return res

    # Clean cookie string
    if "li_at=" in li_at:
        m = re.search(r'li_at=([^;,\s]+)', li_at)
        if m:
            li_at = m.group(1)
    li_at = li_at.strip().strip('"').strip("'")

    masked = f"{li_at[:6]}...{li_at[-4:]}" if len(li_at) > 10 else "Present"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        "Accept": "application/vnd.linkedin.normalized+json+2.1",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.linkedin.com/feed/",
        "Origin": "https://www.linkedin.com",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-li-lang": "en_US",
        "x-restli-protocol-version": "2.0.0"
    }

    clean_js = js_token.strip('"').strip("'") if js_token else None
    had_placeholder_js = False

    # If the user left the example placeholder, do NOT send it as a fake CSRF token
    if clean_js and ("1234567890123456789" in clean_js or clean_js.lower() == "ajax:1234567890123456789"):
        had_placeholder_js = True
        clean_js = None

    cookie_parts = [f"li_at={li_at}"]
    if clean_js:
        cookie_parts.append(f'JSESSIONID="{clean_js}"')
        headers["csrf-token"] = clean_js

    # Enrich with existing storage_state cookies (bcookie, bscookie, li_gc) to satisfy anti-bot device verification
    storage_state_path = BASE_DIR / "data" / "browser_session" / "storage_state.json"
    if storage_state_path.exists():
        try:
            import json
            with open(storage_state_path, "r", encoding="utf-8") as sf:
                s_data = json.load(sf)
            for c in s_data.get("cookies", []):
                c_name = c.get("name")
                c_val = c.get("value")
                if c_name in ("bcookie", "bscookie", "li_gc", "lidc", "liap") and c_val:
                    cookie_parts.append(f"{c_name}={c_val}")
        except Exception:
            pass

    headers["Cookie"] = "; ".join(cookie_parts)

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
                _cached_linkedin_time = time.time()
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
                _cached_linkedin_time = time.time()
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
            _cached_linkedin_time = time.time()
            return res

        # If 302/401/403, check redirect target & headers
        loc = resp.headers.get("location", "")
        set_cookie = resp.headers.get("set-cookie", "")
        
        # Test 2: Fallback feed verification if Voyager REST endpoint redirected
        if resp.status_code != 200 and "delete me" not in set_cookie:
            try:
                feed_resp = requests.get(
                    "https://www.linkedin.com/feed/",
                    headers={
                        "User-Agent": headers["User-Agent"],
                        "Cookie": headers["Cookie"],
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                    },
                    impersonate="chrome124",
                    allow_redirects=False,
                    timeout=3.5
                )
                feed_loc = feed_resp.headers.get("location", "").lower()
                if feed_resp.status_code == 200 or (feed_resp.status_code == 302 and "login" not in feed_loc and "authwall" not in feed_loc and "checkpoint" not in feed_loc):
                    res = {
                        "valid": True,
                        "configured": True,
                        "status": "good",
                        "masked": masked,
                        "account_name": "Active Member",
                        "status_code": 200,
                        "message": "Session Active & Verified"
                    }
                    _cached_linkedin_status = res
                    _cached_linkedin_time = time.time()
                    return res
            except Exception:
                pass

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
            _cached_linkedin_time = time.time()
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
            _cached_linkedin_time = time.time()
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
            _cached_linkedin_time = time.time()
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
        _cached_linkedin_time = time.time()
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
        new_cookies.append({
            "name": "li_at",
            "value": clean_cookie,
            "domain": ".linkedin.com",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        })
        if clean_js:
            new_cookies.append({
                "name": "JSESSIONID",
                "value": clean_js,
                "domain": ".linkedin.com",
                "path": "/",
                "expires": -1,
                "httpOnly": False,
                "secure": True,
                "sameSite": "None"
            })
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

def parse_facebook_cookie_input(user_raw: str, xs_raw: str = "") -> tuple[Optional[str], Optional[str]]:
    """
    Parses Facebook session inputs from individual values, key-value pairs, or full Cookie headers.
    Returns clean (c_user, xs) tuple.
    """
    combined = f"{user_raw or ''} {xs_raw or ''}".strip()
    if not combined:
        return None, None

    c_user = None
    xs = None

    # 1. Extract c_user
    m_user = re.search(r'(?:^|;\s*|\s+)c_user=([0-9]+)', combined)
    if m_user:
        c_user = m_user.group(1).strip()
    elif user_raw and user_raw.strip().strip('"').strip("'").isdigit():
        c_user = user_raw.strip().strip('"').strip("'")

    # 2. Extract xs
    m_xs = re.search(r'(?:^|;\s*|\s+)xs=([^;,\s]+)', combined)
    if m_xs:
        xs = m_xs.group(1).strip().strip('"').strip("'")
    elif xs_raw and xs_raw.strip():
        xs = xs_raw.strip().strip('"').strip("'")

    return c_user, xs

_cached_facebook_status: Optional[Dict[str, Any]] = None

def get_cached_facebook_status() -> Optional[Dict[str, Any]]:
    return _cached_facebook_status

def verify_facebook_cookie(c_user: Optional[str] = None, xs: Optional[str] = None) -> Dict[str, Any]:
    """
    Actively tests whether a Facebook session (c_user + xs) is currently valid and accepted by Meta.
    Queries https://www.facebook.com/me with browser TLS fingerprinting (curl_cffi).
    Caches the validation outcome for instantaneous status retrieval.
    """
    global _cached_facebook_status
    reload_env()

    parsed_u, parsed_x = parse_facebook_cookie_input(c_user or "", xs or "")
    u_token = parsed_u or c_user or os.getenv("FACEBOOK_C_USER", "").strip()
    x_token = parsed_x or xs or os.getenv("FACEBOOK_XS", "").strip()

    if not u_token or not x_token or len(u_token) < 4 or len(x_token) < 10:
        res = {
            "valid": False,
            "configured": False,
            "status": "missing",
            "message": "No Facebook session cookies configured (c_user and xs required)."
        }
        _cached_facebook_status = res
        return res

    u_token = u_token.strip().strip('"').strip("'")
    x_token = x_token.strip().strip('"').strip("'")

    if not u_token.isdigit():
        res = {
            "valid": False,
            "configured": True,
            "status": "invalid_format",
            "message": f"Invalid c_user: '{u_token}' is not a numeric account ID."
        }
        _cached_facebook_status = res
        return res

    masked = f"{x_token[:4]}...{x_token[-4:]}" if len(x_token) > 8 else "Present"

    try:
        from curl_cffi import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": f"c_user={u_token}; xs={x_token}"
        }

        resp = requests.get(
            "https://www.facebook.com/me",
            headers=headers,
            impersonate="chrome124",
            allow_redirects=False,
            timeout=4.5
        )

        loc = resp.headers.get("location", "")

        # Redirect inspection
        if resp.status_code in [301, 302, 303, 307, 308]:
            # Invalid/Expired redirects
            if not loc or loc in ["https://www.facebook.com/", "https://facebook.com/", "https://m.facebook.com/"] or any(k in loc.lower() for k in ["/login", "/checkpoint", "authwall", "recover", "error", "login.php"]):
                res = {
                    "valid": False,
                    "configured": True,
                    "status": "expired",
                    "c_user": u_token,
                    "masked": masked,
                    "status_code": resp.status_code,
                    "redirect_to": loc,
                    "message": "Facebook Session Expired or Rejected. Meta redirected to login/checkpoint."
                }
                _cached_facebook_status = res
                return res
            else:
                account_handle = loc.rstrip("/").split("/")[-1].split("?")[0]
                res = {
                    "valid": True,
                    "configured": True,
                    "status": "good",
                    "c_user": u_token,
                    "masked": masked,
                    "account_name": account_handle or f"User {u_token}",
                    "profile_url": loc,
                    "status_code": resp.status_code,
                    "message": f"Facebook Session Active & Verified (Account: {account_handle or u_token})"
                }
                _cached_facebook_status = res
                return res

        elif resp.status_code == 200:
            body_snippet = resp.text[:2000].lower()
            if any(k in body_snippet for k in ["log into facebook", "log in to facebook", "login_form", "checkpoint"]):
                res = {
                    "valid": False,
                    "configured": True,
                    "status": "expired",
                    "c_user": u_token,
                    "masked": masked,
                    "status_code": 200,
                    "message": "Facebook returned login authwall. Session token is expired or revoked."
                }
                _cached_facebook_status = res
                return res
            else:
                res = {
                    "valid": True,
                    "configured": True,
                    "status": "good",
                    "c_user": u_token,
                    "masked": masked,
                    "account_name": f"User {u_token}",
                    "status_code": 200,
                    "message": "Facebook Session Active (HTTP 200)"
                }
                _cached_facebook_status = res
                return res
        else:
            res = {
                "valid": False,
                "configured": True,
                "status": "problem",
                "c_user": u_token,
                "masked": masked,
                "status_code": resp.status_code,
                "message": f"Facebook returned HTTP {resp.status_code}."
            }
            _cached_facebook_status = res
            return res

    except Exception as e:
        logger.warning(f"Facebook session verification error: {e}")
        res = {
            "valid": False,
            "configured": True,
            "status": "error",
            "c_user": u_token,
            "masked": masked,
            "error": str(e),
            "message": f"Network check error: {e}"
        }
        _cached_facebook_status = res
        return res

def save_facebook_cookie_to_env(c_user: str, xs: str) -> Dict[str, Any]:
    """
    Saves Facebook session cookies (c_user and xs) into .env, runtime memory, and storage_state.json.
    Immediately verifies session validity live.
    """
    parsed_u, parsed_x = parse_facebook_cookie_input(c_user, xs)
    clean_user = parsed_u or (c_user or "").strip().strip('"').strip("'")
    clean_xs = parsed_x or (xs or "").strip().strip('"').strip("'")

    if not clean_user or not clean_user.isdigit():
        return {
            "success": False,
            "message": "Invalid c_user format. Facebook c_user is a numeric account ID."
        }
    if not clean_xs or len(clean_xs) < 10:
        return {
            "success": False,
            "message": "Invalid xs token format. Facebook xs session token is typically 20+ characters."
        }

    os.environ["FACEBOOK_C_USER"] = clean_user
    os.environ["FACEBOOK_XS"] = clean_xs

    update_env_variable("FACEBOOK_C_USER", clean_user)
    update_env_variable("FACEBOOK_XS", clean_xs)

    # Sync into storage_state.json
    try:
        import json
        s_dir = BASE_DIR / "data" / "browser_session"
        s_dir.mkdir(parents=True, exist_ok=True)
        state_file = s_dir / "storage_state.json"
        existing_cookies = []
        if state_file.exists():
            with open(state_file, "r", encoding="utf-8") as sf:
                d = json.load(sf)
                existing_cookies = [c for c in d.get("cookies", []) if c.get("name") not in ("c_user", "xs")]
        existing_cookies.append({
            "name": "c_user",
            "value": clean_user,
            "domain": ".facebook.com",
            "path": "/"
        })
        existing_cookies.append({
            "name": "xs",
            "value": clean_xs,
            "domain": ".facebook.com",
            "path": "/"
        })
        with open(state_file, "w", encoding="utf-8") as sf:
            json.dump({"cookies": existing_cookies, "origins": []}, sf, indent=2)
    except Exception:
        pass

    # Verify session immediately
    ver_res = verify_facebook_cookie(clean_user, clean_xs)

    return {
        "success": True,
        "c_user": clean_user,
        "xs_masked": f"{clean_xs[:4]}...{clean_xs[-4:]}",
        "verification": ver_res,
        "message": f"Facebook session saved to .env ({ver_res.get('message', 'Saved')})"
    }

def get_vault_summary(check_live: bool = False) -> Dict[str, Any]:
    """Returns a full summary of all configured sessions and keys in .env."""
    reload_env()

    # 1. LinkedIn
    li_cookie = get_linkedin_cookie_from_sources()
    li_jsession = get_linkedin_jsessionid_from_sources()
    li_masked = f"{li_cookie[:6]}...{li_cookie[-4:]}" if li_cookie else None

    global _cached_linkedin_status, _cached_facebook_status, _cached_linkedin_time
    now = time.time()
    cache_stale = (now - _cached_linkedin_time) > 120.0
    if (check_live or _cached_linkedin_status is None or cache_stale) and li_cookie:
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
        li_status = "configured"
        li_valid = False

    # 1b. Facebook Session
    fb_user = os.getenv("FACEBOOK_C_USER", "").strip()
    fb_xs = os.getenv("FACEBOOK_XS", "").strip()

    if check_live and fb_user and fb_xs:
        verify_facebook_cookie(fb_user, fb_xs)

    fb_valid = False
    fb_status = "not_configured"
    fb_account = None
    fb_masked = f"{fb_xs[:4]}...{fb_xs[-4:]}" if len(fb_xs) > 8 else None

    if not (fb_user and fb_xs):
        fb_status = "not_configured"
        fb_valid = False
    elif _cached_facebook_status:
        fb_valid = _cached_facebook_status.get("valid", False)
        fb_status = "good" if fb_valid else (_cached_facebook_status.get("status") or "problem")
        fb_account = _cached_facebook_status.get("account_name")
    else:
        # Initial check if basic format is valid
        fb_valid = bool(fb_user and fb_user.isdigit() and fb_xs and len(fb_xs) > 10)
        fb_status = "good" if fb_valid else "problem"

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

    # Overall cookie health:
    # "good" if BOTH LinkedIn and Facebook are active
    # "partial" if one is active and the other is not
    # "problem" if neither is active
    if li_valid and fb_valid:
        overall_status = "good"
    elif li_valid or fb_valid:
        overall_status = "partial"
    else:
        overall_status = "problem"

    return {
        "overall_status": overall_status,
        "is_good": (li_valid and fb_valid),
        "is_partial": (overall_status == "partial"),
        "has_problem": (overall_status == "problem"),
        "linkedin": {
            "configured": bool(li_cookie),
            "jsessionid_configured": bool(li_jsession),
            "valid": li_valid,
            "status": li_status,
            "masked": li_masked,
            "account_name": li_account,
            "env_key": "LINKEDIN_LI_AT",
            "message": _cached_linkedin_status.get("message") if _cached_linkedin_status else None
        },
        "facebook": {
            "configured": bool(fb_user and fb_xs),
            "valid": fb_valid,
            "status": fb_status,
            "c_user": fb_user or None,
            "account_name": fb_account or (f"User {fb_user}" if fb_user else None),
            "masked": fb_masked,
            "env_key": "FACEBOOK_C_USER"
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
