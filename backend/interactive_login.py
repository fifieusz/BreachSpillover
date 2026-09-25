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

def main():
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.linkedin.com/login"
    logger.info(f"Starting interactive browser session for target: {target_url}")
    
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

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                channel=channel,
                headless=False,
                args=[
                    "--start-maximized",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            # Clean up stale storage state so user sees a fresh login page
            # instead of redirect loops or dead sessions
            context = browser.new_context(
                no_viewport=True,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
                )
            )

            page = context.pages[0] if context.pages else context.new_page()
            logger.info(f"Navigating to {target_url}...")
            page.goto(target_url, timeout=45000)
            logger.info("Browser window successfully rendered on desktop. Waiting for user login...")

            login_confirmed = False

            # Keep window open: monitor for genuine user authentication or window close (up to 10 minutes)
            for i in range(600):
                time.sleep(1)
                try:
                    if not context.pages:
                        logger.info("User closed all browser tabs/windows.")
                        break

                    # Collect cookies from all relevant LinkedIn domains
                    cookies = context.cookies(["https://www.linkedin.com", "https://linkedin.com"])
                    li_c = next((c.get("value") for c in cookies if c.get("name") == "li_at"), None)
                    js_c = next((c.get("value") for c in cookies if c.get("name") == "JSESSIONID"), None)

                    # Determine if user has reached genuine post-login destination
                    is_on_feed = False
                    for p in context.pages:
                        p_url = (p.url or "").lower()
                        # Strictly post-login member destinations
                        if any(term in p_url for term in ["/feed", "/mynetwork", "/in/", "/messaging", "/jobs"]):
                            is_on_feed = True
                            break

                    has_valid_cookie = bool(li_c and len(li_c) > 25 and not li_c.startswith("delete"))

                    if has_valid_cookie and is_on_feed:
                        login_confirmed = True
                        logger.info("Genuine authenticated LinkedIn feed confirmed! Saving storage_state and syncing to .env...")
                        try:
                            # Normalize cookies to ensure .linkedin.com domain coverage
                            raw_cookies = context.cookies()
                            normalized_cookies = []
                            for c in raw_cookies:
                                normalized_cookies.append(c)
                                if c.get("name") in ("li_at", "JSESSIONID") and c.get("domain") == ".www.linkedin.com":
                                    c_copy = dict(c)
                                    c_copy["domain"] = ".linkedin.com"
                                    normalized_cookies.append(c_copy)

                            # Save state file with normalized cookies
                            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
                            with open(STATE_FILE, "w", encoding="utf-8") as f:
                                json.dump({"cookies": normalized_cookies, "origins": []}, f, indent=2)

                            sys.path.insert(0, str(BASE_DIR))
                            from backend.session_vault import update_env_variable
                            update_env_variable("LINKEDIN_LI_AT", li_c)
                            if js_c:
                                update_env_variable("LINKEDIN_JSESSIONID", js_c)
                            logger.info("Synchronized matching li_at and JSESSIONID pair into .env and storage_state.json!")

                            try:
                                import backend.session_vault as sv
                                sv.reload_env()
                                sv._cached_linkedin_status = {
                                    "valid": True,
                                    "configured": True,
                                    "status": "good",
                                    "account_name": "Authenticated Member",
                                    "source": "browser_runner",
                                    "message": "Authenticated via local desktop browser."
                                }
                            except Exception:
                                pass

                            # Inject visual confirmation banner
                            for p in context.pages:
                                try:
                                    p.evaluate("""() => {
                                        if (document.getElementById('bs-connect-success-banner')) return;
                                        const b = document.createElement('div');
                                        b.id = 'bs-connect-success-banner';
                                        b.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#059669;color:#ffffff;padding:14px 28px;border-radius:12px;font-family:system-ui,-apple-system,sans-serif;font-size:16px;font-weight:700;z-index:99999999;box-shadow:0 12px 30px rgba(0,0,0,0.5);border:2px solid #34d399;display:flex;align-items:center;gap:12px;';
                                        b.innerHTML = '<span style="font-size:20px;">✓</span> <span>BreachSpillover: LinkedIn Session Connected! (Closing in 4s...)</span>';
                                        document.body.appendChild(b);
                                    }""")
                                except Exception:
                                    pass
                        except Exception as sync_e:
                            logger.warning(f"Error syncing cookies to .env: {sync_e}")

                        # Give user 4 seconds to see visual confirmation before closing
                        for _ in range(4):
                            time.sleep(1)
                            if not context.pages:
                                break
                        break
                except Exception as inner_e:
                    logger.warning(f"Loop check exception: {inner_e}")
                    break

            try:
                browser.close()
                logger.info("Browser closed cleanly.")
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Failed to launch browser: {e}", exc_info=True)

if __name__ == "__main__":
    main()


