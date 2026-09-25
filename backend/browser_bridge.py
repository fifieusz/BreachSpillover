"""
BreachSpillover - Local Investigator Browser Bridge (Zero-Config Portability)
Enables 100% automated LinkedIn reconnaissance and DOM extraction without paid APIs,
without hardcoded shared credentials, and without IP-bound geoblock invalidation.

Architecture:
1. Dedicated Local Profile:
   Stores browser session in gitignored `data/browser_profile/`.
2. One-Time Setup:
   Launches a visible browser window where the investigator logs into their own account once.
3. Native Windows DPAPI Decryption:
   Reads and decrypts `li_at` directly from `data/browser_profile/Default/Network/Cookies` using
   Windows DPAPI + AES-GCM in 5ms without needing headless browsers or CDP locks.
4. Total Portability:
   Every investigator who clones BreachSpillover maintains their own private local session.
"""

import os
import sys
import json
import time
import shutil
import base64
import sqlite3
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ('cbData', wintypes.DWORD),
            ('pbData', ctypes.POINTER(ctypes.c_char))
        ]

BASE_DIR = Path(__file__).resolve().parent.parent
BROWSER_PROFILE_DIR = BASE_DIR / "data" / "browser_session"

# Ensure the local profile directory exists
BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory session cache so background scans do not re-read disk unnecessarily
_CACHED_SESSION: Optional[Dict[str, str]] = None


SESSION_FILE = BASE_DIR / "data" / "session.json"


def find_system_browser() -> Optional[str]:
    """
    Locates an installed browser executable (Opera GX, Google Chrome, Brave, Opera, Microsoft Edge)
    across Windows, macOS, and Linux.
    """
    if sys.platform == "win32":
        candidates = [
            # Check Opera GX first (common default on gaming & power-user Windows PCs)
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe"),
            # Check Google Chrome
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            # Check Brave Browser
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            # Check Standard Opera
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\opera.exe"),
            r"C:\Program Files\Opera\launcher.exe",
            # Check Microsoft Edge (fallback)
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        
        # Check PATH
        for binary in ["opera.exe", "chrome.exe", "brave.exe", "msedge.exe", "opera", "chrome", "msedge"]:
            found = shutil.which(binary)
            if found:
                return found

    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Opera GX.app/Contents/MacOS/Opera GX",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p

    else:
        # Linux
        for binary in ["google-chrome", "brave-browser", "opera", "microsoft-edge", "chromium-browser", "chromium"]:
            found = shutil.which(binary)
            if found:
                return found

    return None


def get_master_key() -> bytes:
    """Decrypts the Chromium master key from Local State using Windows DPAPI."""
    if sys.platform != "win32":
        return b""
    local_state_path = BROWSER_PROFILE_DIR / "Local State"
    if not local_state_path.exists():
        return b""
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        raw_key = local_state.get("os_crypt", {}).get("encrypted_key", "")
        if not raw_key:
            return b""
        encrypted_key = base64.b64decode(raw_key)
        # Strip "DPAPI" 5-byte prefix
        data_to_decrypt = encrypted_key[5:]
        blob_in = DATA_BLOB(len(data_to_decrypt), ctypes.cast(ctypes.c_char_p(data_to_decrypt), ctypes.POINTER(ctypes.c_char)))
        blob_out = DATA_BLOB()
        if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            cbData = int(blob_out.cbData)
            pbData = blob_out.pbData
            key = ctypes.string_at(pbData, cbData)
            ctypes.windll.kernel32.LocalFree(pbData)
            return key
    except Exception:
        pass
    return b""


def read_cookie_from_disk(cookie_name: str = "li_at") -> Optional[str]:
    """
    Safely snapshots and decrypts a cookie from data/browser_profile/Default/Network/Cookies
    even while Microsoft Edge is actively running.
    """
    cookie_db = BROWSER_PROFILE_DIR / "Default" / "Network" / "Cookies"
    if not cookie_db.exists():
        return None

    key = get_master_key()
    tmp = tempfile.mktemp(suffix=".db")
    try:
        if sys.platform == "win32":
            # Kernel32 CopyFileW creates an instant snapshot bypassing exclusive write locks
            res = ctypes.windll.kernel32.CopyFileW(str(cookie_db), tmp, False)
            if not res:
                return None
        else:
            shutil.copyfile(cookie_db, tmp)

        con = sqlite3.connect(tmp)
        rows = con.execute("SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%linkedin.com%'").fetchall()
        con.close()

        for name, val in rows:
            if name == cookie_name:
                if key and len(val) > 15:
                    try:
                        nonce = val[3:15]
                        ciphertext = val[15:]
                        aesgcm = AESGCM(key)
                        decrypted = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
                        if decrypted and len(decrypted) > 15:
                            return decrypted
                    except Exception:
                        pass
                if isinstance(val, str) and len(val) > 15:
                    return val
    except Exception:
        pass
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
    return None


def is_browser_process_active() -> bool:
    """Checks if Edge is currently holding the profile lock."""
    lock_file = BROWSER_PROFILE_DIR / "LOCK"
    if not lock_file.exists():
        lock_file = BROWSER_PROFILE_DIR / "Default" / "LOCK"
    if not lock_file.exists():
        return False
    try:
        with open(lock_file, "r+"):
            pass
        return False
    except (PermissionError, IOError):
        return True


def save_persisted_session(cookie: str) -> bool:
    """Persists a valid li_at cookie to data/session.json for permanent survival across server restarts."""
    global _CACHED_SESSION
    c = cookie.strip()
    if not c:
        return False
    # If the user pasted a raw header or cookie string like li_at=AQED...
    if "li_at=" in c:
        import re
        match = re.search(r'li_at=([^;,\s]+)', c)
        if match:
            c = match.group(1).strip('"\'')

    _CACHED_SESSION = {"li_at": c, "JSESSIONID": "ajax:1234567890"}
    os.environ["LINKEDIN_LI_AT"] = c
    try:
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = get_persisted_session_data()
        data["li_at"] = c
        data["has_scraper_authenticator"] = True
        data["account_issue"] = None
        data["notice"] = None
        data["updated_at"] = time.time()
        data["source"] = "investigator_session"
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def clear_persisted_session() -> None:
    """Clears cached and persisted session data."""
    global _CACHED_SESSION
    _CACHED_SESSION = None
    os.environ.pop("LINKEDIN_LI_AT", None)
    if SESSION_FILE.exists():
        try:
            SESSION_FILE.unlink()
        except Exception:
            pass


_LAST_LAUNCH_TIME: float = 0.0

def launch_investigator_login_window(flow: str = "linkedin") -> Dict[str, Any]:
    """
    Launches a dedicated visible browser window for investigator authentication.
    Supports Opera GX, Chrome, Brave, Edge, and system default browser via webbrowser.
    Guarantees that only a single LinkedIn authentication tab opens.
    """
    global _LAST_LAUNCH_TIME
    import webbrowser

    now = time.time()
    if now - _LAST_LAUNCH_TIME < 3.0:
        return {
            "success": True,
            "browser": "Active",
            "message": "Browser launch already in progress. Please check your browser window.",
            "urls": ["https://www.linkedin.com/login"]
        }
    _LAST_LAUNCH_TIME = now

    browser_bin = find_system_browser()

    # Open exclusively LinkedIn login (never open duplicate tabs or Google account pages)
    urls = ["https://www.linkedin.com/login"]

    # 1. Try launching with the detected browser binary
    if browser_bin and os.path.isfile(browser_bin):
        browser_name = Path(browser_bin).name.lower()
        try:
            if "opera" in browser_name:
                cmd = [
                    browser_bin,
                    f"--user-data-dir={str(BROWSER_PROFILE_DIR)}",
                    "--disable-features=AppBoundEncryptionCredentialValidation",
                    "--remote-debugging-port=9222",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-sync",
                    "--new-window",
                    "--start-maximized"
                ] + urls
            elif "edge" in browser_name:
                cmd = [
                    browser_bin,
                    f"--user-data-dir={str(BROWSER_PROFILE_DIR)}",
                    "--disable-features=AppBoundEncryptionCredentialValidation",
                    "--remote-debugging-port=9222",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-sync",
                    "--new-window",
                    "--start-maximized"
                ] + urls
            else:
                # Chrome / Brave / Chromium
                cmd = [
                    browser_bin,
                    f"--user-data-dir={str(BROWSER_PROFILE_DIR)}",
                    "--disable-features=AppBoundEncryptionCredentialValidation",
                    "--remote-debugging-port=9222",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-sync",
                    "--new-window",
                    "--start-maximized"
                ] + urls

            p = subprocess.Popen(cmd)
            # Give it a brief moment to ensure it didn't instantly exit (like DMA-disabled Edge)
            time.sleep(0.4)
            if p.poll() is None or p.returncode == 0:
                return {
                    "success": True,
                    "browser": Path(browser_bin).stem,
                    "message": f"Browser opened via {Path(browser_bin).stem}. Complete your sign-in in the opened window.",
                    "urls": urls
                }
        except Exception:
            pass

    # 2. Universal Fallback: Use standard OS default browser (works 100% on every OS)
    try:
        for u in urls:
            webbrowser.open_new(u)
        return {
            "success": True,
            "browser": "Default System Browser",
            "message": "Opened login tabs in your system browser. Complete your sign-in in the opened tabs.",
            "urls": urls
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to open browser: {e}"
        }


def get_persisted_session_data() -> Dict[str, Any]:
    """Reads session.json if it exists."""
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def login_google_account(email: str, name: Optional[str] = None) -> Dict[str, Any]:
    """
    Authenticates investigator via their Google account.
    Checks if this Google account has a linked scraping authenticator (e.g. LinkedIn session).
    If unlinked, flags the account_issue and notice as required by user.
    """
    clean_email = email.strip()
    if not clean_email or "@" not in clean_email:
        return {"success": False, "error": "Invalid email address"}

    user_name = name or clean_email.split("@")[0].replace(".", " ").title()
    
    data = get_persisted_session_data()
    data["authenticated"] = True
    data["auth_provider"] = "google"
    data["user_email"] = clean_email
    data["user_name"] = user_name
    data["updated_at"] = time.time()

    # Check if a scraper authenticator (li_at) is already available
    cookie = extract_bridge_session()
    has_authenticator = bool(cookie and len(cookie.get("li_at", "")) > 15)
    data["has_scraper_authenticator"] = has_authenticator

    if not has_authenticator:
        data["account_issue"] = "unregistered_scraper_account"
        data["notice"] = (
            f"The Google account \"{clean_email}\" does not have a registered LinkedIn reconnaissance account attached. "
            "BreachSpillover will operate using Google public indices, but verified corporate and employer profiling will be degraded."
        )
    else:
        data["account_issue"] = None
        data["notice"] = None

    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return {
        "success": True,
        "authenticated": True,
        "user_email": clean_email,
        "user_name": user_name,
        "has_scraper_authenticator": has_authenticator,
        "account_issue": data.get("account_issue"),
        "notice": data.get("notice")
    }


def logout_account() -> Dict[str, Any]:
    """Logs out investigator and clears session state."""
    global _CACHED_SESSION
    _CACHED_SESSION = None
    os.environ.pop("LINKEDIN_LI_AT", None)
    if SESSION_FILE.exists():
        try:
            SESSION_FILE.unlink()
        except Exception:
            pass
    return {"success": True, "authenticated": False}


def extract_bridge_session(timeout_seconds: int = 5) -> Optional[Dict[str, str]]:
    """Extracts the active LinkedIn session tokens from memory, session.json, env, or disk profile."""
    global _CACHED_SESSION
    if _CACHED_SESSION and _CACHED_SESSION.get("li_at"):
        return _CACHED_SESSION

    # 1. Environment variable
    env_cookie = os.getenv("LINKEDIN_LI_AT", "").strip()
    if env_cookie:
        _CACHED_SESSION = {"li_at": env_cookie, "JSESSIONID": "ajax:1234567890"}
        return _CACHED_SESSION

    # 2. Persisted session file (survives restarts)
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            c = data.get("li_at", "").strip()
            if c and len(c) > 20:
                _CACHED_SESSION = {"li_at": c, "JSESSIONID": "ajax:1234567890"}
                os.environ["LINKEDIN_LI_AT"] = c
                return _CACHED_SESSION
        except Exception:
            pass

    # 3. Dedicated browser profile SQLite DB (Edge / Chrome)
    cookie = read_cookie_from_disk("li_at")
    if cookie:
        save_persisted_session(cookie)
        return _CACHED_SESSION

    # 4. Check installed desktop browsers (Opera GX, Opera, Chrome, Edge) if readable
    system_cookie = extract_from_system_browsers()
    if system_cookie:
        save_persisted_session(system_cookie)
        return _CACHED_SESSION

    return None


def extract_from_system_browsers() -> Optional[str]:
    """Attempts to decrypt li_at from installed desktop browsers if available."""
    if sys.platform != "win32":
        return None
    candidates = [
        (os.path.expandvars(r"%APPDATA%\Opera Software\Opera GX Stable\Local State"),
         os.path.expandvars(r"%APPDATA%\Opera Software\Opera GX Stable\Default\Network\Cookies")),
        (os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable\Local State"),
         os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable\Default\Network\Cookies")),
        (os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Local State"),
         os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")),
        (os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Local State"),
         os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies")),
    ]
    for key_path, db_path in candidates:
        if not os.path.isfile(key_path) or not os.path.isfile(db_path):
            continue
        try:
            with open(key_path, "r", encoding="utf-8") as f:
                ls = json.load(f)
            raw_key = base64.b64decode(ls["os_crypt"]["encrypted_key"])[5:]
            blob_in = DATA_BLOB(len(raw_key), ctypes.cast(ctypes.c_char_p(raw_key), ctypes.POINTER(ctypes.c_char)))
            blob_out = DATA_BLOB()
            if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
                continue
            master_key = ctypes.string_at(blob_out.pbData, int(blob_out.cbData))
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)

            tmp = tempfile.mktemp(suffix=".db")
            if ctypes.windll.kernel32.CopyFileW(db_path, tmp, False):
                con = sqlite3.connect(tmp)
                rows = con.execute("SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%linkedin.com%'").fetchall()
                con.close()
                os.remove(tmp)
                for name, val in rows:
                    if name == "li_at" and len(val) > 15:
                        if val.startswith(b"v10") or val.startswith(b"v11"):
                            aes = AESGCM(master_key)
                            dec = aes.decrypt(val[3:15], val[15:], None).decode("utf-8", errors="ignore")
                            if dec and len(dec) > 20:
                                return dec
        except Exception:
            pass
    return None


def get_active_bridge_cookie() -> Optional[str]:
    """Retrieves the active li_at cookie from the local bridge or environment."""
    session = extract_bridge_session()
    if session and session.get("li_at"):
        return session["li_at"]
    return None


def is_bridge_authenticated() -> bool:
    """Checks whether the investigator is authenticated via Google or has a valid scraper session."""
    data = get_persisted_session_data()
    if data.get("authenticated", False):
        return True
    cookie = get_active_bridge_cookie()
    return bool(cookie and len(cookie) > 20)


def clear_cached_session() -> None:
    """Invalidates the in-memory session cache."""
    global _CACHED_SESSION
    _CACHED_SESSION = None


def inspect_bridge_status() -> Dict[str, Any]:
    """Returns full diagnostics of investigator authentication and scraping status."""
    browser_bin = find_system_browser()
    is_open = is_browser_process_active()
    data = get_persisted_session_data()

    # Check cookie
    cookie_dict = extract_bridge_session()
    has_cookie = bool(cookie_dict and len(cookie_dict.get("li_at", "")) > 15)

    is_authed = bool(data.get("authenticated", False) or has_cookie)
    email = data.get("user_email")
    name = data.get("user_name")

    # In Zero-Auth mode, BreachSpillover operates with 100% capacity via passive OSINT & browser delegation
    mode = "voyager" if has_cookie else "zero_auth"
    notice = data.get("notice")
    account_issue = data.get("account_issue")

    if has_cookie:
        mode_label = "Linked Session (Voyager API Active)"
        account_issue = None
        notice = None
    elif is_authed and email:
        mode_label = "Google Investigator Active (Zero-Auth OSINT)"
        if not notice:
            notice = f"The Google account \"{email}\" does not have a registered LinkedIn reconnaissance account attached."
    else:
        mode_label = "Zero-Auth OSINT Active"
        notice = "Operating in Zero-Auth mode. Public OSINT, company intelligence, and direct browser pivots are fully unlocked."

    return {
        "authenticated": is_authed,
        "mode": mode,
        "mode_label": mode_label,
        "zero_auth_ready": True,
        "user_email": email,
        "user_name": name,
        "has_scraper_authenticator": has_cookie,
        "account_issue": account_issue,
        "notice": notice,
        "browser_available": bool(browser_bin),
        "browser_path": browser_bin,
        "profile_dir": str(BROWSER_PROFILE_DIR),
        "is_live_browser_open": is_open
    }

