"""
BreachSpillover - Universal Web Unblocker & HTTP 999 Bypass Engine
Integrates proxy-unblocker APIs (ScraperAPI, ScrapingBee, ZenRows) to automatically
bypass HTTP 999 anti-bot barriers, Cloudflare, and authwalls across LinkedIn,
social media, and protected corporate sites without local browser popups.
"""

import os
import re
import logging
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger("BreachSpillover.Unblocker")

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

def resolve_unblocker_config() -> Dict[str, Optional[str]]:
    """
    Resolves configured unblocker provider and API key from .env or os.environ.
    Supported providers:
    - scraperapi (SCRAPER_API_KEY)
    - scrapingbee (SCRAPINGBEE_API_KEY)
    - zenrows (ZENROWS_API_KEY)
    """
    scraperapi_key = ""
    scrapedo_key = ""
    zenrows_key = ""
    scrapingbee_key = ""
    brightdata_key = ""
    generic_key = ""

    try:
        from dotenv import dotenv_values
        if ENV_FILE.exists():
            vals = dotenv_values(dotenv_path=ENV_FILE)
            scraperapi_key = (vals.get("SCRAPER_API_KEY") or "").strip()
            scrapedo_key = (vals.get("SCRAPEDO_API_KEY") or vals.get("SCRAPE_DO_TOKEN") or "").strip()
            zenrows_key = (vals.get("ZENROWS_API_KEY") or "").strip()
            scrapingbee_key = (vals.get("SCRAPINGBEE_API_KEY") or "").strip()
            brightdata_key = (vals.get("BRIGHTDATA_API_KEY") or "").strip()
            generic_key = (vals.get("UNBLOCKER_API_KEY") or "").strip()
    except Exception:
        pass

    if not any([scraperapi_key, scrapedo_key, zenrows_key, scrapingbee_key, brightdata_key, generic_key]):
        scraperapi_key = os.getenv("SCRAPER_API_KEY", "").strip()
        scrapedo_key = os.getenv("SCRAPEDO_API_KEY", "").strip() or os.getenv("SCRAPE_DO_TOKEN", "").strip()
        zenrows_key = os.getenv("ZENROWS_API_KEY", "").strip()
        scrapingbee_key = os.getenv("SCRAPINGBEE_API_KEY", "").strip()
        brightdata_key = os.getenv("BRIGHTDATA_API_KEY", "").strip()
        generic_key = os.getenv("UNBLOCKER_API_KEY", "").strip()

    if scrapedo_key:
        return {"provider": "scrapedo", "api_key": scrapedo_key}
    elif scraperapi_key:
        if len(scraperapi_key) > 35:
            return {"provider": "scrapedo", "api_key": scraperapi_key}
        return {"provider": "scraperapi", "api_key": scraperapi_key}
    elif zenrows_key:
        return {"provider": "zenrows", "api_key": zenrows_key}
    elif scrapingbee_key:
        return {"provider": "scrapingbee", "api_key": scrapingbee_key}
    elif brightdata_key:
        return {"provider": "brightdata", "api_key": brightdata_key}
    elif generic_key:
        provider = os.getenv("UNBLOCKER_PROVIDER", "scraperapi").lower().strip()
        return {"provider": provider, "api_key": generic_key}

    return {"provider": None, "api_key": None}

def fetch_html_with_unblocker_fallback(
    url: str,
    render_js: bool = True,
    timeout: int = 4
) -> Dict[str, Any]:
    """
    1. Attempts direct fetch with curl_cffi Chrome impersonation.
    2. If the site returns HTTP 999, 403, 429, or redirects to an authwall:
       Automatically routes request through the configured Unblocker API.
    """
    clean_url = url.strip()
    from curl_cffi import requests as curl_requests

    # 1. Attempt direct request
    try:
        r = curl_requests.get(
            clean_url,
            impersonate="chrome124",
            timeout=8,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9,nl;q=0.8"
            }
        )
        is_blocked = (
            r.status_code in [999, 403, 429] or
            "authwall" in r.text.lower() or
            "request denied" in r.text.lower() or
            ("linkedin.com" in clean_url and "join linkedin" in r.text.lower() and len(r.text) < 5000)
        )
        if not is_blocked and r.status_code == 200:
            return {
                "success": True,
                "status_code": 200,
                "html": r.text,
                "via": "direct",
                "url": clean_url
            }
    except Exception as e:
        logger.warning(f"Direct request failed for {clean_url}: {e}")

    # 2. Site blocked or returned 999: Check if Unblocker API key is configured
    config = resolve_unblocker_config()
    provider = config.get("provider")
    api_key = config.get("api_key")

    if not api_key:
        return {
            "success": False,
            "status_code": 999,
            "blocked": True,
            "via": "direct_blocked",
            "url": clean_url,
            "message": "Target website blocked automated access (HTTP 999). Add SCRAPER_API_KEY to .env to bypass automatically."
        }

    # 3. Route through Unblocker API
    try:
        import requests as std_requests
        unblocker_url = None
        params = {}

        if provider == "scraperapi":
            unblocker_url = "https://api.scraperapi.com"
            params = {
                "api_key": api_key,
                "url": clean_url,
                "render": "true" if render_js else "false"
            }
        elif provider == "scrapingbee":
            unblocker_url = "https://app.scrapingbee.com/api/v1/"
            params = {
                "api_key": api_key,
                "url": clean_url,
                "render_js": "true" if render_js else "false",
                "premium_proxy": "true" if "linkedin.com" in clean_url else "false"
            }
        elif provider == "scrapedo":
            unblocker_url = "https://api.scrape.do"
            params = {
                "token": api_key,
                "url": clean_url,
                "render": "true" if render_js else "false"
            }
        elif provider == "zenrows":
            unblocker_url = "https://api.zenrows.com/v1/"
            params = {
                "apikey": api_key,
                "url": clean_url,
                "js_render": "true" if render_js else "false",
                "premium_proxy": "true" if "linkedin.com" in clean_url else "false"
            }

        logger.info(f"Routing blocked URL {clean_url} through Unblocker API ({provider})...")
        resp = std_requests.get(unblocker_url, params=params, timeout=timeout)

        if resp.status_code in (401, 402, 403):
            logger.warning(f"Unblocker API returned {resp.status_code} (quota exceeded / unauthorized). Fast-failing.")
            return {
                "success": False,
                "status_code": resp.status_code,
                "is_private_profile": False,
                "message": f"Unblocker API quota exceeded ({resp.status_code})."
            }

        is_private = (
            "may be private" in resp.text.lower() or
            (resp.status_code == 404 and "linkedin.com" in clean_url)
        )

        if resp.status_code == 200 and len(resp.text) > 500 and not is_private:
            return {
                "success": True,
                "status_code": 200,
                "html": resp.text,
                "via": f"unblocker_{provider}",
                "provider": provider,
                "url": clean_url
            }
        else:
            return {
                "success": False,
                "status_code": resp.status_code,
                "is_private_profile": is_private,
                "via": f"unblocker_{provider}",
                "url": clean_url,
                "message": f"Unblocker API returned status {resp.status_code}: {'Profile is set to Members Only privacy wall' if is_private else resp.text[:200]}"
            }

    except Exception as e:
        logger.error(f"Unblocker API request error: {e}")
        return {
            "success": False,
            "status_code": 500,
            "via": f"unblocker_{provider}",
            "error": str(e),
            "url": clean_url
        }

def parse_linkedin_html(html: str, profile_url: str) -> Dict[str, Any]:
    """
    Parses unblocked LinkedIn profile HTML to extract current company (e.g. Merlon Security),
    job titles, headline, location, avatar, and career experiences.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Page Title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    
    # 1. Full Name
    full_name = None
    h1 = soup.find("h1")
    if h1:
        full_name = h1.get_text(strip=True)
    elif title and " | " in title:
        full_name = title.split(" - ")[0].split(" | ")[0].strip()
        
    # 2. Headline
    headline = None
    meta_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        desc = meta_desc["content"].strip()
        headline = desc
    
    if not headline:
        for cls in ["text-body-medium", "top-card-layout__headline", "pv-text-details__left-panel"]:
            el = soup.find(class_=re.compile(cls))
            if el:
                headline = el.get_text(strip=True)
                break
                
    # 3. Current Company Determination (e.g. "Merlon Security", "Vooruit")
    current_company = None
    if headline:
        for sep in [" at ", " @ ", " bij ", " | ", " - "]:
            if sep in headline:
                parts = headline.split(sep)
                if len(parts) > 1:
                    cand = parts[-1].strip().split(".")[0].strip()
                    if cand and len(cand) < 40 and not any(w in cand.lower() for w in ["linkedin", "profile", "view"]):
                        current_company = cand
                        break

    # 4. Avatar Image URL
    avatar_url = None
    img_el = soup.find("img", class_=re.compile(r"pv-top-card-profile-picture|top-card__photo|evi-image|entity-image"))
    if not img_el:
        img_el = soup.find("img", attrs={"title": re.compile(r"photo|profile", re.I)})
    if img_el:
        src = img_el.get("src") or img_el.get("data-delayed-url")
        if src and src.startswith("http") and "data:image" not in src and "ghost" not in src and "profile-framedphoto" not in src:
            avatar_url = src

    # 5. Experience items
    experiences = []
    for li in soup.find_all("li", class_=re.compile(r"experience|artdeco-list__item|pvs-list__item")):
        spans = [s.get_text(strip=True) for s in li.find_all(["span", "div"]) if s.get_text(strip=True)]
        unique_spans = []
        for s in spans:
            if s not in unique_spans and len(s) < 80:
                unique_spans.append(s)
        if len(unique_spans) >= 2:
            experiences.append({
                "role": unique_spans[0],
                "company": unique_spans[1],
                "duration": unique_spans[2] if len(unique_spans) > 2 else "N/A"
            })
            if not current_company:
                current_company = unique_spans[1]

    return {
        "full_name": full_name,
        "headline": headline or title,
        "current_company": current_company,
        "avatar_url": avatar_url,
        "experiences": experiences,
        "profile_url": profile_url
    }

def unblock_and_enrich_target_profile(
    profile_url: str,
    target_email: Optional[str] = None,
    target_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    High-level handler: Fetches profile HTML with unblocker fallback.
    If the target profile is behind a Members-Only privacy wall ("profile may be private"),
    automatically waterfalls to the local background browser runner (Tier 2).
    """
    res = fetch_html_with_unblocker_fallback(profile_url, render_js=False)
    
    # If unblocker returned 404 or private profile wall, waterfall down to local browser runner
    if not res.get("success") or res.get("is_private_profile"):
        logger.info(f"Target profile {profile_url} is private or unblocker failed. Waterfalling to Tier 2 (Local Browser Runner)...")
        try:
            from backend.browser_runner import auto_enrich_target_from_browser
            browser_res = auto_enrich_target_from_browser(profile_url, target_email=target_email, target_name=target_name, persist_to_db=False)
            if browser_res and browser_res.get("success"):
                return {
                    "success": True,
                    "via": "hybrid_waterfall_browser_runner",
                    "waterfall_tier": 2,
                    "profile_url": browser_res.get("profile_url"),
                    "dead_urls": browser_res.get("dead_urls", []),
                    "scraped": browser_res.get("scraped")
                }
        except Exception as e:
            logger.warning(f"Tier 2 local browser fallback error: {e}")
        return res

    parsed = parse_linkedin_html(res.get("html", ""), profile_url)

    # Validate identity to prevent stranger collisions
    from backend.linkedin_recon import is_linkedin_identity_match
    if not is_linkedin_identity_match(parsed, target_name, target_email):
        logger.info(
            f"Unblocked LinkedIn profile '{parsed.get('full_name')}' at {profile_url} "
            f"does not match target identity '{target_name or target_email}'. Skipping entity collision."
        )
        return {
            "success": False,
            "is_identity_collision": True,
            "profile_url": profile_url,
            "parsed": parsed,
            "message": f"Profile full name '{parsed.get('full_name')}' does not match target identity '{target_name}'"
        }
    
    # Ingest directly into database
    try:
        from backend.main import ProfileIngestRequest, ingest_profile_data
        
        req = ProfileIngestRequest(
            profile_url=profile_url,
            platform="LinkedIn",
            target_email=target_email,
            target_name=target_name or parsed.get("full_name"),
            headline=parsed.get("headline"),
            current_company=parsed.get("current_company"),
            location=None,
            experience=parsed.get("experiences"),
            avatar_url=parsed.get("avatar_url")
        )
        ingest_res = ingest_profile_data(req)
        return {
            "success": True,
            "via": res.get("via"),
            "waterfall_tier": 1,
            "parsed": parsed,
            "ingested": ingest_res
        }
    except Exception as e:
        logger.error(f"Failed to ingest unblocked profile: {e}")
        return {
            "success": True,
            "via": res.get("via"),
            "parsed": parsed,
            "ingest_error": str(e)
        }

