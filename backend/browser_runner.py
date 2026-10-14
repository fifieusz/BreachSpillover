"""
BreachSpillover - Autonomous Background Browser Runner
Leverages a local persistent browser context (Microsoft Edge / Chromium) to seamlessly
extract deep LinkedIn career timelines, current employers (e.g. Merlon Security),
and verified profile dossiers completely hands-free without manual cookie pasting.
"""

import os
import re
import time
import json
import copy
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("BreachSpillover.BrowserRunner")

BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_DIR = BASE_DIR / "data" / "browser_session"

# In-memory TTL cache for browser extraction results
_LINKEDIN_BROWSER_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
)

def get_session_dir() -> Path:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return SESSION_DIR

def get_browser_channel() -> str:
    """Returns 'msedge' on Windows or default 'chromium'."""
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    if any(os.path.exists(p) for p in edge_paths):
        return "msedge"
    return "chromium"

def _load_env_keys():
    """Ensure any newly added .env keys (such as LINKEDIN_LI_AT, FACEBOOK_C_USER) are dynamically loaded."""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k in ("LINKEDIN_LI_AT", "LINKEDIN_JSESSIONID", "FACEBOOK_C_USER", "FACEBOOK_XS") and v:
                            os.environ[k] = v
        except Exception:
            pass

def is_browser_authenticated() -> Dict[str, Any]:
    """
    Checks if the persistent browser session or environment contains active sessions
    for LinkedIn and Facebook. Operates 100% locally to prevent session invalidation.
    """
    _load_env_keys()
    env_li = os.getenv("LINKEDIN_LI_AT", "").strip()
    env_fb_user = os.getenv("FACEBOOK_C_USER", "").strip()
    env_fb_xs = os.getenv("FACEBOOK_XS", "").strip()

    s_dir = get_session_dir()
    state_file = s_dir / "storage_state.json"

    li_auth = bool(env_li and len(env_li) > 25 and not env_li.startswith("delete"))
    try:
        from backend.session_vault import get_cached_linkedin_status
        cached_li = get_cached_linkedin_status()
        if cached_li is not None and cached_li.get("valid"):
            li_auth = True
    except Exception:
        pass

    fb_auth = bool(env_fb_user and env_fb_xs and len(env_fb_xs) > 15)

    # Check storage_state.json for active browser cookies
    if state_file.exists():
        try:
            import json
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            cookies = state_data.get("cookies", [])
            li_at_cookie = next((c for c in cookies if c.get("name") == "li_at"), None)
            js_cookie = next((c for c in cookies if c.get("name") == "JSESSIONID"), None)
            fb_c_user = next((c for c in cookies if c.get("name") == "c_user"), None)
            fb_xs = next((c for c in cookies if c.get("name") == "xs"), None)

            if li_at_cookie and len(li_at_cookie.get("value", "")) > 15:
                li_val = li_at_cookie["value"]
                exp = li_at_cookie.get("expires", -1)
                if not (exp > 0 and exp < time.time()) and not li_val.startswith("delete"):
                    li_auth = True
                    if li_val != env_li:
                        try:
                            from backend.session_vault import update_env_variable
                            update_env_variable("LINKEDIN_LI_AT", li_val)
                            if js_cookie and js_cookie.get("value"):
                                update_env_variable("LINKEDIN_JSESSIONID", js_cookie["value"])
                        except Exception:
                            pass

            if fb_c_user and fb_xs:
                fb_u_val = fb_c_user.get("value", "")
                fb_x_val = fb_xs.get("value", "")
                if fb_u_val and len(fb_x_val) > 15:
                    fb_auth = True
                    if fb_u_val != env_fb_user or fb_x_val != env_fb_xs:
                        try:
                            from backend.session_vault import update_env_variable
                            update_env_variable("FACEBOOK_C_USER", fb_u_val)
                            update_env_variable("FACEBOOK_XS", fb_x_val)
                        except Exception:
                            pass
        except Exception as e:
            logger.debug(f"Error reading storage_state.json: {e}")

    overall_auth = (li_auth or fb_auth)

    msg_tokens = []
    if li_auth:
        msg_tokens.append("LinkedIn Active")
    if fb_auth:
        msg_tokens.append("Facebook Active")
    summary_msg = f"Connected ({', '.join(msg_tokens)})" if msg_tokens else "No active investigator session. Launch browser to authenticate."

    return {
        "authenticated": overall_auth,
        "linkedin_authenticated": li_auth,
        "facebook_authenticated": fb_auth,
        "has_profile": state_file.exists(),
        "session_dir": str(s_dir),
        "linkedin": {
            "authenticated": li_auth,
            "masked": f"{env_li[:6]}...{env_li[-4:]}" if len(env_li) > 10 else None
        },
        "facebook": {
            "authenticated": fb_auth,
            "c_user": env_fb_user or None,
            "masked": f"{env_fb_xs[:6]}...{env_fb_xs[-4:]}" if len(env_fb_xs) > 10 else None
        },
        "message": summary_msg
    }

def _kill_stale_login_processes():
    """Terminates any existing orphaned interactive_login.py or Playwright browser processes to avoid conflicts."""
    if sys.platform == "win32":
        try:
            ps_script = """
            Get-CimInstance Win32_Process -Filter "name = 'python.exe'" | ForEach-Object {
                if ($_.CommandLine -like "*interactive_login.py*") {
                    Stop-Process -Id $_.ProcessId -Force
                }
            }
            Get-CimInstance Win32_Process -Filter "name = 'msedge.exe'" | ForEach-Object {
                if ($_.CommandLine -like "*remote-debugging-pipe*" -or $_.CommandLine -like "*playwright*" -or $_.CommandLine -like "*browser_session*") {
                    Stop-Process -Id $_.ProcessId -Force
                }
            }
            """
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, timeout=5)
        except Exception:
            pass

def _spawn_process_on_desktop(cmd_args: List[str], cwd: Path) -> bool:
    """
    Spawns a process explicitly assigned to the interactive user desktop (WinSta0\\Default).
    This ensures visible GUI windows (like Playwright browser instances) open on the user's
    physical monitor even when the parent server process runs inside a virtual/isolated desktop.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            import subprocess

            kernel32 = ctypes.windll.kernel32

            class STARTUPINFOW(ctypes.Structure):
                _fields_ = [
                    ('cb', wintypes.DWORD),
                    ('lpReserved', wintypes.LPWSTR),
                    ('lpDesktop', wintypes.LPWSTR),
                    ('lpTitle', wintypes.LPWSTR),
                    ('dwX', wintypes.DWORD),
                    ('dwY', wintypes.DWORD),
                    ('dwXSize', wintypes.DWORD),
                    ('dwYSize', wintypes.DWORD),
                    ('dwXCountChars', wintypes.DWORD),
                    ('dwYCountChars', wintypes.DWORD),
                    ('dwFillAttribute', wintypes.DWORD),
                    ('dwFlags', wintypes.DWORD),
                    ('wShowWindow', wintypes.WORD),
                    ('cbReserved2', wintypes.WORD),
                    ('lpReserved2', ctypes.c_char_p),
                    ('hStdInput', wintypes.HANDLE),
                    ('hStdOutput', wintypes.HANDLE),
                    ('hStdError', wintypes.HANDLE),
                ]

            class PROCESS_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ('hProcess', wintypes.HANDLE),
                    ('hThread', wintypes.HANDLE),
                    ('dwProcessId', wintypes.DWORD),
                    ('dwThreadId', wintypes.DWORD),
                ]

            si = STARTUPINFOW()
            si.cb = ctypes.sizeof(STARTUPINFOW)
            si.lpDesktop = r"WinSta0\Default"

            pi = PROCESS_INFORMATION()
            cmd_line = subprocess.list2cmdline(cmd_args)
            CREATE_NEW_PROCESS_GROUP = 0x00000200

            res = kernel32.CreateProcessW(
                None,
                cmd_line,
                None,
                None,
                False,
                CREATE_NEW_PROCESS_GROUP,
                None,
                str(cwd),
                ctypes.byref(si),
                ctypes.byref(pi)
            )
            if res:
                kernel32.CloseHandle(pi.hProcess)
                kernel32.CloseHandle(pi.hThread)
                return True
            else:
                logger.warning(f"CreateProcessW returned 0, error code: {kernel32.GetLastError()}")
        except Exception as e:
            logger.warning(f"Error launching process on WinSta0\\Default desktop: {e}")

    # Fallback to standard subprocess.Popen
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        cmd_args,
        cwd=str(cwd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags
    )
    return True

def launch_interactive_login(target: str = "all") -> Dict[str, Any]:
    """
    Launches a visible browser window using Playwright.
    Supports:
    - 'all': opens LinkedIn on Tab 1 and Facebook on Tab 2 in one browser session
    - 'linkedin': opens LinkedIn login
    - 'facebook': opens Facebook login
    Automatically captures cookies and synchronizes them to .env and storage_state.json.
    """
    _kill_stale_login_processes()
    clean_target = (target or "all").strip().lower()
    script_path = BASE_DIR / "backend" / "interactive_login.py"
    cmd = [sys.executable, str(script_path), clean_target]
    
    _spawn_process_on_desktop(cmd, BASE_DIR)

    if clean_target == "facebook":
        msg = "Visible browser launched. Please sign into Facebook. BreachSpillover will automatically capture your session tokens."
    elif clean_target == "linkedin":
        msg = "Visible browser launched. Please sign into LinkedIn. BreachSpillover will automatically capture your session tokens."
    else:
        msg = "Visible browser launched with LinkedIn and Facebook tabs. Sign into either or both platforms; BreachSpillover will automatically capture and sync your session tokens."
    
    return {
        "success": True,
        "mode": clean_target,
        "message": msg
    }

# In-memory TTL cache for headless profile scrapes (avoids redundant Playwright launches)
_LINKEDIN_SCRAPE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

def scrape_linkedin_profile_headless(profile_url: str) -> Dict[str, Any]:
    """
    Runs a headless browser using the persistent context to extract rich profile
    and career timeline details (current company, past roles, headline, about).
    Optimized for high-speed execution with in-memory caching and non-blocking DOM checks.
    """
    from playwright.sync_api import sync_playwright
    
    s_dir = get_session_dir()
    channel = get_browser_channel()
    
    clean_url = profile_url.strip().split("?")[0].rstrip("/")

    # Check in-memory cache first (5 minute TTL, only cache successful scrapes)
    now = time.time()
    if clean_url in _LINKEDIN_SCRAPE_CACHE:
        cached_time, cached_res = _LINKEDIN_SCRAPE_CACHE[clean_url]
        if now - cached_time < 300.0 and cached_res.get("success"):
            return cached_res

    auth_check = is_browser_authenticated()
    if not auth_check.get("linkedin_authenticated"):
        return {
            "success": False,
            "auth_required": True,
            "profile_url": clean_url,
            "message": auth_check.get("message", "No active authenticated LinkedIn session.")
        }
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel=channel,
                headless=True,
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            state_file = s_dir / "storage_state.json"
            if state_file.exists():
                try:
                    context = browser.new_context(
                        storage_state=str(state_file),
                        user_agent=USER_AGENT,
                        viewport={"width": 1440, "height": 900}
                    )
                except Exception:
                    context = browser.new_context(
                        user_agent=USER_AGENT,
                        viewport={"width": 1440, "height": 900}
                    )
            else:
                context = browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1440, "height": 900}
                )

            # Mask webdriver to evade bot detection
            try:
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            except Exception:
                pass

            _load_env_keys()
            env_li = os.getenv("LINKEDIN_LI_AT", "").strip()
            env_js = os.getenv("LINKEDIN_JSESSIONID", "").strip().strip('"').strip("'")

            # Only inject from env if not already present in context or differs
            if env_li and len(env_li) > 20 and not env_li.startswith("delete"):
                has_li_in_context = any(c.get("name") == "li_at" and c.get("value") == env_li for c in context.cookies())
                if not has_li_in_context:
                    cookies_to_add = [
                        {
                            "name": "li_at",
                            "value": env_li,
                            "domain": ".linkedin.com",
                            "path": "/",
                            "secure": True,
                            "httpOnly": True,
                            "sameSite": "None"
                        }
                    ]
                    if env_js:
                        cookies_to_add.append({
                            "name": "JSESSIONID",
                            "value": f'"{env_js}"',
                            "domain": ".linkedin.com",
                            "path": "/",
                            "secure": True,
                            "httpOnly": False,
                            "sameSite": "None"
                        })
                    try:
                        context.add_cookies(cookies_to_add)
                    except Exception as ce:
                        logger.debug(f"Could not inject env cookies: {ce}")
            
            page = context.new_page()
            
            try:
                page.goto(clean_url, wait_until="domcontentloaded", timeout=8000)
            except Exception as e:
                logger.warning(f"Headless navigation failed or redirected for {clean_url}: {e}")
                try:
                    browser.close()
                except Exception:
                    pass
                is_redirect_loop = "ERR_TOO_MANY_REDIRECTS" in str(e)
                res_fail = {
                    "success": False,
                    "is_redirect_loop": is_redirect_loop,
                    "message": f"Navigation failed: {e}"
                }
                return res_fail
                
            try:
                page.wait_for_selector("h1, main, div.profile-detail", timeout=2000)
            except Exception:
                pass
            time.sleep(0.5)
            
            curr_url = page.url
            title = page.title()
            title_lower = (title or "").lower()
            if "authwall" in curr_url or "login" in curr_url or "signup" in curr_url or "sign up" in title_lower or "log in" in title_lower:
                try:
                    browser.close()
                except Exception:
                    pass
                return {
                    "success": False,
                    "auth_required": True,
                    "profile_url": clean_url,
                    "message": "LinkedIn redirected to authwall. Please click 'Connect Browser' to authenticate once."
                }
                
            def _safe_query(sel, multiple=False):
                try:
                    return page.query_selector_all(sel) if multiple else page.query_selector(sel)
                except Exception as ex_ctx:
                    if "destroyed" in str(ex_ctx).lower() or "navigation" in str(ex_ctx).lower():
                        time.sleep(1.5)
                        try:
                            return page.query_selector_all(sel) if multiple else page.query_selector(sel)
                        except Exception:
                            return [] if multiple else None
                    return [] if multiple else None

            page_text = page.inner_text("body").lower() if _safe_query("body") else ""

            # Dismiss cookie consent dialog if present (common in EU / Netherlands)
            try:
                for consent_btn_sel in [
                    "button[action-type='ACCEPT']",
                    "button:has-text('Accept')",
                    "button:has-text('Accepteren')",
                    "button:has-text('Agree')",
                    "button.artdeco-button--primary"
                ]:
                    c_btn = _safe_query(consent_btn_sel)
                    if c_btn and c_btn.is_visible():
                        c_btn.click()
                        time.sleep(0.8)
                        break
            except Exception:
                pass

            # Safety Layer: Robust 404 & Dead Profile Detection
            is_404 = (
                "page not found" in title_lower
                or "404" in title_lower
                or "an exact match could not be found" in page_text
                or "this page doesn’t exist" in page_text
                or "this page doesn't exist" in page_text
                or "user not found" in page_text
                or "profile not found" in page_text
            )
            if is_404:
                logger.info(f"Target URL {clean_url} is a 404 / dead LinkedIn page.")
                try:
                    browser.close()
                except Exception:
                    pass
                return {
                    "success": False,
                    "is_404": True,
                    "profile_url": clean_url,
                    "message": f"LinkedIn profile does not exist (HTTP 404: {clean_url})"
                }
            
            # 1. Full Name: check page title first (e.g. "(21) Alje Woltjer | LinkedIn")
            full_name = None
            m_title = re.search(r'^(?:\(\d+\)\s*)?([^|•\n]+?)\s*\|\s*LinkedIn', title, re.IGNORECASE)
            if m_title:
                cand_title_name = m_title.group(1).strip()
                if cand_title_name and len(cand_title_name) < 60 and not any(w in cand_title_name.lower() for w in ["sign in", "login", "join", "feed"]):
                    full_name = cand_title_name

            if not full_name:
                for sel in ["h1.text-heading-xlarge", "h1.top-card-layout__title", "h1", "main h2", "h2"]:
                    el = _safe_query(sel)
                    if el:
                        text = el.inner_text().strip()
                        if text and len(text) < 60 and not any(w in text.lower() for w in ["linkedin", "notification", "activity", "options", "ad options"]):
                            full_name = text
                            break
                        
            # 2. Headline: check modern DOM elements and body text
            headline = None
            for sel in [
                ".text-body-medium.break-words",
                ".top-card-layout__headline",
                "div.text-body-medium",
                "main p",
                "main div"
            ]:
                for el in _safe_query(sel, multiple=True):
                    text = el.inner_text().strip()
                    if text and 3 < len(text) < 140 and not any(w in text.lower() for w in ["skip to", "notification", "connect", "message", "followers", "connections", "contact info"]):
                        if any(kw in text.lower() for kw in ["cto", "ceo", "ciso", "coo", "officer", "founder", "director", "manager", "lead", "engineer", "specialist", "partner", "consultant", "security", "merlon", "vooruit", "vormgever", "designer", "developer"]):
                            headline = text
                            break
                if headline:
                    break

            if not headline:
                dom_body = page.inner_text("body") if _safe_query("body") else ""
                m_hl = re.search(r'(?:^|\n)\s*((?:CTO|CEO|CISO|COO|Director|Lead|Founder|Head|Engineer|Specialist|Security)\s+[^\n]{2,80})', dom_body)
                if m_hl:
                    headline = m_hl.group(1).strip()
                        
            # 3. Location
            location = None
            for sel in [".text-body-small.inline.t-black--light.break-words", ".top-card__subline-item"]:
                el = _safe_query(sel)
                if el:
                    text = el.inner_text().strip()
                    if text and len(text) < 80:
                        location = text
                        break

            if not location:
                dom_body = page.inner_text("body") if _safe_query("body") else ""
                m_loc = re.search(r'(?:^|\n)\s*([^\n]*(?:Netherlands|Randstad|Amsterdam|Rotterdam|Utrecht|The Hague|Groningen|United Kingdom|London|United States|Germany)[^\n]*)', dom_body, re.IGNORECASE)
                if m_loc:
                    cand_loc = m_loc.group(1).strip()
                    if len(cand_loc) < 80 and not any(w in cand_loc.lower() for w in ["skip to", "notification"]):
                        location = cand_loc
                        
            # Scroll down to load Experience, Education, and Activity sections
            try:
                page.evaluate("window.scrollTo(0, 1200);")
                time.sleep(0.8)
                page.evaluate("window.scrollTo(0, 2600);")
                time.sleep(0.8)
            except Exception:
                pass
            
            # 4. Extract Experience items using accessibility clean spans
            experiences = []
            exp_lis = _safe_query("#experience ~ .pvs-list__outer-container > ul > li, section[data-section='experience'] li", multiple=True)
            
            for li in (exp_lis or []):
                try:
                    # Prefer clean aria-hidden text spans to avoid screen-reader duplication
                    clean_spans = li.query_selector_all("span[aria-hidden='true']")
                    lines = [s.inner_text().strip() for s in clean_spans if s.inner_text().strip()]
                    
                    if not lines:
                        raw = li.inner_text()
                        lines = [l.strip() for l in raw.split("\n") if l.strip()]
                        
                    if len(lines) >= 2:
                        role = lines[0]
                        company = lines[1]
                        if "•" in company:
                            company = company.split("•")[0].strip()
                        duration = lines[2] if len(lines) > 2 and any(char.isdigit() for char in lines[2]) else "N/A"
                        experiences.append({
                            "role": role,
                            "company": company,
                            "duration": duration,
                            "raw": " • ".join(lines[:3])
                        })
                except Exception:
                    pass
                    
            # 5. Extract Profile Picture, Cover Banner, Activity Posts, and Media Attachments
            profile_picture_url = None
            background_cover_url = None
            linkedin_photos = []
            try:
                from backend.image_recon import extract_image_perceptual_features, build_reverse_image_search_links
                
                raw_media = page.evaluate('''() => {
                    const items = [];
                    const seen = new Set();

                    const add = (img, cat, caption = '') => {
                        if (!img) return;
                        let src = img.src || img.getAttribute('data-delayed-url') || '';
                        if (!src || !src.includes('media.licdn.com') || src.includes('profile-framedphoto') || src.includes('ghost')) return;
                        if (img.closest('nav') || img.closest('header') || img.closest('#global-nav') || img.closest('aside') || img.closest('.scaffold-layout__aside')) return;
                        
                        // Select highest resolution from srcset if available
                        let bestSrc = src;
                        if (img.srcset) {
                            const parts = img.srcset.split(',').map(s => s.trim());
                            for (const part of parts) {
                                const [candUrl] = part.split(' ');
                                if (candUrl && candUrl.startsWith('http')) {
                                    bestSrc = candUrl;
                                }
                            }
                        }

                        const base = bestSrc.split('?')[0];
                        if (seen.has(base)) return;
                        seen.add(base);

                        items.push({
                            category: cat,
                            src: bestSrc,
                            thumbnail_url: src,
                            caption: caption || img.alt || ''
                        });
                    };

                    const main = document.querySelector('main, #profile-content, .scaffold-layout__main') || document.body;

                    // 1. Profile Avatar (Headshot)
                    for (const img of main.querySelectorAll('.pv-top-card-profile-picture__image, .pv-top-card__photo, .profile-card__photo, button.pv-top-card-profile-picture img, div.pv-top-card__photo-wrapper img, .top-card__profile-image')) {
                        add(img, 'avatar', 'Verified target professional headshot');
                    }
                    if (!items.some(i => i.category === 'avatar')) {
                        for (const img of main.querySelectorAll('img[src*="profile-displayphoto"]')) {
                            if (img.naturalWidth >= 200 || img.width >= 200 || img.matches('.pv-top-card-profile-picture__image, .pv-top-card__photo')) {
                                add(img, 'avatar', 'Verified target professional headshot');
                                break;
                            }
                        }
                    }

                    // 2. Profile Background Cover Banner
                    for (const img of main.querySelectorAll('.profile-background-image__image, img[src*="profile-displaybackground"], .pv-top-card__cover-photo img, div.profile-background-image img, div[data-view-name*="background-image"] img, img[alt*="cover photo" i]')) {
                        add(img, 'cover', 'Profile header cover banner');
                    }

                    // 3. Featured Section Media
                    for (const sec of main.querySelectorAll('section[id*="featured"], div[data-view-name*="featured"], .pv-featured-items__list-item')) {
                        for (const img of sec.querySelectorAll('img')) {
                            add(img, 'featured', 'Featured portfolio asset or certificate');
                        }
                    }

                    // 4. Activity Section / Post Previews on Profile
                    for (const img of main.querySelectorAll('img')) {
                        const s = img.src || img.getAttribute('data-delayed-url') || '';
                        if (s.includes('feedshare') || s.includes('article-cover') || (s.includes('dms/image') && (img.alt === 'View image' || (img.alt && img.alt.toLowerCase().includes('post'))))) {
                            if (!s.includes('logo') && !s.includes('profile-displayphoto') && !s.includes('profile-displaybackground')) {
                                add(img, 'post', img.alt || 'Target post / activity shared on LinkedIn');
                            }
                        }
                    }

                    // 5. Experience & Education Media Attachments
                    for (const img of main.querySelectorAll('a[href*="media"] img, a[href*="detail/treasury"] img, li.artdeco-list__item img[src*="dms/image"]')) {
                        const s = img.src || '';
                        if (!s.includes('logo') && !s.includes('profile-displayphoto') && !s.includes('profile-displaybackground')) {
                            add(img, 'project', 'Media attached to career experience or academic credential');
                        }
                    }

                    return items;
                }''')

                seen_p_bases = set()
                disp_name = full_name or "Target"
                for it in (raw_media or []):
                    u = it.get("src")
                    if not u or not u.startswith("http"):
                        continue
                    cat = it.get("category")
                    clean_b = u.split("?")[0]
                    if clean_b in seen_p_bases:
                        continue
                    seen_p_bases.add(clean_b)

                    feat = extract_image_perceptual_features(u)
                    if not feat.get("is_accessible"):
                        continue
                    w = feat.get("width", 0)
                    h = feat.get("height", 0)
                    if w < 48 or h < 48:
                        continue

                    is_sq = feat.get("is_square_or_portrait", False)
                    skin = feat.get("center_skin_ratio", 0)

                    if cat == "cover":
                        src_lbl = "LinkedIn Cover Banner"
                        classification = "WEBSITE_BANNER_OR_ASSET"
                        conf = 0.95
                        if not background_cover_url:
                            background_cover_url = u
                    elif cat == "avatar":
                        src_lbl = "LinkedIn Profile Avatar"
                        classification = "REAL_HUMAN_PORTRAIT"
                        conf = 0.99
                        if not profile_picture_url:
                            profile_picture_url = u
                    elif cat == "featured":
                        src_lbl = "LinkedIn Featured Media"
                        classification = "REAL_HUMAN_PORTRAIT" if (is_sq and skin >= 0.08) else "WEBSITE_BANNER_OR_ASSET"
                        conf = 0.92
                    elif cat == "project":
                        src_lbl = "LinkedIn Project Media"
                        classification = "WEBSITE_BANNER_OR_ASSET"
                        conf = 0.90
                    else: # post
                        src_lbl = "LinkedIn Posted Photo"
                        classification = "REAL_HUMAN_PORTRAIT" if (is_sq and skin >= 0.08) else "WEBSITE_BANNER_OR_ASSET"
                        conf = 0.92

                    linkedin_photos.append({
                        "platform": "LinkedIn",
                        "badge": "linkedin.com",
                        "source": src_lbl,
                        "image_url": u,
                        "thumbnail_url": it.get("thumbnail_url") or u,
                        "profile_url": clean_url,
                        "label": f"{src_lbl} ({disp_name})",
                        "caption": it.get("caption", ""),
                        "classification": classification,
                        "confidence": conf,
                        "is_verified": True,
                        "reverse_search_links": build_reverse_image_search_links(u),
                        "_feat": feat
                    })
            except Exception as e_media:
                logger.debug(f"Error extracting target LinkedIn media assets: {e_media}")

            # Extract top-card company and education indicators generically
            top_company = None
            top_education = None
            educations = []

            # 1. School links & entity buttons in top card / header
            try:
                school_links = page.query_selector_all("a[href*='/school/'], button[aria-label*='Education' i], div[aria-label*='Education' i]")
                for sl in school_links:
                    aria_lbl = (sl.get_attribute("aria-label") or "").strip()
                    clean_aria = re.sub(r'^(?:view\s+(?:company|school|education):\s*|education:\s*)', '', aria_lbl, flags=re.IGNORECASE).strip()
                    txt = sl.inner_text().strip().split("\n")[0].strip()
                    candidate_edu = clean_aria if (clean_aria and len(clean_aria) < 80 and not any(w in clean_aria.lower() for w in ["linkedin", "notification", "connections"])) else txt
                    if candidate_edu and len(candidate_edu) < 80 and not any(w in candidate_edu.lower() for w in ["linkedin", "notification", "connections"]):
                        top_education = candidate_edu
                        break
            except Exception as e_sl:
                logger.debug(f"Error extracting school link: {e_sl}")

            top_selectors = [
                "ul.pv-text-details__right-panel li",
                "div[aria-label*='Current company']",
                "button[aria-label*='Current company']",
                ".top-card-layout__entity-info",
                ".pv-top-card--experience-list-item",
                ".top-card__subline-item--bullet"
            ]
            for ts in top_selectors:
                el = page.query_selector(ts)
                if el:
                    t_text = el.inner_text().strip().split("\n")[0].strip()
                    if t_text and len(t_text) < 80 and not any(w in t_text.lower() for w in ["linkedin", "connections", "contact info"]):
                        is_edu_word = any(w in t_text.lower() for w in ["education", "school", "university", "college", "hogeschool", "universiteit", "academy", "institut", "applied sciences"])
                        if is_edu_word and not top_education:
                            top_education = t_text
                        elif not is_edu_word and not top_company and len(t_text) < 50:
                            top_company = t_text

            # Check entity elements with bullet e.g. "Employer • University"
            if not top_education or not top_company:
                try:
                    for el in _safe_query("p, div, span", multiple=True):
                        txt = el.inner_text().strip()
                        if "•" in txt and any(kw in txt.lower() for kw in ["university", "college", "hogeschool", "universiteit", "applied sciences", "school", "academy", "institut"]):
                            parts = [p.strip() for p in txt.split("•") if p.strip()]
                            for part in parts:
                                if any(kw in part.lower() for kw in ["university", "college", "hogeschool", "universiteit", "applied sciences", "school", "academy", "institut"]) and len(part) < 80:
                                    if not top_education:
                                        top_education = part
                                elif len(part) < 50 and not top_company and not any(w in part.lower() for w in ["connections", "contact info", "linkedin", "follower"]):
                                    if full_name and any(p_tok in part.lower() for p_tok in full_name.lower().split() if len(p_tok) >= 3):
                                        continue
                                    if any(bad_w in part.lower() for bad_w in ["1st", "2nd", "3rd", "degree"]):
                                        continue
                                    top_company = part
                except Exception:
                    pass

            # 6. Extract Education items from dedicated education section
            edu_lis = _safe_query("#education ~ .pvs-list__outer-container > ul > li, section[data-section='education'] li, div:has(> #education) ~ div ul > li, section:has(#education) li", multiple=True)
            for li in (edu_lis or []):
                try:
                    clean_spans = li.query_selector_all("span[aria-hidden='true']")
                    lines = [s.inner_text().strip() for s in clean_spans if s.inner_text().strip()]
                    if not lines:
                        raw = li.inner_text()
                        lines = [l.strip() for l in raw.split("\n") if l.strip()]
                    if len(lines) >= 1:
                        inst = lines[0]
                        deg = lines[1] if len(lines) > 1 else "Degree Program"
                        dur = lines[2] if len(lines) > 2 and any(char.isdigit() for char in lines[2]) else "Historical"
                        if inst and len(inst) < 100 and not any(w in inst.lower() for w in ["linkedin", "connections"]):
                            educations.append({
                                "institution": inst,
                                "degree": deg,
                                "duration": dur,
                                "raw": " • ".join(lines[:3])
                            })
                            if not top_education:
                                top_education = inst
                except Exception:
                    pass

            # 7. Fallback: Parse About section for educational credentials if no education section exists
            if not educations and not top_education:
                try:
                    about_el = _safe_query("section:has(#about), div:has(> #about) ~ div, #about ~ div, section.artdeco-card:has(#about)")
                    about_txt = about_el.inner_text().strip() if about_el else ""
                    if not about_txt:
                        dom_body = page.inner_text("body") if _safe_query("body") else ""
                        m_ab = re.search(r'(?:About|Info)\s*\n+([^\n]+(?:\n+[^\n]+){1,5})', dom_body, re.IGNORECASE)
                        if m_ab:
                            about_txt = m_ab.group(1).strip()
                    if about_txt:
                        m_edu = re.search(
                            r'(?:Afgestudeerd|Opleiding|Studied|Graduated|Student|Bachelor|Master|Degree|Associate Degree|Alumnus|Alumna)\s+(?:(?:aan|bij|at|an der|to)\s+(?:de\s+)?)?([A-Z][a-zA-Z\s&-]{2,50}?(?:University|Hogeschool|College|Universiteit|Academy|Institut|School|Applied Sciences)[a-zA-Z\s]*)',
                            about_txt,
                            re.IGNORECASE
                        )
                        if m_edu:
                            cand_inst = m_edu.group(1).strip().rstrip(".,;")
                            if len(cand_inst) < 80:
                                top_education = cand_inst
                                educations.append({
                                    "institution": cand_inst,
                                    "degree": "Higher Education Program",
                                    "duration": "Alumni",
                                    "raw": cand_inst
                                })
                        if not top_education:
                            m_inst_direct = re.search(
                                r'([A-Z][a-zA-Z\s&-]{2,50}?(?:University of Applied Sciences|University|Hogeschool|College|Universiteit|Academy|Institut|School of [A-Z][a-zA-Z]+))',
                                about_txt
                            )
                            if m_inst_direct:
                                cand_inst = m_inst_direct.group(1).strip().rstrip(".,;")
                                if len(cand_inst) < 80 and not any(w in cand_inst.lower() for w in ["linkedin", "security"]):
                                    top_education = cand_inst
                                    educations.append({
                                        "institution": cand_inst,
                                        "degree": "Higher Education Institution",
                                        "duration": "Alumni",
                                        "raw": cand_inst
                                    })
                except Exception as ex_ab:
                    logger.debug(f"Error parsing About for education: {ex_ab}")

            if top_education and not any(e.get("institution", "").lower() == top_education.lower() for e in educations):
                educations.insert(0, {
                    "institution": top_education,
                    "degree": "Higher Education Program",
                    "duration": "Alumni / Student",
                    "raw": top_education
                })

            # Determine current company from Experience, Headline, or Top Card
            current_company = None
            if experiences:
                current_company = experiences[0].get("company")
            if headline:
                for sep in [" at ", " @ ", " bij ", " - ", " | "]:
                    if sep in headline:
                        parts = headline.split(sep)
                        if len(parts) > 1:
                            cand = parts[-1].strip().split(".")[0].strip()
                            if cand and len(cand) < 40 and not any(w in cand.lower() for w in ["linkedin", "profile", "view"]):
                                current_company = cand
                                break
                if not current_company:
                    m_co = re.search(r'(?:CTO|CEO|CISO|COO|Director|Head|Lead|Manager)\s+(.+)', headline, re.IGNORECASE)
                    if m_co:
                        cand = m_co.group(1).strip()
                        if cand and len(cand) < 40 and not any(w in cand.lower() for w in ["linkedin", "profile", "view"]):
                            current_company = cand
            if not current_company and top_company:
                if not (full_name and any(p_tok in top_company.lower() for p_tok in full_name.lower().split() if len(p_tok) >= 3)):
                    current_company = top_company

            context.close()
            try:
                browser.close()
            except Exception:
                pass

            is_scraped = bool(full_name or headline or current_company or experiences or location or top_education or educations)
            if not is_scraped:
                logger.warning(f"Could not extract profile elements for {clean_url}. Title was: {title}")
                res_fail = {
                    "success": False,
                    "auth_required": ("sign up" in title_lower or "authwall" in curr_url or "login" in curr_url),
                    "profile_url": clean_url,
                    "page_title": title,
                    "message": "LinkedIn profile elements not accessible. Active browser authentication required."
                }
                return res_fail

            res_ok = {
                "success": True,
                "profile_url": clean_url,
                "full_name": full_name,
                "headline": headline,
                "current_company": current_company,
                "location": location,
                "experience": experiences,
                "education": educations,
                "top_education": top_education,
                "profile_picture_url": profile_picture_url,
                "background_cover_url": background_cover_url,
                "photos": linkedin_photos,
                "page_title": title
            }
            _LINKEDIN_SCRAPE_CACHE[clean_url] = (time.time(), res_ok)
            return res_ok

    except Exception as e:
        logger.error(f"Error scraping LinkedIn headless: {e}")
        res_err = {
            "success": False,
            "error": str(e),
            "profile_url": clean_url
        }
        return res_err

def auto_enrich_target_from_browser(
    profile_url: str,
    target_email: Optional[str] = None,
    target_name: Optional[str] = None,
    candidate_urls: Optional[List[str]] = None,
    persist_to_db: bool = True
) -> Dict[str, Any]:
    """
    Autonomously invokes the headless browser, scrapes the target's verified LinkedIn profile,
    and calls the ingestion pipeline to persist the complete employer and timeline directly.
    Safely iterates through candidate URLs if the primary candidate returns 404, preventing dead links.
    Capped at top 2 candidates for high speed.
    """
    c_key = f"{(profile_url or '').strip().lower()}::{(target_email or '').strip().lower()}::{(target_name or '').strip().lower()}"
    now = time.time()
    from backend.cache_manager import is_cache_disabled
    if not is_cache_disabled() and c_key in _LINKEDIN_BROWSER_CACHE:
        c_time, c_val = _LINKEDIN_BROWSER_CACHE[c_key]
        if now - c_time < 600.0:
            return copy.deepcopy(c_val)

    to_try = []
    if profile_url:
        to_try.append(profile_url)
    if candidate_urls:
        for cu in candidate_urls:
            if cu and cu not in to_try:
                to_try.append(cu)
    elif target_name or target_email:
        try:
            from backend.linkedin_recon import derive_linkedin_candidate_slugs
            for s in derive_linkedin_candidate_slugs(target_name or "", target_email):
                su = f"https://www.linkedin.com/in/{s}"
                if su not in to_try and f"{su}/" not in to_try:
                    to_try.append(su)
        except Exception:
            pass

    dead_urls: List[str] = []
    res = None
    successful_url = None

    # Cap to top 2 candidate URLs and enforce 6s overall timeout to guarantee fast execution
    start_time = time.time()
    for cand_u in to_try[:2]:
        if time.time() - start_time > 6.0:
            logger.info("LinkedIn candidate probing exceeded time budget, breaking early.")
            break
        cand_clean = cand_u.split("?")[0].rstrip("/")
        logger.info(f"Testing LinkedIn profile candidate: {cand_clean}")
        res = scrape_linkedin_profile_headless(cand_clean)
        if res and res.get("is_404"):
            dead_urls.append(cand_clean)
            logger.info(f"Candidate {cand_clean} confirmed 404 dead link, trying next candidate...")
            continue
        if res and res.get("success"):
            from backend.linkedin_recon import is_linkedin_identity_match
            if is_linkedin_identity_match(res, target_name, target_email):
                successful_url = cand_clean
                break
            else:
                logger.info(
                    f"Candidate {cand_clean} returned profile '{res.get('full_name')}' "
                    f"which does not match target identity '{target_name or target_email}'. Skipping entity collision."
                )
                continue
        if res and res.get("auth_required"):
            return res
        if res and res.get("is_redirect_loop"):
            dead_urls.append(cand_clean)
            logger.info(f"Candidate {cand_clean} returned redirect loop (non-existent profile), trying next candidate...")
            continue

    if not res or not res.get("success") or not successful_url:
        is_truly_all_404 = bool(dead_urls and len(dead_urls) >= len(to_try))
        error_msg = (
            "All candidate URLs returned 404 (pages do not exist)."
            if is_truly_all_404
            else (res.get("message") if res else "Failed to extract LinkedIn profile data via headless browser.")
        )
        return {
            "success": False,
            "is_404": is_truly_all_404,
            "dead_urls": dead_urls,
            "message": error_msg,
            "auth_required": bool(res and res.get("auth_required"))
        }

    if not persist_to_db:
        ret = {
            "success": True,
            "profile_url": successful_url,
            "dead_urls": dead_urls,
            "scraped": res,
            "full_name": res.get("full_name"),
            "headline": res.get("headline"),
            "current_company": res.get("current_company"),
            "top_education": res.get("top_education"),
            "location": res.get("location"),
            "experience": res.get("experience"),
            "education": res.get("education"),
            "profile_picture_url": res.get("profile_picture_url"),
            "photos": res.get("photos", []),
            "background_cover_url": res.get("background_cover_url")
        }
        _LINKEDIN_BROWSER_CACHE[c_key] = (now, copy.deepcopy(ret))
        return ret

    try:
        persist_res = persist_linkedin_profile_to_db(
            successful_url=successful_url,
            res=res,
            target_email=target_email,
            target_name=target_name
        )
        return {
            "success": True,
            "profile_url": successful_url,
            "dead_urls": dead_urls,
            "scraped": res,
            "full_name": res.get("full_name"),
            "headline": res.get("headline"),
            "current_company": res.get("current_company"),
            "top_education": res.get("top_education"),
            "location": res.get("location"),
            "experience": res.get("experience"),
            "education": res.get("education"),
            "profile_picture_url": res.get("profile_picture_url"),
            "photos": res.get("photos", []),
            "background_cover_url": res.get("background_cover_url"),
            "ingested": persist_res
        }
    except Exception as e:
        logger.error(f"Auto-enrichment DB persistence error: {e}")
        return {
            "success": True,
            "profile_url": successful_url,
            "dead_urls": dead_urls,
            "scraped": res,
            "full_name": res.get("full_name"),
            "headline": res.get("headline"),
            "current_company": res.get("current_company"),
            "top_education": res.get("top_education"),
            "location": res.get("location"),
            "experience": res.get("experience"),
            "education": res.get("education"),
            "profile_picture_url": res.get("profile_picture_url"),
            "photos": res.get("photos", []),
            "background_cover_url": res.get("background_cover_url"),
            "ingest_error": str(e)
        }


def persist_linkedin_profile_to_db(
    successful_url: str,
    res: Dict[str, Any],
    target_email: Optional[str] = None,
    target_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Directly persists verified LinkedIn profile, current organization (e.g. Merlon Security),
    and career timeline into SQLite database, removing any speculative dead links.
    """
    from backend.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()

    disp_name = target_name or res.get("full_name") or "Investigated Target"
    emp_id = None
    if target_email:
        cursor.execute("SELECT id, full_name, corporate_email, department FROM employees WHERE LOWER(corporate_email) = ?", (target_email.lower(),))
        row = cursor.fetchone()
        if row:
            emp_id = row["id"]
    if not emp_id and target_name:
        cursor.execute("SELECT id, full_name, corporate_email, department FROM employees WHERE LOWER(full_name) = ?", (target_name.lower(),))
        row = cursor.fetchone()
        if row:
            emp_id = row["id"]

    headline = res.get("headline") or "Professional Role"
    current_company = res.get("current_company") or "Corporate Identity"
    avatar_pic = res.get("profile_picture_url") or res.get("avatar_url")
    if avatar_pic and "profile-framedphoto" in avatar_pic:
        avatar_pic = None

    if not emp_id:
        disp_name = target_name or res.get("full_name") or "Investigated Target"
        corp_mail = target_email or f"{disp_name.lower().replace(' ', '.')}@osint.local"
        cursor.execute("""
            INSERT INTO employees (full_name, corporate_email, department, job_title)
            VALUES (?, ?, ?, ?)
        """, (disp_name, corp_mail, current_company, headline))
        emp_id = cursor.lastrowid

    cursor.execute("SELECT corporate_email, department FROM employees WHERE id = ?", (emp_id,))
    emp_row = cursor.fetchone()
    corp_mail = emp_row["corporate_email"] if emp_row and emp_row["corporate_email"] else (target_email or "")
    existing_dept = emp_row["department"] if emp_row and emp_row["department"] else ""

    domain_org = ""
    if corp_mail and "@" in corp_mail:
        d_host = corp_mail.split("@")[-1].lower()
        d_stem = d_host.split(".")[0].capitalize()
        if d_stem.lower() not in ["gmail", "outlook", "hotmail", "yahoo", "proton", "protonmail", "icloud", "osint"]:
            domain_org = d_stem

    combined_dept = current_company
    if domain_org and domain_org.lower() != current_company.lower():
        combined_dept = f"{current_company} • {domain_org}"
    elif existing_dept and existing_dept.lower() != current_company.lower() and "corporate identity" not in existing_dept.lower():
        parts = [p.strip() for p in existing_dept.split("•") if p.strip()]
        if current_company not in parts:
            combined_dept = f"{current_company} • {parts[0]}"

    emp_updates = ["job_title = ?", "department = ?"]
    emp_params = [headline, combined_dept]
    if avatar_pic:
        emp_updates.append("avatar_seed = ?")
        emp_params.append(avatar_pic)
    emp_params.append(emp_id)
    cursor.execute(f"UPDATE employees SET {', '.join(emp_updates)} WHERE id = ?", tuple(emp_params))

    clean_ver_url = successful_url.rstrip("/")
    slug = clean_ver_url.split("/")[-1]

    cursor.execute("""
        DELETE FROM pivots 
        WHERE employee_id = ? 
          AND (pivot_value LIKE 'LinkedIn:%' OR context_note LIKE '%linkedin.com/in/%')
          AND pivot_value != ?
    """, (emp_id, f"LinkedIn: @{slug}"))

    cursor.execute("""
        DELETE FROM pivots
        WHERE employee_id = ? AND pivot_type = 'PUBLIC_PROFILE' AND pivot_value = ?
    """, (emp_id, f"LinkedIn: @{slug}"))

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, NULL, 'PUBLIC_PROFILE', ?, 0.99, ?)
    """, (
        emp_id,
        f"LinkedIn: @{slug}",
        f"Verified LinkedIn Professional Profile: {headline} at {current_company} [URL: {clean_ver_url}/] [STATUS: VERIFIED]"
    ))

    cursor.execute("""
        DELETE FROM pivots 
        WHERE employee_id = ? 
          AND pivot_type = 'WORKPLACE'
          AND (pivot_value = ? OR pivot_value LIKE ?)
    """, (emp_id, f"Employer: {current_company}", f"Role:%{current_company}%"))

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, NULL, 'WORKPLACE', ?, 0.99, ?)
    """, (
        emp_id,
        f"Employer: {current_company}",
        f"Current verified corporate organization: {current_company} • Role: {headline} [STATUS: VERIFIED]"
    ))

    if headline and headline.lower() != "professional role":
        cursor.execute("""
            INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
            VALUES (?, NULL, 'WORKPLACE', ?, 0.98, ?)
        """, (
            emp_id,
            f"Role: {headline} at {current_company}",
            f"Verified executive/specialist role: {headline} [STATUS: VERIFIED]"
        ))

    if domain_org and domain_org.lower() != current_company.lower():
        cursor.execute("SELECT id FROM pivots WHERE employee_id = ? AND pivot_type = 'WORKPLACE' AND pivot_value LIKE ?", (emp_id, f"Employer: {domain_org}%"))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
                VALUES (?, NULL, 'WORKPLACE', ?, 0.95, ?)
            """, (
                emp_id,
                f"Employer: {domain_org}",
                f"Corporate domain & entity affiliation tied to {corp_mail} [STATUS: VERIFIED]"
            ))

    for exp in res.get("experience", []) or []:
        role = exp.get("role") or exp.get("title") or "Role"
        comp = exp.get("company") or "Company"
        dur = exp.get("duration") or exp.get("period") or "Historical"
        cursor.execute("""
            INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
            VALUES (?, NULL, 'TIMELINE', ?, 0.95, ?)
        """, (
            emp_id,
            f"{dur}: {role} at {comp}",
            f"Career experience verified via LinkedIn [Category: Career] [STATUS: VERIFIED]"
        ))

    for edu in res.get("education", []) or []:
        inst = edu.get("institution") or ""
        deg = edu.get("degree") or "Higher Education"
        dur = edu.get("duration") or edu.get("period") or "Alumni"
        if inst:
            cursor.execute("SELECT id FROM pivots WHERE employee_id = ? AND pivot_type = 'EDUCATION' AND pivot_value LIKE ?", (emp_id, f"Alma Mater: {inst}%"))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
                    VALUES (?, NULL, 'EDUCATION', ?, 0.98, ?)
                """, (
                    emp_id,
                    f"Alma Mater: {inst}",
                    f"Verified Higher Education Alma Mater: {inst} (Degree: {deg} • {dur}) [STATUS: VERIFIED]"
                ))

    # Persist all verified multi-photos from LinkedIn
    for photo in res.get("photos", []) or []:
        p_u = photo.get("image_url")
        p_src = photo.get("source") or "LinkedIn Profile Avatar"
        p_conf = float(photo.get("confidence", 0.95))
        p_class = photo.get("classification") or ("WEBSITE_BANNER_OR_ASSET" if ("banner" in p_src.lower() or "cover" in p_src.lower()) else "REAL_HUMAN_PORTRAIT")
        if p_u:
            cursor.execute("SELECT id FROM pivots WHERE employee_id = ? AND pivot_type = 'AVATAR_CORRELATION' AND pivot_value LIKE ?", (emp_id, f"%{p_u}%"))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
                    VALUES (?, NULL, 'AVATAR_CORRELATION', ?, ?, ?)
                """, (
                    emp_id,
                    f"Secondary Visual Footprint (LinkedIn): {p_u}",
                    p_conf,
                    f"Verified LinkedIn visual asset ({p_src}) for target {disp_name}. [CLASSIFICATION: {p_class}] [URL: {p_u}] [STATUS: SECONDARY AVATAR]"
                ))

    conn.commit()
    conn.close()
    return {"persisted": True, "employee_id": emp_id, "company": current_company, "job_title": headline}


