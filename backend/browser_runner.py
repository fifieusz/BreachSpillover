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
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("BreachSpillover.BrowserRunner")

BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_DIR = BASE_DIR / "data" / "browser_session"

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
    """Ensure any newly added .env keys (such as LINKEDIN_LI_AT) are dynamically loaded."""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("LINKEDIN_LI_AT="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            os.environ["LINKEDIN_LI_AT"] = val
        except Exception:
            pass

def is_browser_authenticated() -> Dict[str, Any]:
    """
    Checks if the persistent browser session contains an active session for LinkedIn.
    Validates storage_state.json in data/browser_session or LINKEDIN_LI_AT in .env.
    Operates 100% locally to prevent anti-bot session invalidation.
    """
    _load_env_keys()
    env_li = os.getenv("LINKEDIN_LI_AT", "").strip()
    s_dir = get_session_dir()
    state_file = s_dir / "storage_state.json"

    # Check storage_state.json first (source of truth from active browser session)
    if state_file.exists():
        try:
            import json
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            cookies = state_data.get("cookies", [])
            li_at_cookie = next((c for c in cookies if c.get("name") == "li_at"), None)
            js_cookie = next((c for c in cookies if c.get("name") == "JSESSIONID"), None)
            if li_at_cookie and len(li_at_cookie.get("value", "")) > 15:
                li_val = li_at_cookie["value"]
                exp = li_at_cookie.get("expires", -1)
                is_expired = (exp > 0 and exp < time.time())
                if not is_expired and not li_val.startswith("delete"):
                    # Sync into .env if missing or updated
                    if li_val != env_li:
                        try:
                            from backend.session_vault import update_env_variable
                            update_env_variable("LINKEDIN_LI_AT", li_val)
                            if js_cookie and js_cookie.get("value"):
                                update_env_variable("LINKEDIN_JSESSIONID", js_cookie["value"])
                        except Exception:
                            pass
                    return {
                        "authenticated": True,
                        "has_profile": True,
                        "source": "browser_session_state",
                        "session_dir": str(s_dir),
                        "message": "Authenticated LinkedIn session active via saved browser session."
                    }
        except Exception as e:
            logger.debug(f"Error reading storage_state.json: {e}")

    # Fallback to .env cookie if configured
    if env_li and len(env_li) > 25 and not env_li.startswith("delete"):
        return {
            "authenticated": True,
            "has_profile": True,
            "source": "env_cookie",
            "session_dir": str(s_dir),
            "message": "Authenticated LinkedIn session active via LINKEDIN_LI_AT (.env)"
        }

    return {
        "authenticated": False,
        "has_profile": state_file.exists(),
        "session_dir": str(s_dir),
        "message": "No active browser session found. Click 'Connect Browser' to authenticate once."
    }

def launch_interactive_login(target_url: str = "https://www.linkedin.com/login") -> Dict[str, Any]:
    """
    Launches a real visible browser window with the persistent session profile using Playwright.
    Allows the user to sign in once via Google SSO or standard credentials.
    All cookies are permanently saved to data/browser_session.
    """
    script_path = BASE_DIR / "backend" / "interactive_login.py"
    cmd = [sys.executable, str(script_path), target_url]
    
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        
    subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags
    )
    
    return {
        "success": True,
        "mode": "playwright_edge_interactive",
        "message": "Visible Microsoft Edge browser launched. Please sign into LinkedIn (via Google or password). Once logged in, close the browser window or return here."
    }

def scrape_linkedin_profile_headless(profile_url: str) -> Dict[str, Any]:
    """
    Runs a headless browser using the persistent context to extract rich profile
    and career timeline details (current company, past roles, headline, about).
    """
    from playwright.sync_api import sync_playwright
    
    s_dir = get_session_dir()
    channel = get_browser_channel()
    
    clean_url = profile_url.strip().split("?")[0].rstrip("/")

    auth_check = is_browser_authenticated()
    if not auth_check.get("authenticated"):
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
                page.goto(clean_url, wait_until="domcontentloaded", timeout=12000)
            except Exception as e:
                logger.warning(f"Headless navigation failed or redirected for {clean_url}: {e}")
                try:
                    browser.close()
                except Exception:
                    pass
                return {
                    "success": False,
                    "message": f"Navigation failed: {e}"
                }
                
            time.sleep(1.2)
            
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
                
            page_text = page.inner_text("body").lower() if page.query_selector("body") else ""

            # Dismiss cookie consent dialog if present (common in EU / Netherlands)
            try:
                for consent_btn_sel in [
                    "button[action-type='ACCEPT']",
                    "button:has-text('Accept')",
                    "button:has-text('Accepteren')",
                    "button:has-text('Agree')",
                    "button.artdeco-button--primary"
                ]:
                    c_btn = page.query_selector(consent_btn_sel)
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
                    el = page.query_selector(sel)
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
                for el in page.query_selector_all(sel):
                    text = el.inner_text().strip()
                    if text and 3 < len(text) < 140 and not any(w in text.lower() for w in ["skip to", "notification", "connect", "message", "followers", "connections", "contact info"]):
                        if any(kw in text.lower() for kw in ["cto", "ceo", "ciso", "coo", "officer", "founder", "director", "manager", "lead", "engineer", "specialist", "partner", "consultant", "security", "merlon", "vooruit"]):
                            headline = text
                            break
                if headline:
                    break

            if not headline:
                dom_body = page.inner_text("body") if page.query_selector("body") else ""
                m_hl = re.search(r'(?:^|\n)\s*((?:CTO|CEO|CISO|COO|Director|Lead|Founder|Head|Engineer|Specialist|Security)\s+[^\n]{2,80})', dom_body)
                if m_hl:
                    headline = m_hl.group(1).strip()
                        
            # 3. Location
            location = None
            for sel in [".text-body-small.inline.t-black--light.break-words", ".top-card__subline-item"]:
                el = page.query_selector(sel)
                if el:
                    text = el.inner_text().strip()
                    if text and len(text) < 80:
                        location = text
                        break

            if not location:
                dom_body = page.inner_text("body") if page.query_selector("body") else ""
                m_loc = re.search(r'(?:^|\n)\s*([^\n]*(?:Netherlands|Randstad|Amsterdam|Rotterdam|Utrecht|The Hague|Groningen|United Kingdom|London|United States|Germany)[^\n]*)', dom_body, re.IGNORECASE)
                if m_loc:
                    cand_loc = m_loc.group(1).strip()
                    if len(cand_loc) < 80 and not any(w in cand_loc.lower() for w in ["skip to", "notification"]):
                        location = cand_loc
                        
            # Scroll down to load Experience section
            page.evaluate("window.scrollTo(0, 1000);")
            time.sleep(1.2)
            
            # 4. Extract Experience items using accessibility clean spans
            experiences = []
            exp_lis = page.query_selector_all("#experience ~ .pvs-list__outer-container > ul > li, section[data-section='experience'] li")
            
            for li in exp_lis:
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
                    
            # 5. Extract Profile Picture / Avatar strictly from target's top-card container
            profile_picture_url = None
            try:
                top_card_img_src = page.evaluate('''() => {
                    const mainContainer = document.querySelector('main, #profile-content, .scaffold-layout__main, .profile-card__content');
                    if (!mainContainer) return null;

                    const candidateImgs = Array.from(mainContainer.querySelectorAll('img')).filter(img => {
                        // Strict exclusion of header, navigation, and global UI elements
                        if (img.closest('nav') || img.closest('header') || img.closest('.global-nav') || img.closest('#global-nav') || img.closest('[data-view-name*="me-navigation"]')) {
                            return false;
                        }
                        const src = img.src || img.getAttribute('data-delayed-url') || '';
                        if (!src || !src.startsWith('http') || src.includes('data:image') || src.includes('ghost')) {
                            return false;
                        }
                        // Ignore background banners / covers and investigator frames
                        if (src.includes('background') || src.includes('banner') || src.includes('profile-framedphoto')) {
                            return false;
                        }
                        // Target profile pictures on LinkedIn contain profile-displayphoto or match top-card avatar classes
                        const isProfilePhoto = img.matches('.pv-top-card-profile-picture__image, .pv-top-card__photo, .profile-card__photo, button.pv-top-card-profile-picture img, div.pv-top-card__photo-wrapper img, .top-card__profile-image');
                        const isMainDisplay = src.includes('media.licdn.com') && src.includes('profile-displayphoto');
                        return isProfilePhoto || isMainDisplay;
                    });

                    if (candidateImgs.length > 0) {
                        return candidateImgs[0].src || candidateImgs[0].getAttribute('data-delayed-url') || null;
                    }
                    return null;
                }''')
                if top_card_img_src and "ghost" not in top_card_img_src and "profile-framedphoto" not in top_card_img_src:
                    profile_picture_url = top_card_img_src
            except Exception as e:
                logger.debug(f"Error extracting target avatar: {e}")

            # Extract top-card company indicator
            top_company = None
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
                    if t_text and len(t_text) < 50 and not any(w in t_text.lower() for w in ["linkedin", "education", "school", "university", "college", "connections", "contact info"]):
                        top_company = t_text
                        break

            # Determine current company from Experience, Top Card, or Headline
            current_company = None
            if experiences:
                current_company = experiences[0].get("company")
            if not current_company and top_company:
                current_company = top_company
            if not current_company and headline:
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

            context.close()
            try:
                browser.close()
            except Exception:
                pass

            is_scraped = bool(full_name or headline or current_company or experiences or location)
            if not is_scraped:
                logger.warning(f"Could not extract profile elements for {clean_url}. Title was: {title}")
                return {
                    "success": False,
                    "auth_required": ("sign up" in title_lower or "authwall" in curr_url or "login" in curr_url),
                    "profile_url": clean_url,
                    "page_title": title,
                    "message": "LinkedIn profile elements not accessible. Active browser authentication required."
                }

            return {
                "success": True,
                "profile_url": clean_url,
                "full_name": full_name,
                "headline": headline,
                "current_company": current_company,
                "location": location,
                "experience": experiences,
                "profile_picture_url": profile_picture_url,
                "page_title": title
            }

    except Exception as e:
        logger.error(f"Error scraping LinkedIn headless: {e}")
        return {
            "success": False,
            "error": str(e),
            "profile_url": clean_url
        }

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
    """
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

    for cand_u in to_try:
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
        return {
            "success": True,
            "profile_url": successful_url,
            "dead_urls": dead_urls,
            "scraped": res
        }

    try:
        from backend.main import ProfileIngestRequest, ingest_profile_data

        req = ProfileIngestRequest(
            profile_url=successful_url,
            platform="LinkedIn",
            target_email=target_email,
            target_name=target_name or res.get("full_name"),
            headline=res.get("headline"),
            current_company=res.get("current_company"),
            location=res.get("location"),
            experience=res.get("experience"),
            avatar_url=res.get("profile_picture_url")
        )
        ingest_res = ingest_profile_data(req)
        return {
            "success": True,
            "profile_url": successful_url,
            "dead_urls": dead_urls,
            "scraped": res,
            "ingested": ingest_res
        }
    except Exception as e:
        logger.error(f"Auto-enrichment error: {e}")
        return {
            "success": True,
            "profile_url": successful_url,
            "dead_urls": dead_urls,
            "scraped": res,
            "ingest_error": str(e)
        }


