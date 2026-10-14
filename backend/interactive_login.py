import os
import sys
import time
import json
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_DIR = BASE_DIR / "data" / "browser_session"
LOG_FILE = SESSION_DIR / "interactive_login.log"
STATE_FILE = SESSION_DIR / "storage_state.json"

SESSION_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("InteractiveLogin")

def inject_success_banner(page, service_name: str):
    """Injects a floating visual confirmation banner into the authenticated page."""
    try:
        banner_id = f"bs-connect-success-{service_name.lower()}"
        page.evaluate(f"""() => {{
            if (document.getElementById('{banner_id}')) return;
            const b = document.createElement('div');
            b.id = '{banner_id}';
            b.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#059669;color:#ffffff;padding:14px 28px;border-radius:12px;font-family:system-ui,-apple-system,sans-serif;font-size:15px;font-weight:600;z-index:99999999;box-shadow:0 12px 30px rgba(0,0,0,0.5);border:2px solid #34d399;display:flex;align-items:center;gap:12px;text-align:center;';
            b.innerHTML = '<span style="font-weight:bold;">[OK]</span> <span>BreachSpillover: {service_name} Session Connected!</span><span style="font-size:12px;opacity:0.85;margin-left:8px;">(Session verified. Window will close shortly, or you can close it now)</span>';
            document.body.appendChild(b);
        }}""")
    except Exception:
        pass

def sync_storage_state(context):
    """Saves all cookies from the context into storage_state.json with clean deduplication."""
    try:
        raw_cookies = context.cookies()
        seen = set()
        clean_cookies = []
        for c in raw_cookies:
            c_dict = dict(c)
            # Normalize root domain without creating duplicates
            if c_dict.get("name") in ("li_at", "JSESSIONID") and c_dict.get("domain") == ".www.linkedin.com":
                c_dict["domain"] = ".linkedin.com"
            if c_dict.get("name") in ("c_user", "xs", "sb", "datr", "fr") and c_dict.get("domain") in (".www.facebook.com", "m.facebook.com", "web.facebook.com"):
                c_dict["domain"] = ".facebook.com"
            
            key = (c_dict.get("name"), c_dict.get("domain"), c_dict.get("path"))
            if key in seen:
                continue
            seen.add(key)
            clean_cookies.append(c_dict)

        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"cookies": clean_cookies, "origins": []}, f, indent=2)
    except Exception as e:
        logger.warning(f"Error saving storage state: {e}")

def force_foreground_desktop_window():
    """Forces the newly opened Edge / browser window to pop up in the foreground on Windows."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        
        h_desk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_desk:
            user32.SetThreadDesktop(h_desk)
        
        def enum_cb(hwnd, extra):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    if any(k in title for k in ["linkedin", "facebook", "edge", "log in", "login"]):
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # HWND_TOPMOST
                        user32.SetForegroundWindow(hwnd)
                        user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # HWND_NOTOPMOST
            return True
            
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        if h_desk:
            user32.EnumDesktopWindows(h_desk, WNDENUMPROC(enum_cb), 0)
        else:
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception as e:
        logger.warning(f"Could not force foreground window: {e}")

def main():
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            h_desk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if h_desk:
                user32.SetThreadDesktop(h_desk)
        except Exception as e:
            logger.warning(f"Could not switch thread desktop to Default: {e}")

    # Target can be "all", "unified", "linkedin", or "facebook" (defaults to "all")
    mode = (sys.argv[1] if len(sys.argv) > 1 else "all").strip().lower()
    if mode not in ["all", "unified", "linkedin", "facebook"]:
        if "facebook" in mode:
            mode = "facebook"
        elif "linkedin" in mode:
            mode = "linkedin"
        else:
            mode = "all"

    logger.info(f"Starting interactive session in mode: {mode}")

    # Clean up stale lockfile if not in use
    lock = SESSION_DIR / "lockfile"
    if lock.exists():
        try:
            lock.unlink()
        except Exception:
            pass

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        logger.error(f"Playwright not installed: {e}")
        return

    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    channel = "msedge" if any(os.path.exists(p) for p in edge_paths) else "chromium"
    logger.info(f"Launching desktop browser using channel: {channel}")

    sys.path.insert(0, str(BASE_DIR))
    from backend.session_vault import update_env_variable

    with sync_playwright() as p:
        try:
            launch_args = [
                "--disable-features=msEdgeStartupBoost,DestroyProfileOnBrowserClose",
                "--new-window",
                "--start-maximized",
                "--window-size=1280,850",
                "--window-position=60,40",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-blink-features=AutomationControlled"
            ]
            browser = None
            using_persistent = False
            try:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(SESSION_DIR),
                    channel=channel,
                    headless=False,
                    no_viewport=True,
                    ignore_default_args=["--no-startup-window"],
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
                    ),
                    args=launch_args
                )
                using_persistent = True
                logger.info(f"Connected persistent browser context at {SESSION_DIR}")
            except Exception as pe:
                logger.warning(f"Persistent context fallback ({pe}), launching isolated browser window...")
                browser = p.chromium.launch(
                    channel=channel,
                    headless=False,
                    ignore_default_args=["--no-startup-window"],
                    args=launch_args
                )
                context = browser.new_context(
                    no_viewport=True,
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
                    )
                )
                using_persistent = False

            want_linkedin = mode in ["all", "unified", "linkedin"]
            want_facebook = mode in ["all", "unified", "facebook"]

            linkedin_page = None
            facebook_page = None

            if want_linkedin:
                linkedin_page = context.pages[0] if context.pages else context.new_page()
                logger.info("Opening LinkedIn login in Tab 1...")
                try:
                    linkedin_page.goto("https://www.linkedin.com/login", timeout=45000)
                    linkedin_page.bring_to_front()
                except Exception as e_li:
                    logger.warning(f"LinkedIn initial navigation warning: {e_li}")

            if want_facebook:
                facebook_page = context.new_page() if (linkedin_page or context.pages) else (context.pages[0] if context.pages else context.new_page())
                logger.info("Opening Facebook login in Tab 2...")
                try:
                    facebook_page.goto("https://www.facebook.com/login", timeout=45000)
                except Exception as e_fb:
                    logger.warning(f"Facebook initial navigation warning: {e_fb}")

            # Bring primary tab to front
            if linkedin_page:
                try:
                    linkedin_page.bring_to_front()
                except Exception:
                    pass
            elif facebook_page:
                try:
                    facebook_page.bring_to_front()
                except Exception:
                    pass

            force_foreground_desktop_window()
            logger.info("Browser tabs rendered on desktop. Monitoring for authenticated session tokens...")

            linkedin_confirmed = not want_linkedin
            facebook_confirmed = not want_facebook
            settle_countdown = None

            # Polling loop: monitor for authentic tokens or user window close (up to 10 minutes)
            for i in range(600):
                time.sleep(1)
                if i in (1, 3):
                    force_foreground_desktop_window()

                try:
                    if not context.pages:
                        logger.info("User closed all browser tabs/windows.")
                        break

                    # 1. Check LinkedIn Authentication
                    if want_linkedin:
                        li_cookies = context.cookies(["https://www.linkedin.com", "https://linkedin.com"])
                        li_c = next((c.get("value") for c in li_cookies if c.get("name") == "li_at"), None)
                        js_c = next((c.get("value") for c in li_cookies if c.get("name") == "JSESSIONID"), None)

                        is_on_feed = False
                        for p_obj in context.pages:
                            p_url = (p_obj.url or "").lower()
                            # Specifically match authenticated LinkedIn areas
                            if "linkedin.com" in p_url and any(term in p_url for term in ["/feed", "/mynetwork", "/in/", "/messaging", "/jobs", "/notifications"]):
                                is_on_feed = True
                                break
                            try:
                                p_title = (p_obj.title() or "").lower()
                                if "feed" in p_title and "linkedin" in p_title:
                                    is_on_feed = True
                                    break
                            except Exception:
                                pass

                        has_valid_li = bool(li_c and len(li_c) > 50 and not li_c.startswith("delete"))
                        if has_valid_li and is_on_feed:
                            if not linkedin_confirmed:
                                linkedin_confirmed = True
                                logger.info("LinkedIn session confirmed. Persisting tokens...")
                                for p_obj in context.pages:
                                    if "linkedin.com" in (p_obj.url or "").lower():
                                        inject_success_banner(p_obj, "LinkedIn")
                            
                            # Keep persisting latest tokens if rotated
                            update_env_variable("LINKEDIN_LI_AT", li_c)
                            if js_c:
                                clean_js = js_c.strip('"').strip("'")
                                update_env_variable("LINKEDIN_JSESSIONID", clean_js)
                            sync_storage_state(context)

                    # 2. Check Facebook Authentication
                    if want_facebook:
                        fb_cookies = context.cookies(["https://www.facebook.com", "https://facebook.com"])
                        c_user = next((c.get("value") for c in fb_cookies if c.get("name") == "c_user"), None)
                        xs = next((c.get("value") for c in fb_cookies if c.get("name") == "xs"), None)

                        is_on_fb_feed = False
                        for p_obj in context.pages:
                            p_url = (p_obj.url or "").lower()
                            if "facebook.com" in p_url and not any(term in p_url for term in ["/login", "/checkpoint"]):
                                is_on_fb_feed = True
                                break

                        has_valid_fb = bool(c_user and c_user.isdigit() and len(c_user) >= 4 and xs and len(xs) > 15)
                        if has_valid_fb and is_on_fb_feed:
                            if not facebook_confirmed:
                                facebook_confirmed = True
                                logger.info(f"Facebook session confirmed (c_user: {c_user}). Persisting tokens...")
                                for p_obj in context.pages:
                                    if "facebook.com" in (p_obj.url or "").lower():
                                        inject_success_banner(p_obj, "Facebook")
                            update_env_variable("FACEBOOK_C_USER", c_user)
                            update_env_variable("FACEBOOK_XS", xs)
                            sync_storage_state(context)

                    # 3. Settling period management
                    if linkedin_confirmed and facebook_confirmed:
                        if settle_countdown is None:
                            settle_countdown = 10
                            logger.info("All requested services authenticated. Allowing 10s for session settling and telemetry...")
                        else:
                            settle_countdown -= 1
                            if settle_countdown <= 0:
                                logger.info("Session settling period finished. Closing browser cleanly.")
                                break

                except Exception as inner_e:
                    logger.warning(f"Loop check exception: {inner_e}")
                    break

            try:
                sync_storage_state(context)
                context.close()
                if not using_persistent and browser:
                    browser.close()
                logger.info("Interactive browser session closed cleanly.")
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Failed to launch browser: {e}", exc_info=True)

if __name__ == "__main__":
    main()
