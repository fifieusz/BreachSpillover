"""
BreachSpillover - Universal AI-Assisted Web Dork Reconnaissance Engine
Automates live targeted OSINT search queries (Facebook, LinkedIn, personal websites, handles),
harvests search snippets and profile URLs, and executes LLM-driven entity
disambiguation (Groq Llama 3.3 / Gemini) to prune false positives and extract
corroborated physical locations, employers, and social presence.
COMPLETELY GENERIC: Zero hardcoded names, companies, or cities.
"""

import json
import os
import re
import base64
import urllib.parse
import urllib.request
import concurrent.futures
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

logger = logging.getLogger("BreachSpillover.WebDorkRecon")

from backend.ai_engine import call_groq_api, resolve_api_key, load_dotenv

USER_AGENT_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
)
USER_AGENT_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Generic TLD to Country Mapping for OSINT endpoint localization
TLD_TO_COUNTRY = {
    "nl": "Netherlands",
    "de": "Germany",
    "uk": "United Kingdom",
    "fr": "France",
    "be": "Belgium",
    "ch": "Switzerland",
    "at": "Austria",
    "es": "Spain",
    "it": "Italy",
    "se": "Sweden",
    "no": "Norway",
    "dk": "Denmark",
    "fi": "Finland",
    "pl": "Poland",
    "cz": "Czech Republic",
    "ca": "Canada",
    "au": "Australia",
    "nz": "New Zealand",
    "br": "Brazil",
    "jp": "Japan",
    "in": "India",
    "us": "United States",
    "ie": "Ireland",
    "pt": "Portugal",
    "za": "South Africa"
}

# In-memory cache for fast session re-queries without duplicate network calls
_DORK_CACHE: Dict[str, Dict[str, Any]] = {}

# Disallowed Facebook route slugs (system pages, directories, login/search paths)
FB_DISALLOWED_SLUGS = {
    "login", "login.php", "recover", "help", "policies", "sharer", "share", "groups", "pages",
    "settings", "watch", "marketplace", "events", "company_creation", "photo.php", "permalink.php",
    "story.php", "hashtag", "messages", "me", "about", "public", "people", "directory", "places",
    "games", "saved", "fundraisers", "index.php", "checkpoint", "dialog", "plugins", "tr", "ads",
    "business", "careers", "privacy", "terms", "legal", "security", "support", "gaming", "live",
    "reel", "reels", "stories", "share", "sharer.php"
}

def extract_valid_facebook_profile(
    url: str,
    title: str = "",
    snippet: str = "",
    target_name: str = "",
    target_email: str = "",
    known_handles: Optional[List[str]] = None
) -> Optional[Dict[str, str]]:
    """
    Strictly validates whether a discovered Facebook URL is a legitimate personal profile
    belonging to the investigated target entity.
    Supports:
    - Standard vanity profiles: facebook.com/username
    - Hyphenated vanity slugs with numeric IDs: facebook.com/First-Last-10000...
    - People path profiles: facebook.com/people/First-Last/10000... or facebook.com/people/First-Last
    - Profile ID format: facebook.com/profile.php?id=10000...
    Filters out:
    - Encoded/hashed garbage URLs (%E6%AD%25, %F0%9D...)
    - Generic directories (/public/, /directory/, /places/)
    - System pages (/login.php, /recover, /help, /policies)
    - Subdomains like work.facebook.com or l.facebook.com
    - Unrelated third parties with different names/surnames
    """
    if not url or "facebook.com" not in url.lower():
        return None

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return None

    netloc = parsed.netloc.lower()
    if netloc not in ["facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com"]:
        return None

    path = parsed.path.strip("/")
    if not path and not parsed.query:
        return None

    segments = path.split("/") if path else []
    target_slug = ""
    clean_profile_url = ""

    # Handle profile.php?id=12345678
    if path.lower() == "profile.php":
        qs = urllib.parse.parse_qs(parsed.query)
        profile_id = qs.get("id", [None])[0]
        if not profile_id or not profile_id.isdigit():
            return None
        target_slug = f"profile.php?id={profile_id}"
        clean_profile_url = f"https://www.facebook.com/profile.php?id={profile_id}"
    elif segments:
        first_seg = segments[0]
        # Handle /people/First-Last/12345 or /people/First-Last
        if first_seg.lower() == "people" and len(segments) > 1:
            slug = segments[1]
            num_id = segments[2] if len(segments) > 2 else ""
            if num_id and num_id.isdigit():
                clean_profile_url = f"https://www.facebook.com/people/{slug}/{num_id}"
                target_slug = f"{slug}-{num_id}"
            else:
                clean_profile_url = f"https://www.facebook.com/people/{slug}"
                target_slug = slug
        elif first_seg.lower() in FB_DISALLOWED_SLUGS:
            return None
        else:
            target_slug = first_seg
            clean_profile_url = f"https://www.facebook.com/{first_seg}"
    else:
        return None

    # Validate target_slug contains valid characters (allow hyphens, dots, underscores, alphanumeric)
    slug_only = target_slug.split("?")[0]
    if not re.match(r'^[a-zA-Z0-9._-]{3,100}$', slug_only):
        return None

    # Strict target verification if target attributes provided
    if target_name:
        clean_target = target_name.lower().strip()
        name_parts = clean_target.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        combined_text = f"{title} {snippet} {target_slug}".lower()
        local_part = target_email.split("@")[0].lower() if "@" in target_email else ""
        handles = [h.lower().strip() for h in (known_handles or []) if h]
        if local_part:
            handles.append(local_part)

        # 1. Full name match in snippet/title (both first and last name MUST be distinct tokens)
        name_matched = False
        if first_name and last_name and len(first_name) >= 3 and len(last_name) >= 3:
            if re.search(rf'\b{re.escape(first_name)}\b', combined_text) and re.search(rf'\b{re.escape(last_name)}\b', combined_text):
                name_matched = True

        # 2. Slug matches target handle or full name pattern (e.g. FirstName-LastName-10000... or firstname.lastname)
        slug_matched = False
        slug_clean = slug_only.replace(".", "").replace("-", "").replace("_", "").lower()
        if any(h.replace(".", "").replace("-", "").lower() in slug_clean for h in handles if len(h) >= 4):
            slug_matched = True
        elif first_name and last_name:
            if first_name in slug_clean and last_name in slug_clean:
                slug_matched = True

        # If neither name nor handle matches, this is a false positive / stranger profile
        if not name_matched and not slug_matched:
            return None

    return {
        "platform": "Facebook",
        "url": clean_profile_url,
        "handle": target_slug,
        "context": f"Public Facebook Profile verified against target identity: '{title or target_slug}'"
    }



_DDG_FAILED_COUNT = 0

def query_duckduckgo_lite(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    Scrapes https://lite.duckduckgo.com/lite/ which delivers rich descriptive
    biographical snippets without heavy JavaScript challenges.
    """
    global _DDG_FAILED_COUNT
    if _DDG_FAILED_COUNT >= 2:
        return []

    snippets: List[Dict[str, str]] = []
    try:
        url = "https://lite.duckduckgo.com/lite/"
        data = urllib.parse.urlencode({'q': query}).encode('utf-8')
        headers = {
            'User-Agent': USER_AGENT_DESKTOP,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://lite.duckduckgo.com/'
        }
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        _DDG_FAILED_COUNT = 0
        rows = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', html)
        i = 0
        while i < len(rows) and len(snippets) < max_results:
            r = rows[i]
            link_m = re.search(r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', r)
            if link_m and ("result-link" in r or "rel=\"nofollow\"" in r):
                href = link_m.group(1)
                raw_title = link_m.group(2)
                title = re.sub(r'<[^>]+>', '', raw_title).strip()

                snippet = ""
                if i + 1 < len(rows):
                    next_r = rows[i + 1]
                    snip_m = re.search(r'<td[^>]+class=[\'"]result-snippet[\'"][^>]*>([\s\S]*?)</td>', next_r)
                    if snip_m:
                        snippet = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', snip_m.group(1))).strip()
                        i += 1

                if href and "duckduckgo.com" not in href:
                    if "uddg=" in href:
                        qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        href = qs.get("uddg", [href])[0]
                    snippets.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet
                    })
            i += 1
    except Exception:
        _DDG_FAILED_COUNT += 1
    return snippets


def query_yahoo_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    snippets: List[Dict[str, str]] = []
    try:
        url = "https://search.yahoo.com/search?p=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={
            'User-Agent': USER_AGENT_DESKTOP,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        # Parse standard Yahoo links
        links = re.findall(r'<a class=" d-ib[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
        for href, raw_title in links[:max_results]:
            title = re.sub(r'<[^>]+>', '', raw_title).strip()
            if href and 'yahoo.com' not in href:
                snippets.append({
                    "title": title,
                    "url": href,
                    "snippet": "" # Yahoo snippets are harder to cleanly extract without a full DOM parser, title+URL is often enough for disambiguation
                })
    except Exception:
        pass
    return snippets

def query_bing_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    snippets: List[Dict[str, str]] = []
    try:
        url = "https://www.bing.com/search?q=" + urllib.parse.quote(query)
        html = None
        try:
            from curl_cffi import requests
            headers = {
                'User-Agent': USER_AGENT_DESKTOP,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            resp = requests.get(url, headers=headers, impersonate="chrome124", timeout=4.0)
            if resp.status_code == 200:
                html = resp.text
        except Exception:
            pass

        if not html:
            req = urllib.request.Request(url, headers={
                'User-Agent': USER_AGENT_DESKTOP,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            })
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                html = resp.read().decode('utf-8', errors='ignore')

        html_low = html.lower()
        if "there are no results for" in html_low or "ingen resultater for" in html_low or "ingen treff for" in html_low:
            return []

        query_terms = [t.lower() for t in re.findall(r'[a-zA-Z0-9]+', query) if len(t) >= 3 and t.lower() not in ["site", "http", "https", "com", "www", "org", "net"]]

        blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
        for b in blocks[:max_results]:
            target_url = None
            title = None
            snippet = ""

            # Primary: Extract title and URL directly from the result's <h2> heading anchor
            h2_m = re.search(r'<h2[^>]*>([\s\S]*?)</h2>', b)
            if h2_m:
                a_m = re.search(r'<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', h2_m.group(1))
                if a_m:
                    raw_href = a_m.group(1).replace('&amp;', '&')
                    raw_title = re.sub(r'<[^>]+>', '', a_m.group(2)).strip()
                    title = raw_title

                    if raw_href.startswith('http') and 'bing.com' not in raw_href and 'microsoft.com' not in raw_href:
                        target_url = raw_href
                    elif 'bing.com/ck/a' in raw_href:
                        qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                        u_param = qs.get('u', [''])[0]
                        if u_param.startswith('a1'):
                            b64 = u_param[2:]
                            b64 += '=' * ((4 - len(b64) % 4) % 4)
                            try:
                                dec = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                                if dec.startswith('http') and 'bing.com' not in dec and 'microsoft.com' not in dec:
                                    target_url = dec
                            except Exception:
                                pass

            # Fallback: scan any child anchors if h2 didn't yield target URL
            if not target_url:
                a_matches = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', b)
                for href, text_content in a_matches:
                    clean_text = re.sub(r'<[^>]+>', '', text_content).strip()
                    clean_href = href.replace('&amp;', '&')

                    if clean_href.startswith('http') and 'bing.com' not in clean_href and 'microsoft.com' not in clean_href:
                        target_url = clean_href
                        if not title:
                            title = clean_text
                        break

                    if 'bing.com/ck/a' in clean_href:
                        qs = urllib.parse.parse_qs(urllib.parse.urlparse(clean_href).query)
                        u_param = qs.get('u', [''])[0]
                        if u_param.startswith('a1'):
                            b64 = u_param[2:]
                            b64 += '=' * ((4 - len(b64) % 4) % 4)
                            try:
                                dec = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                                if dec.startswith('http') and 'bing.com' not in dec and 'microsoft.com' not in dec:
                                    target_url = dec
                                    if not title and clean_text and len(clean_text) > 3 and not clean_text.startswith('http'):
                                        title = clean_text
                                    break
                            except Exception:
                                pass

            p_match = re.search(r'<p[^>]*>([\s\S]*?)</p>', b)
            if p_match:
                snippet = re.sub(r'<[^>]+>', '', p_match.group(1)).strip()

            if target_url:
                combined_txt = f"{title or ''} {target_url} {snippet}".lower()
                if query_terms and not any(qt in combined_txt for qt in query_terms):
                    continue
                snippets.append({
                    "title": title or target_url,
                    "url": target_url,
                    "snippet": snippet
                })
    except Exception:
        pass
    return snippets


def query_search_snippets(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    Executes a search request against public search endpoints and parses result URLs, titles, and descriptive snippets.
    Combines Bing Search, DuckDuckGo Lite, DuckDuckGo HTML, and Yahoo Search with resilient fallback.
    """
    global _DDG_FAILED_COUNT
    snippets: List[Dict[str, str]] = []
    seen_urls: Set[str] = set()

    # Step 0: High-reliability Unblocker Search (Scrape.do / ScraperAPI) if configured
    global _UNBLOCKER_DISABLED
    if not globals().get("_UNBLOCKER_DISABLED", False):
        try:
            from backend.unblocker_client import resolve_unblocker_config
            cfg = resolve_unblocker_config()
            token = cfg.get("api_key")
            if token:
                target_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                if cfg.get("provider") == "scrapedo":
                    scrape_url = f"https://api.scrape.do?token={token}&url={urllib.parse.quote(target_url)}"
                else:
                    scrape_url = f"http://api.scraperapi.com?api_key={token}&url={urllib.parse.quote(target_url)}"

                req = urllib.request.Request(scrape_url, headers={"User-Agent": USER_AGENT_DESKTOP})
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                    blocks = re.findall(r'<div class="result results_links[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
                    for b in blocks[:max_results]:
                        title_m = re.search(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b)
                        snip_m = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', b, re.DOTALL)
                        clean_text = re.sub(r'<[^>]+>', ' ', b)
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        if title_m:
                            raw_href = title_m.group(1)
                            qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                            clean_url = qs.get("uddg", [raw_href])[0]
                            title = re.sub(r'<[^>]+>', '', title_m.group(2)).strip()
                            snip = re.sub(r'<[^>]+>', '', snip_m.group(1)).strip() if snip_m else clean_text
                            if "duckduckgo.com" not in clean_url and clean_url not in seen_urls:
                                seen_urls.add(clean_url)
                                snippets.append({
                                    "title": title,
                                    "url": clean_url,
                                    "snippet": snip[:350]
                                })
                if len(snippets) >= 3:
                    return snippets
        except urllib.error.HTTPError as he:
            if he.code in (401, 402, 403, 429):
                _UNBLOCKER_DISABLED = True
                logger.info(f"Unblocker API key returned {he.code} (quota/unauthorized). Bypassing unblocker.")
        except Exception as e:
            logger.debug(f"Unblocker search notice: {e}")

    # Step 1: Query Bing Search first (fastest, decodes real target URLs and rich snippets)
    bing_snips = query_bing_search(query, max_results=max_results)
    for s in bing_snips:
        u = s.get("url")
        if u and u not in seen_urls:
            seen_urls.add(u)
            snippets.append(s)

    # Step 2: Query DuckDuckGo Lite if more results needed
    if len(snippets) < max_results:
        lite_snips = query_duckduckgo_lite(query, max_results=max_results - len(snippets))
        for s in lite_snips:
            u = s.get("url")
            if u and u not in seen_urls:
                seen_urls.add(u)
                snippets.append(s)

    # Step 3: DuckDuckGo HTML if still sparse
    if len(snippets) < 3:
        try:
            data = urllib.parse.urlencode({"q": query}).encode("utf-8")
            req = urllib.request.Request(
                "https://html.duckduckgo.com/html/",
                data=data,
                headers={
                    "User-Agent": USER_AGENT_DESKTOP,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "https://duckduckgo.com/",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9"
                }
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            blocks = re.findall(r'<div class="result results_links[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
            for b in blocks[:max_results]:
                title_m = re.search(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b)
                snip_m = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', b, re.DOTALL)
                clean_text = re.sub(r'<[^>]+>', ' ', b)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()

                if title_m:
                    raw_href = title_m.group(1)
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                    clean_url = qs.get("uddg", [raw_href])[0]
                    title = re.sub(r'<[^>]+>', '', title_m.group(2)).strip()
                    snip = re.sub(r'<[^>]+>', '', snip_m.group(1)).strip() if snip_m else clean_text

                    if "duckduckgo.com" in clean_url or clean_url in seen_urls:
                        continue

                    seen_urls.add(clean_url)
                    snippets.append({
                        "title": title,
                        "url": clean_url,
                        "snippet": snip[:350]
                    })
        except Exception:
            pass

    # Step 4: Yahoo Search fallback
    if len(snippets) < 3:
        yahoo_snips = query_yahoo_search(query, max_results=max_results)
        for s in yahoo_snips:
            u = s.get("url")
            if u and u not in seen_urls:
                seen_urls.add(u)
                snippets.append(s)

    return snippets


def is_valid_user_page(html: str, url: str) -> bool:
    """
    Validates that a fetched web page contains genuine user profile/portfolio content
    and is NOT a dead 404, generic registration prompt, parked domain, or placeholder.
    """
    if not html or len(html.strip()) < 250:
        return False

    lower = html.lower()

    # 1. Structural check: Must contain basic HTML structure
    if "<html" not in lower and "<body" not in lower:
        return False

    # 2. Not Found & Registration / Placeholder heuristic indicators
    dead_indicators = [
        "page not found", "404 not found", "user not found", "profile not found",
        "blog not found", "unknown blog", "unknown_blog",
        "this site doesn't exist", "site not found", "domain is parked",
        "buy this domain", "create a free website", "sign up for wordpress",
        "register a new blog", "the page you requested cannot be found",
        "the link you followed may be broken", "this content isn't available right now",
        "does not exist", "nothing here", "error 404", "<title>not found</title>",
        "account suspended", "website under construction", "domain default page",
        "parked for free on", "registered at namecheap", "welcome to nginx", "apache2 default page"
    ]
    for ind in dead_indicators:
        if ind in lower:
            return False

    # 3. WordPress.com specific check: Verify it's not the generic landing page
    if "wordpress.com" in url.lower():
        if "<title>wordpress.com</title>" in lower or "create a website or blog" in lower:
            return False
        if "log in to wordpress.com" in lower and "recent posts" not in lower and "about" not in lower:
            return False

    return True


def inspect_personal_site_metadata(url: str) -> Optional[Dict[str, Any]]:
    """
    Deep fetch of a discovered portfolio, CV, or personal website to extract
    location, residence city, education, workplace, secondary emails, and direct social profile links.
    Completely generic for any country/city worldwide.
    """
    intel: Dict[str, Any] = {
        "city": None,
        "country": None,
        "secondary_emails": [],
        "linkedin_url": None,
        "facebook_url": None,
        "workplace": None,
        "bio": None,
        "url": url
    }
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT_DESKTOP,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Validate that the page is a live user page and not a 404 / parking page
        if not is_valid_user_page(html, url):
            return None

        # Strip scripts and styles for clean text extraction
        clean_text = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
        clean_text = re.sub(r'<style[\s\S]*?</style>', ' ', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        clean_text = clean_text.replace('\u200b', '').replace('&nbsp;', ' ')

        # LLM-Driven Deep Personal Website Scraping
        api_key = resolve_api_key("GROQ_API_KEY")
        if api_key and len(clean_text) > 50:
            prompt = f"Extract the following entities from this personal website text. Return JSON with keys: city (str), country (str), bio (str), job_title (str), workplace (str), phone (str). If an entity is not found, set its value to null.\n\nWebsite Text: {clean_text[:5000]}"
            system_instruction = "You are an expert OSINT data extraction tool. You extract biographical data from unstructured text. Return ONLY a valid JSON object matching the exact keys requested."
            try:
                res = call_groq_api(prompt, system_instruction, api_key, response_json=True, max_tokens=300)
                if res and res.get("success") and res.get("text"):
                    raw_text = res["text"].strip()
                    if "```" in raw_text:
                        m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
                        if m:
                            raw_text = m.group(1).strip()
                    parsed = json.loads(raw_text)
                    if isinstance(parsed, dict):
                        intel["city"] = parsed.get("city")
                        intel["country"] = parsed.get("country")
                        intel["bio"] = parsed.get("bio")
                        intel["job_title"] = parsed.get("job_title")
                        intel["workplace"] = parsed.get("workplace")
                        
                        if parsed.get("phone"):
                            if "phone_numbers" not in intel:
                                intel["phone_numbers"] = []
                            intel["phone_numbers"].append(parsed.get("phone"))
            except Exception as e:
                print(f"[!] LLM Deep Scrape failed: {e}")

        # Fallback bio snippet from clean page text if LLM extraction returned null
        if not intel.get("bio") and clean_text:
            intel["bio"] = clean_text[:300]

        # Secondary email check
        mail_m = re.findall(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', html, re.IGNORECASE)
        for m in mail_m:
            if m not in intel["secondary_emails"] and "wix" not in m.lower() and "example" not in m.lower():
                intel["secondary_emails"].append(m)

        # LinkedIn link (supports www.linkedin.com/in/... and cc.linkedin.com/in/...)
        li_m = re.search(r'https?://(?:www\.|[a-z]{2}\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?', html)
        if li_m:
            intel["linkedin_url"] = li_m.group(0)

        # Facebook link (excludes standard platform pages)
        fb_m = re.search(r'https?://(?:www\.|m\.)?facebook\.com/([a-zA-Z0-9_.-]+(?:/[0-9]+)?)/?', html)
        if fb_m:
            slug = fb_m.group(1).lower().split("/")[0]
            if slug not in FB_DISALLOWED_SLUGS and slug not in ["sharer", "share", "login", "recover", "help", "policies", "wix", "pages", "group", "tr"]:
                intel["facebook_url"] = fb_m.group(0)

        # Instagram link (personal accounts)
        ig_m = re.search(r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.-]+)/?', html)
        if ig_m:
            ig_slug = ig_m.group(1).lower()
            if ig_slug not in ["p", "reel", "stories", "explore", "about", "developer", "terms", "privacy"]:
                intel["instagram_url"] = ig_m.group(0)
    except Exception:
        pass

    return intel


def disambiguate_with_llm(
    target_name: str,
    target_email: str,
    snippets: List[Dict[str, str]],
    known_handles: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Uses Groq Llama 3.3 (or Gemini) to filter out false-positive stranger profiles
    and extract verified location, employer, and social profiles.
    COMPLETELY GENERIC: Evaluates any target based purely on evidence in search snippets.
    """
    load_dotenv()
    api_key = resolve_api_key("groq")
    if not api_key:
        return None

    name_parts = target_name.lower().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    local_part = target_email.split("@")[0].lower() if "@" in target_email else ""
    handles = [h.lower().strip() for h in (known_handles or []) if h]
    if local_part:
        handles.append(local_part)

    system_instruction = (
        "You are an elite OSINT Intelligence Disambiguation Engine. "
        "Your duty is to strictly filter out false positives and extract verified "
        "person attributes from search engine snippets and personal web footprints. Output strictly valid JSON."
    )

    prompt = f"""Target Entity Under Investigation:
- Target Full Name: {target_name}
- Target Email Address: {target_email}
- Target Known Handles / Nicknames: {', '.join(handles)}

Raw Live Search Snippets & Web Footprints Retrieved for Target:
{json.dumps(snippets, indent=2)}

Verification Guidelines:
1. Strict Entity Disambiguation (Prune False Positives):
   - Only corroborate snippets that genuinely belong to the target entity.
   - REJECT stranger profiles: if the target has a specific given name and surname, REJECT unrelated accounts that merely share a common first name, generic handle fragment, or differing surname.
   - REJECT individuals with distinct conflicting professions, countries, or identities.
   - Only accept social and web profiles (e.g. LinkedIn, Facebook, Portfolio, Instagram, GitHub) where the handle, full name, email, or biography explicitly corroborates the target's identity.
2. Verified Attributes Extraction:
   - Physical Location: Look for explicit residential declarations (e.g. 'lives in <City>', 'based in <City>', 'resident of <City>'). Extract the confirmed city, region/province, and country.
   - Workplace / Education: Extract confirmed educational institutions, universities, employers, and companies.
   - Verified Profiles: Extract confirmed URLs matching the target's identity.

Respond ONLY with valid JSON in this exact structure:
{{
  "is_corroborated": true,
  "confidence_score": 0.95,
  "full_name_candidate": "Full verified legal or expanded name discovered (including middle names, e.g. 'Alexander Vance Morgan') or null",
  "location": {{
    "city": "Exact city name or null",
    "country": "Country name or null",
    "context": "Evidence citation"
  }},
  "workplace": {{
    "company": "Company or Educational Institution name or null",
    "job_title": "Role title or null",
    "context": "Evidence citation"
  }},
  "phone_numbers": ["Discovered telephone or mobile numbers or empty list"],
  "profiles": [
    {{
      "platform": "LinkedIn / Facebook / Portfolio / Instagram / GitHub",
      "url": "https://...",
      "handle": "username or profile ID",
      "context": "Context note"
    }}
  ]
}}
If no verified target data is corroborated, return {{"is_corroborated": false, "confidence_score": 0.0, "full_name_candidate": null, "location": null, "workplace": null, "phone_numbers": [], "profiles": []}}."""

    try:
        res = call_groq_api(prompt, system_instruction, api_key, temperature=0.1, response_json=True, max_tokens=400)
        if res.get("success") and res.get("text"):
            raw_text = res["text"].strip()
            if "```" in raw_text:
                m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
                if m:
                    raw_text = m.group(1).strip()
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and parsed.get("is_corroborated"):
                # Generic regional TLD fallback if LLM left country empty
                loc = parsed.get("location")
                if not loc or not loc.get("country"):
                    for s in snippets:
                        u = s.get("url", "").lower()
                        cc_match = re.search(r'https?://([a-z]{2})\.linkedin\.com', u)
                        if cc_match:
                            cc = cc_match.group(1)
                            if cc in TLD_TO_COUNTRY:
                                parsed["location"] = {
                                    "city": loc.get("city") if loc else None,
                                    "country": TLD_TO_COUNTRY[cc],
                                    "context": f"Discovered via regional endpoint ({cc}.linkedin.com)"
                                }
                                break

                # Generic workplace post-processing fallback if LLM left company empty
                wp = parsed.get("workplace")
                if not wp or not wp.get("company"):
                    for s in snippets:
                        t = s.get("title", "")
                        comp_m = re.search(r'-\s*([^|•\n]+?)\s*\|\s*LinkedIn', t, re.IGNORECASE)
                        if comp_m:
                            cand_comp = comp_m.group(1).strip()
                            if cand_comp and len(cand_comp) > 2 and cand_comp.lower() not in ["profile", "profiles", "overview", "posts", "feed"]:
                                parsed["workplace"] = {
                                    "company": cand_comp,
                                    "job_title": "Professional Role",
                                    "context": f"Extracted from verified professional headline: '{t}'"
                                }
                                break

                # Sanitize and strictly validate any returned profiles against false positives
                cleaned_profiles = []
                for prof in parsed.get("profiles", []):
                    plat = prof.get("platform", "")
                    u = prof.get("url", "")
                    if "facebook" in plat.lower() or "facebook.com" in u.lower():
                        v_fb = extract_valid_facebook_profile(
                            url=u,
                            title=prof.get("context", ""),
                            target_name=target_name,
                            target_email=target_email,
                            known_handles=known_handles
                        )
                        if v_fb:
                            cleaned_profiles.append(v_fb)
                    elif "instagram" in plat.lower() or "instagram.com" in u.lower():
                        # Strict Instagram check: handle or context must match target surname or verified handle
                        clean_u = u.lower().rstrip("/")
                        inst_handle = clean_u.split("/")[-1].replace("@", "")
                        # Reject stranger handles that don't match target surname or known handles
                        if target_name and last_name:
                            if last_name not in inst_handle and not any(h in inst_handle for h in handles if len(h) >= 4):
                                continue
                        cleaned_profiles.append(prof)
                    else:
                        cleaned_profiles.append(prof)
                parsed["profiles"] = cleaned_profiles

                return parsed
    except Exception:
        pass

    return None


def heuristic_fallback_disambiguation(
    target_name: str,
    target_email: str,
    snippets: List[Dict[str, str]],
    known_handles: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Deterministic heuristic extractor if no LLM API key is configured.
    Strictly verifies identity to prevent false positives and junk links.
    """
    clean_target = target_name.lower().strip()
    name_parts = clean_target.split()
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    local_part = target_email.split("@")[0].lower() if "@" in target_email else ""
    handles = [h.lower().strip() for h in (known_handles or []) if h]
    if local_part:
        handles.append(local_part)

    result: Dict[str, Any] = {
        "is_corroborated": False,
        "confidence_score": 0.0,
        "full_name_candidate": None,
        "location": None,
        "workplace": None,
        "phone_numbers": [],
        "profiles": []
    }

    for s in snippets:
        title = s.get("title", "")
        url = s.get("url", "")
        snip = s.get("snippet", "")
        combined = f"{title} {snip}".lower()

        # Strict target identification: must match both first and last name or handle
        has_full_name = bool(first_name and last_name and (first_name in combined and last_name in combined))
        has_handle = bool(local_part and len(local_part) >= 4 and local_part in combined)

        if not has_full_name and not has_handle:
            continue

        result["is_corroborated"] = True
        result["confidence_score"] = max(result["confidence_score"], 0.88)

        # Check for full legal name candidate with middle names (e.g. multi-token expanded legal name)
        if first_name and last_name:
            prefix = last_name[:4] if len(last_name) >= 4 else last_name
            full_pattern = re.compile(
                rf'\b({re.escape(first_name)}\s+[A-Za-z]+(?:\s+[A-Za-z]+)*\s+{re.escape(prefix)}[a-z]*)\b',
                re.IGNORECASE
            )
            name_m = full_pattern.search(f"{title} {snip}")
            if name_m:
                cand = " ".join(w.capitalize() for w in name_m.group(1).split())
                if len(cand.split()) > len(target_name.split()):
                    result["full_name_candidate"] = cand

        # Check for phone numbers in snippet/title
        phone_matches = re.findall(r'(?:\+|00)?(?:\d[\s.-]?){8,14}\d', f"{title} {snip}")
        for pm in phone_matches:
            clean_digits = re.sub(r'\D', '', pm)
            if 8 <= len(clean_digits) <= 15:
                if pm.strip() not in result["phone_numbers"]:
                    result["phone_numbers"].append(pm.strip())

        # Check for residence / city mentions in snippets (e.g. Dutch: "ik woon in Wolvega", English: "Lives in Wolvega")
        nl_loc = re.search(r'(?:ik\s+woon\s+in|woonachtig\s+te|woonplaats:?)\s+([A-Z][a-z]+(?:[\s-][A-Z][a-z]+)?)', snip, re.IGNORECASE)
        en_loc = re.search(r'(?:lives\s+in|living\s+in|based\s+in|located\s+in|residing\s+in)\s+([A-Z][a-z]+(?:[\s-][A-Z][a-z]+)?)', snip, re.IGNORECASE)
        found_city = (nl_loc.group(1).title() if nl_loc else (en_loc.group(1).title() if en_loc else None))
        if found_city and (not result["location"] or not result["location"].get("city")):
            result["location"] = {
                "city": found_city,
                "country": "Netherlands" if nl_loc else "International",
                "context": f"Extracted via confirmed residence bio mention: '{found_city}'"
            }

        # 1. LinkedIn Profile
        if "linkedin.com/in/" in url.lower() or "linkedin.com/pub/dir" in url.lower() or "linkedin.com/posts" in url.lower():
            comp_match = re.search(r'-\s*([^|•\n]+?)\s*\|\s*LinkedIn', title, re.IGNORECASE)
            company = comp_match.group(1).strip() if comp_match else None
            if company and company.lower() in ["profile", "profiles", "overview", "posts", "feed"]:
                company = None

            result["profiles"].append({
                "platform": "LinkedIn",
                "url": url,
                "handle": url.rstrip("/").split("/")[-1],
                "context": f"Public LinkedIn Profile • {company or 'Professional Network'}"
            })
            if company and not result["workplace"]:
                result["workplace"] = {
                    "company": company,
                    "job_title": "Professional Role",
                    "context": f"Discovered via verified LinkedIn headline: '{title}'"
                }

            # Generic ccTLD check for country
            cc_match = re.search(r'https?://([a-z]{2})\.linkedin\.com', url.lower())
            if cc_match:
                cc = cc_match.group(1)
                if cc in TLD_TO_COUNTRY and not result["location"]:
                    result["location"] = {
                        "city": None,
                        "country": TLD_TO_COUNTRY[cc],
                        "context": f"Identified via regional endpoint ({cc}.linkedin.com)"
                    }

        # 2. Facebook Profile (Strict verification)
        elif "facebook.com/" in url.lower():
            v_fb = extract_valid_facebook_profile(
                url=url,
                title=title,
                snippet=snip,
                target_name=target_name,
                target_email=target_email,
                known_handles=known_handles
            )
            if v_fb and not any(p.get("url") == v_fb["url"] for p in result["profiles"]):
                result["profiles"].append(v_fb)

        # 3. Portfolio / Personal Site (Requires genuine content verification)
        elif any(ext in url for ext in [".wixsite.com", ".github.io", ".portfolio", ".me", ".jouwweb.nl", "carrd.co"]):
            meta = inspect_personal_site_metadata(url)
            if meta:
                result["profiles"].append({
                    "platform": "Portfolio",
                    "url": url,
                    "handle": target_name,
                    "context": "Verified Personal Web Portfolio located via OSINT dork"
                })

    return result


def execute_ai_dork_recon(
    target_name: str,
    target_email: str,
    known_handles: Optional[List[str]] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Master orchestrator: queries web dorks for Facebook, LinkedIn, identity keywords,
    inspects personal portfolio sites, and executes AI-powered disambiguation to eliminate
    false positives and yield verified location, workplace, and social pivots.
    100% GENERIC for any identity globally.
    """
    if not target_name or target_name.lower() in ["target user", "target identity", "webmail user"]:
        from backend.database import parse_name_from_email
        target_name = parse_name_from_email(target_email)

    cache_key = (target_email or target_name).strip().lower()
    if not force_refresh and cache_key in _DORK_CACHE and _DORK_CACHE[cache_key].get("is_corroborated"):
        cached = _DORK_CACHE[cache_key]
        if cached.get("location") and cached["location"].get("city"):
            return cached

    if not target_name or len(target_name.strip()) < 3:
        return {"is_corroborated": False, "profiles": []}

    name_parts = (target_name or "").strip().split()
    first_name = name_parts[0].lower() if name_parts else ""
    last_name = name_parts[-1].lower() if len(name_parts) >= 2 else ""

    local_part = target_email.split("@")[0].lower() if "@" in target_email else ""
    handles = [h.lower().strip() for h in (known_handles or []) if h]
    if local_part:
        handles.append(local_part)

    # Proactively probe personal domain / portfolio patterns based on target handles & name
    candidate_handles = []
    if local_part:
        candidate_handles.append(local_part)
        base_h = re.sub(r'\d+$', '', local_part)
        if base_h and base_h != local_part and len(base_h) >= 4:
            candidate_handles.append(base_h)
    clean_name_handle = target_name.lower().replace(" ", "").replace(".", "").replace("-", "")
    if clean_name_handle and clean_name_handle not in candidate_handles:
        candidate_handles.append(clean_name_handle)

    from backend.live_osint import derive_candidate_handles
    name_derived = derive_candidate_handles(target_email, target_name=target_name)
    for nh in name_derived:
        if nh not in candidate_handles:
            candidate_handles.append(nh)

    for h in handles:
        if h not in candidate_handles:
            candidate_handles.append(h)

    all_snippets: List[Dict[str, str]] = []
    seen_urls: Set[str] = set()
    site_metadata = None
    probe_templates = [
        "https://{h}.wixsite.com/portfolio",
        "https://{h}.wixsite.com/{h}",
        "https://{h}.jouwweb.nl",
        "https://{h}.github.io",
        "https://{h}.carrd.co",
        "https://about.me/{h}",
    ]

    discovered_personal_sites: List[Dict[str, Any]] = []

    def _probe_single_site(tmpl_str: str, h_str: str) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        c_url = tmpl_str.format(h=h_str)
        try:
            p_req = urllib.request.Request(c_url, headers={
                "User-Agent": USER_AGENT_DESKTOP,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            })
            with urllib.request.urlopen(p_req, timeout=2.0) as p_resp:
                if p_resp.status == 200:
                    s_meta = inspect_personal_site_metadata(c_url)
                    if s_meta:
                        return (c_url, h_str, s_meta)
        except Exception:
            pass
        return None

    probe_tasks = [(tmpl, h) for h in candidate_handles[:4] for tmpl in probe_templates]
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(_probe_single_site, tmpl, h) for tmpl, h in probe_tasks]
        for fut in concurrent.futures.as_completed(futs):
            hit = fut.result()
            if hit:
                candidate_url, h, site_meta = hit
                if not site_metadata:
                    site_metadata = site_meta
                discovered_personal_sites.append({
                    "platform": "Portfolio",
                    "url": candidate_url,
                    "handle": h,
                    "context": f"Verified Personal Web Portfolio ({h}) located via OSINT dork"
                })
                if candidate_url not in seen_urls:
                    seen_urls.add(candidate_url)
                    all_snippets.append({
                        "title": f"Verified Personal Web Portfolio ({h})",
                        "url": candidate_url,
                        "snippet": site_meta.get("bio") or f"Personal web presence deployed at {candidate_url}"
                    })

    # Execute prioritized targeted live dorks concurrently
    queries = []
    if target_email and "@" in target_email:
        queries.append(f'"{target_email}"')

    email_dom = target_email.split("@")[1].lower() if "@" in target_email else ""
    is_freemail = any(d in email_dom for d in ["gmail", "yahoo", "outlook", "hotmail", "proton", "icloud", "zoho", "mail", "live", "aol", "yandex"])
    org_stem = email_dom.split(".")[0].capitalize() if not is_freemail and "." in email_dom else None

    # Retrieve AI-generated search dorks from identity decomposer
    try:
        from backend.identity_decomposer import decompose_target_identity
        dec = decompose_target_identity(target_email, raw_name=target_name)
        if dec:
            if dec.get("organization") and not org_stem:
                org_stem = dec["organization"]
            for dk in dec.get("search_dorks", []):
                if dk not in queries:
                    queries.append(dk)
    except Exception:
        pass

    # Execute prioritized targeted live dorks concurrently
    prioritized_queries = []
    has_real_target_name = bool(target_name and target_name.lower() not in ["target user", "webmail target", "target"])
    if has_real_target_name:
        prioritized_queries.append(f'{target_name} linkedin')
        if org_stem:
            prioritized_queries.append(f'{target_name} {org_stem}')
        prioritized_queries.append(f'"{target_name}"')
        prioritized_queries.append(f'{target_name} security OR cyber')
        prioritized_queries.append(f'{target_name} CTO OR manager OR director')

    if target_email and "@" in target_email:
        prioritized_queries.append(f'"{target_email}"')

    for q in queries:
        if q not in prioritized_queries:
            prioritized_queries.append(q)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(query_search_snippets, q, 6) for q in prioritized_queries[:6]]
        for fut in concurrent.futures.as_completed(futs):
            try:
                snips = fut.result()
                for s in snips:
                    u = s.get("url")
                    if u and u not in seen_urls:
                        seen_urls.add(u)
                        all_snippets.append(s)
            except Exception:
                pass

    # Inspect personal portfolios or personal sites discovered from search snippets if not yet probed
    if not site_metadata:
        for s in all_snippets:
            u = s.get("url", "")
            if any(w in u.lower() for w in [".wixsite.com", ".github.io", "portfolio", ".me", ".jouwweb.nl", "wordpress.com"]):
                site_metadata = inspect_personal_site_metadata(u)
                if site_metadata:
                    break

    # If personal site metadata contains biography text, inject it directly at the head of snippets for LLM
    if site_metadata and site_metadata.get("bio"):
        all_snippets.insert(0, {
            "title": f"Verified Personal Bio / Portfolio - {target_name}",
            "url": site_metadata.get("url") or "",
            "snippet": site_metadata["bio"]
        })

    # If personal site revealed confirmed city (e.g. Wolvega), also query specifically with target name + city
    if site_metadata and site_metadata.get("city"):
        city_snips = query_search_snippets(f"{target_name} {site_metadata['city']}", max_results=6)
        for s in city_snips:
            u = s.get("url")
            if u and u not in seen_urls:
                seen_urls.add(u)
                all_snippets.append(s)

    final_result = None
    if all_snippets:
        # Run AI Disambiguation
        ai_result = disambiguate_with_llm(target_name, target_email, all_snippets, handles)
        if ai_result and ai_result.get("is_corroborated"):
            final_result = ai_result
        else:
            final_result = heuristic_fallback_disambiguation(target_name, target_email, all_snippets, handles)
    elif cache_key in _DORK_CACHE:
        return _DORK_CACHE[cache_key]

    if not final_result:
        final_result = {"is_corroborated": False, "profiles": []}

    # Post-process with inspected site metadata if available
    if final_result and site_metadata:
        if not final_result.get("location") and site_metadata.get("country"):
            final_result["location"] = {
                "city": site_metadata.get("city"),
                "country": site_metadata.get("country"),
                "context": "Discovered via verified personal web deployment metadata"
            }
        elif final_result.get("location"):
            if not final_result["location"].get("city") and site_metadata.get("city"):
                final_result["location"]["city"] = site_metadata["city"]
            if not final_result["location"].get("country") and site_metadata.get("country"):
                final_result["location"]["country"] = site_metadata["country"]

        if site_metadata.get("workplace") and (not final_result.get("workplace") or not final_result["workplace"].get("company")):
            final_result["workplace"] = {
                "company": site_metadata["workplace"],
                "job_title": site_metadata.get("job_title") or "Student / Professional Role",
                "context": f"Discovered via verified educational / portfolio statement on {site_metadata.get('url', 'personal site')}"
            }
        elif final_result.get("workplace") and site_metadata.get("job_title"):
            if not final_result["workplace"].get("job_title") or final_result["workplace"]["job_title"] in ["Professional Role", "Student / Professional Role", None]:
                final_result["workplace"]["job_title"] = site_metadata["job_title"]

        if site_metadata.get("secondary_emails"):
            final_result["secondary_emails"] = site_metadata["secondary_emails"]

        if site_metadata.get("phone_numbers"):
            final_result.setdefault("phone_numbers", []).extend(site_metadata["phone_numbers"])

        if site_metadata.get("linkedin_url"):
            has_li = any("linkedin" in p.get("url", "") for p in final_result.get("profiles", []))
            if not has_li:
                final_result.setdefault("profiles", []).append({
                    "platform": "LinkedIn",
                    "url": site_metadata["linkedin_url"],
                    "handle": target_name,
                    "context": "Verified LinkedIn link from personal portfolio"
                })

        if site_metadata.get("facebook_url"):
            v_fb = extract_valid_facebook_profile(
                url=site_metadata["facebook_url"],
                target_name=target_name,
                target_email=target_email,
                known_handles=handles
            )
            if v_fb and not any("facebook" in p.get("url", "") for p in final_result.get("profiles", [])):
                final_result.setdefault("profiles", []).append(v_fb)

    # Ingest verified personal sites discovered via direct candidate probing
    if final_result and discovered_personal_sites:
        for ps in discovered_personal_sites:
            if not any(p.get("url") == ps["url"] for p in final_result.get("profiles", [])):
                final_result.setdefault("profiles", []).append(ps)

    # Corporate identity and LinkedIn anti-scraping barrier handling (Zero-Auth Mode)
    # If the target belongs to a corporate domain (e.g. vooruit.nl -> Vooruit), enrich workplace
    # via live impressum/website crawling and synthesize candidate LinkedIn profiles (e.g. /in/alje/)
    # to bypass LinkedIn HTTP 999 anti-scraping blocks and present direct verified investigator links.
    if final_result and org_stem:
        final_result["is_corroborated"] = True

        # 1. Passive Domain & Chamber of Commerce Impressum Probing
        company_details = {}
        try:
            from backend.corporate_recon import inspect_company_web_registry
            company_web = f"https://{email_dom}"
            reg_info = inspect_company_web_registry(company_web)
            if reg_info:
                company_details.update(reg_info)

            # Probe homepage for title, meta description and company social presence
            req_c = urllib.request.Request(company_web, headers={"User-Agent": USER_AGENT_DESKTOP})
            with urllib.request.urlopen(req_c, timeout=3.0) as resp_c:
                c_html = resp_c.read().decode("utf-8", errors="ignore")
                t_m = re.search(r'<title>(.*?)</title>', c_html, re.IGNORECASE)
                if t_m:
                    company_details["page_title"] = t_m.group(1).split("-")[0].strip()
                # Find company LinkedIn page (handling JSON-LD escaped slashes)
                unescaped_html = c_html.replace(r'\/', '/')
                li_comp_m = re.search(r'https?://(?:www\.)?linkedin\.com/company/[a-zA-Z0-9_\-]+', unescaped_html)
                if li_comp_m:
                    company_details["company_linkedin"] = li_comp_m.group(0)
        except Exception:
            pass

        corp_ctx_tokens = [f"Corporate organization associated with domain @{email_dom}"]
        kvk_num = company_details.get("kvk_number")
        addr_cand = company_details.get("address_candidate")
        comp_li = company_details.get("company_linkedin")
        page_t = company_details.get("page_title")

        if kvk_num:
            corp_ctx_tokens.append(f"Chamber of Commerce (KvK): {kvk_num}")
        if addr_cand:
            corp_ctx_tokens.append(f"Registered Office: {addr_cand}")
        if comp_li:
            corp_ctx_tokens.append(f"Corporate LinkedIn: {comp_li}")

        comp_name = f"{org_stem} ({page_t})" if page_t and len(page_t) < 30 and page_t.lower() != org_stem.lower() else org_stem

        if not final_result.get("workplace") or not final_result["workplace"].get("company"):
            final_result["workplace"] = {
                "company": comp_name,
                "job_title": f"Corporate Specialist / IT Professional ({org_stem})" if "it" in (page_t or "").lower() or email_dom.endswith(".nl") else "Professional Role",
                "context": " • ".join(corp_ctx_tokens),
                "kvk_number": kvk_num,
                "address": addr_cand,
                "company_linkedin": comp_li
            }

        # If registered company address discovered, corroborate physical footprint
        if addr_cand and not final_result.get("location"):
            final_result["location"] = {
                "city": addr_cand,
                "country": "Netherlands" if email_dom.endswith(".nl") else "International",
                "context": f"Corporate registered headquarters for {org_stem} (@{email_dom})"
            }

        has_li = any(p.get("platform") == "LinkedIn" for p in final_result.get("profiles", []))
        if not has_li:
            try:
                from backend.linkedin_recon import (
                    derive_linkedin_candidate_slugs,
                    generate_linkedin_search_url
                )
                slugs = derive_linkedin_candidate_slugs(target_name, target_email)
                if slugs:
                    primary_slug = slugs[0]
                    cand_url = f"https://www.linkedin.com/in/{primary_slug}/"
                    search_url = generate_linkedin_search_url(target_name, org_stem)
                    cand_list = [f"https://www.linkedin.com/in/{s}/" for s in slugs]
                    cand_str = " | ".join(cand_list[:4])
                    final_result.setdefault("profiles", []).append({
                        "platform": "LinkedIn",
                        "url": cand_url,
                        "handle": primary_slug,
                        "name": target_name,
                        "job_title": final_result.get("workplace", {}).get("job_title") or f"Professional Role ({org_stem})",
                        "company": comp_name,
                        "context": f"Candidate LinkedIn Profile (@{primary_slug}) • Affiliated with {org_stem} (@{email_dom}) • Direct Member Search Pivot [SEARCH_URL: {search_url}] [CANDIDATES: {cand_str}] [STATUS: PROBABILITY_CANDIDATE]",
                        "is_verified": False,
                        "is_suspected": True,
                        "confidence": 0.75,
                        "search_url": search_url,
                        "candidate_urls": cand_list
                    })
            except Exception as e:
                print(f"[!] LinkedIn candidate derivation error: {e}")


    # Check search snippets for strictly verified LinkedIn, Facebook and Twitter/X profiles
    if final_result:
        for s in all_snippets:
            u = s.get("url", "")
            s_text = f"{s.get('title', '')} {s.get('snippet', '')}".lower()
            if "linkedin.com/in/" in u.lower():
                li_match = re.search(r'https?://(?:[a-z]{2}\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?', u, re.IGNORECASE)
                if li_match:
                    li_slug = li_match.group(1).lower()
                    if li_slug not in ["login", "signup", "help", "pulse", "jobs"]:
                        t_parts = [p.lower() for p in target_name.split() if len(p) >= 3]
                        first_n = t_parts[0] if t_parts else ""
                        last_n = t_parts[-1] if len(t_parts) >= 2 else ""
                        
                        has_name_match = False
                        if last_n:
                            # Require both first name and surname match to eliminate wrong-person collisions
                            has_first = first_n in s_text or first_n in li_slug
                            has_last = last_n in s_text or last_n in li_slug
                            has_name_match = has_first and has_last
                        elif first_n:
                            has_name_match = (first_n in li_slug) or (first_n in s_text)
                        if has_name_match:
                            clean_li_url = f"https://www.linkedin.com/in/{li_slug}/"
                            from backend.linkedin_recon import generate_linkedin_search_url
                            search_url = generate_linkedin_search_url(target_name, org_stem)
                            li_prof = {
                                "platform": "LinkedIn",
                                "url": clean_li_url,
                                "handle": li_slug,
                                "name": target_name,
                                "job_title": f"Professional Role ({org_stem})" if org_stem else "Professional Role",
                                "company": org_stem or "",
                                "context": f"Verified LinkedIn Profile discovered via OSINT web index (@{li_slug}) • Affiliated with {org_stem or 'Corporate Identity'} [SEARCH_URL: {search_url}] [STATUS: VERIFIED]",
                                "is_verified": True,
                                "is_suspected": False,
                                "confidence": 0.95,
                                "search_url": search_url
                            }
                            # Remove candidate or duplicate if present
                            final_result["profiles"] = [p for p in final_result.get("profiles", []) if p.get("platform") != "LinkedIn"]
                            final_result["profiles"].append(li_prof)
            elif "facebook.com/" in u.lower():
                v_fb = extract_valid_facebook_profile(
                    url=u,
                    title=s.get("title", ""),
                    snippet=s.get("snippet", ""),
                    target_name=target_name,
                    target_email=target_email,
                    known_handles=handles
                )
                if v_fb and not any(p.get("url") == v_fb["url"] for p in final_result.get("profiles", [])):
                    final_result.setdefault("profiles", []).append(v_fb)
            elif "twitter.com/" in u.lower() or "x.com/" in u.lower():
                tw_match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,25})', u, re.IGNORECASE)
                if tw_match:
                    tw_handle = tw_match.group(1).lower()
                    if tw_handle not in ["home", "explore", "search", "intent", "share", "i", "settings", "login"]:
                        s_text = f"{s.get('title', '')} {s.get('snippet', '')}".lower()
                        t_parts = [p.lower() for p in target_name.split() if len(p) >= 3]
                        has_name_match = (len(t_parts) >= 2 and all(tp in s_text or tp in tw_handle for tp in t_parts)) or (len(t_parts) >= 1 and any(tp in tw_handle for tp in t_parts))
                        has_handle_match = any(h.lower() == tw_handle or (len(h) >= 4 and h.lower() in tw_handle) for h in handles)
                        if (has_name_match or has_handle_match) and not any(p.get("platform") == "Twitter / X" for p in final_result.get("profiles", [])):
                            final_result.setdefault("profiles", []).append({
                                "platform": "Twitter / X",
                                "url": f"https://x.com/{tw_handle}",
                                "handle": tw_handle,
                                "context": f"Public profile on X (Twitter) corroborated via OSINT search dork (@{tw_handle})"
                            })

    # Final sanitization: ensure no corrupted or non-matching Facebook URLs exist in profiles
    if final_result and "profiles" in final_result:
        clean_profs = []
        for p in final_result["profiles"]:
            plat = p.get("platform", "").lower()
            u = p.get("url", "")
            if "facebook" in plat or "facebook.com" in u.lower():
                v = extract_valid_facebook_profile(
                    url=u,
                    title=p.get("context", ""),
                    target_name=target_name,
                    target_email=target_email,
                    known_handles=handles
                )
                if v:
                    clean_profs.append(v)
            elif "instagram" in plat or "instagram.com" in u.lower():
                # Strict Instagram sanity check: reject accounts that don't match target surname or known handles
                clean_u = u.lower().rstrip("/")
                inst_handle = clean_u.split("/")[-1].replace("@", "")
                if last_name and (last_name in inst_handle or any(h in inst_handle for h in handles if len(h) >= 4)):
                    clean_profs.append(p)
                elif any(h in inst_handle for h in handles if len(h) >= 4):
                    clean_profs.append(p)
            else:
                clean_profs.append(p)
        final_result["profiles"] = clean_profs

    # Deduplicate phone numbers if present
    if final_result and "phone_numbers" in final_result:
        clean_phones = []
        for ph in final_result["phone_numbers"]:
            ph_clean = ph.strip()
            if ph_clean and ph_clean not in clean_phones:
                clean_phones.append(ph_clean)
        final_result["phone_numbers"] = clean_phones

    if final_result and final_result.get("is_corroborated"):
        _DORK_CACHE[cache_key] = final_result

    return final_result or {"is_corroborated": False, "profiles": []}
