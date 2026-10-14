"""
BreachSpillover - Facebook OSINT & Profile Extraction Engine
Handles automated candidate profile derivation, Meta authwall navigation,
authenticated People Search, and session-based profile intelligence extraction.
"""

import os
import re
import time
import json
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from backend.image_recon import build_reverse_image_search_links, extract_image_perceptual_features

BASE_DIR = Path(__file__).resolve().parent.parent
USER_AGENT_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get_facebook_session_cookies() -> Dict[str, str]:
    """
    Retrieves Facebook investigator session cookies from environment variables
    or storage_state.json with automatic token normalization.
    """
    try:
        from backend.session_vault import reload_env
        reload_env()
    except Exception:
        pass

    c_user = os.environ.get("FACEBOOK_C_USER", "").strip().strip('"').strip("'")
    xs = os.environ.get("FACEBOOK_XS", "").strip().strip('"').strip("'")
    raw_cookie = os.environ.get("FACEBOOK_COOKIE", "").strip().strip('"').strip("'")

    cookies: Dict[str, str] = {}
    if c_user and c_user.isdigit():
        cookies["c_user"] = c_user
    if xs and len(xs) > 10:
        cookies["xs"] = xs

    if not cookies and raw_cookie:
        for part in raw_cookie.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                cookies[k.strip()] = v.strip().strip('"').strip("'")

    # Fallback / augment with browser_session storage_state.json
    storage_state = BASE_DIR / "data" / "browser_session" / "storage_state.json"
    if storage_state.exists():
        try:
            with open(storage_state, "r", encoding="utf-8") as f:
                d = json.load(f)
            for c in d.get("cookies", []):
                c_name = c.get("name", "")
                c_val = c.get("value", "")
                if c_name in ("c_user", "xs", "sb", "datr", "fr") and c_val:
                    if c_name not in cookies:
                        cookies[c_name] = c_val
        except Exception:
            pass

    return cookies


def derive_candidate_facebook_urls(
    target_name: str,
    target_email: str = "",
    known_handles: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """
    Generates deterministic candidate Facebook profile URLs based on verified
    target name permutations and discovered handles.
    """
    candidates: List[Dict[str, str]] = []
    seen_urls: Set[str] = set()

    def _add(url_str: str, slug_label: str, confidence: float):
        clean = url_str.strip()
        if clean not in seen_urls:
            seen_urls.add(clean)
            candidates.append({
                "platform": "Facebook",
                "url": clean,
                "handle": slug_label,
                "confidence": confidence,
                "source": "Deterministic Identity Derivation"
            })

    # 1. Email local part
    if target_email and "@" in target_email:
        local = target_email.split("@")[0].strip().lower()
        if len(local) >= 3 and not any(k in local for k in ["admin", "info", "contact", "support"]):
            _add(f"https://www.facebook.com/{local}", local, 0.88)
            base_local = re.sub(r'\d+$', '', local)
            if base_local and base_local != local and len(base_local) >= 4:
                _add(f"https://www.facebook.com/{base_local}", base_local, 0.82)

    # 2. Name permutations
    if target_name:
        parts = [p.lower() for p in target_name.strip().split() if p.isalpha()]
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]
            _add(f"https://www.facebook.com/{first}.{last}", f"{first}.{last}", 0.90)
            _add(f"https://www.facebook.com/{first}{last}", f"{first}{last}", 0.85)
            _add(f"https://www.facebook.com/{first}-{last}", f"{first}-{last}", 0.80)
            _add(f"https://www.facebook.com/people/{first.capitalize()}-{last.capitalize()}", f"{first}-{last}", 0.75)

    # 3. Known handles from earlier pivots
    if known_handles:
        for h in known_handles:
            h_clean = h.strip().lstrip("@").lower()
            if len(h_clean) >= 3 and h_clean not in ["none", "target", "unknown"]:
                _add(f"https://www.facebook.com/{h_clean}", h_clean, 0.85)

    return candidates


async def search_facebook_people(
    page,
    target_name: str,
    known_corroborations: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Executes an authenticated search on Facebook People Search using Playwright,
    extracting candidates with corroboration scoring (name, location, education, workplace).
    """
    if not target_name or not target_name.strip():
        return []

    q_encoded = urllib.parse.quote(target_name.strip())
    search_url = f"https://www.facebook.com/search/people/?q={q_encoded}"

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=5000)
        await page.wait_for_timeout(500)

        curr_url = (page.url or "").lower()
        if "login" in curr_url or "checkpoint" in curr_url:
            return []

        raw_candidates = await page.evaluate("""() => {
            const results = [];
            const main = document.querySelector('div[role="main"]') || document.body;
            for (const a of main.querySelectorAll('a')) {
                const href = a.href || '';
                if (!href.includes('facebook.com/')) continue;
                if (href.includes('/search/') || href.includes('/help/') || href.includes('/pages/') || href.includes('/groups/') || href.includes('/events/') || href.includes('/hashtag/')) continue;

                let linkText = (a.innerText || '').trim();
                if (!linkText || linkText.includes('Online status') || linkText.includes('Add friend') || linkText.includes('Message') || linkText.includes('Follow')) continue;

                let cleanUrl = href.split('&__tn__=')[0].split('?__tn__=')[0];
                if (cleanUrl.includes('profile.php?id=')) {
                    const m = cleanUrl.match(/(https:\\/\\/www\\.facebook\\.com\\/profile\\.php\\?id=\\d+)/);
                    if (m) cleanUrl = m[1];
                } else {
                    cleanUrl = cleanUrl.split('?')[0];
                }

                let card = a;
                for (let i = 0; i < 5; i++) {
                    if (card.parentElement) card = card.parentElement;
                }
                const cardText = (card.innerText || '').trim();

                const existing = results.find(r => r.url === cleanUrl);
                if (!existing) {
                    results.push({
                        name: linkText,
                        url: cleanUrl,
                        snippet: cardText.replace(/\\n+/g, ' â€¢ ').substring(0, 250)
                    });
                } else if (existing.name.includes('\\n') || existing.name.length < linkText.length) {
                    existing.name = linkText;
                }
            }
            return results;
        }""")

        name_tokens = [tok.lower() for tok in target_name.strip().split() if len(tok) >= 2]
        scored_candidates: List[Dict[str, Any]] = []

        corrob_tokens = []
        if known_corroborations:
            for item in known_corroborations:
                if item and len(item.strip()) >= 3:
                    corrob_tokens.append(item.strip().lower())

        for c in raw_candidates:
            c_name = c.get("name", "").lower()
            snippet = c.get("snippet", "").lower()
            score = 0.0

            if target_name.lower() in c_name:
                score += 0.80
            elif all(tok in c_name for tok in name_tokens):
                score += 0.70
            elif any(tok in c_name for tok in name_tokens):
                score += 0.35
            else:
                continue

            # Corroborate with target location, school, employer
            for token in corrob_tokens:
                if token in snippet:
                    score += 0.25

            c["score"] = round(score, 2)
            scored_candidates.append(c)

        scored_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
        return scored_candidates

    except Exception:
        return []


# In-memory TTL cache for Facebook Playwright scrapes
_FB_SCRAPE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

async def scrape_facebook_profile_with_playwright(
    profile_url: Optional[str] = None,
    target_name: str = "",
    session_cookies: Optional[Dict[str, str]] = None,
    known_corroborations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Uses Playwright with authenticated session cookies (c_user, xs) to extract
    verified profile pictures, cover banners, biographical details, and timeline information.
    If direct candidate URL fails or is absent, automatically performs authenticated People Search.
    Optimized for high-speed execution with in-memory caching and tight navigation limits.
    """
    cache_key = f"{(target_name or '').strip().lower()}::{(profile_url or '').strip().lower()}"
    now = time.time()
    from backend.cache_manager import is_cache_disabled
    if not is_cache_disabled() and cache_key in _FB_SCRAPE_CACHE:
        c_time, c_res = _FB_SCRAPE_CACHE[cache_key]
        if now - c_time < 300.0 and c_res.get("is_verified"):
            return c_res

    cookies_to_use = session_cookies or get_facebook_session_cookies()
    has_auth = bool(cookies_to_use.get("c_user") and cookies_to_use.get("xs"))

    result: Dict[str, Any] = {
        "is_authenticated": has_auth,
        "session_expired": False,
        "profile_url": profile_url or "",
        "is_verified": False,
        "photos": [],
        "bio": None,
        "full_name": None,
        "lives_in": None,
        "from_location": None,
        "education": None,
        "work": None,
        "birth_date": None,
        "details_summary": "",
        "reasoning": ""
    }

    if not has_auth:
        result["reasoning"] = (
            "[SAFETY LINE] Facebook session not configured. Meta enforces strict authwalls on public endpoints. "
            "Configure FACEBOOK_C_USER and FACEBOOK_XS in Investigator Session Vault to enable authenticated timeline & photo extraction."
        )
        return result

    try:
        from playwright.async_api import async_playwright

        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        has_edge = any(os.path.exists(p) for p in edge_paths)

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(channel="msedge" if has_edge else "chromium", headless=True)
            except Exception:
                browser = await p.chromium.launch(headless=True)

            context = await browser.new_context(
                user_agent=USER_AGENT_DESKTOP,
                viewport={"width": 1280, "height": 800}
            )

            # Inject session cookies
            cookie_list = []
            for k, v in cookies_to_use.items():
                cookie_list.append({
                    "name": k,
                    "value": v,
                    "domain": ".facebook.com",
                    "path": "/"
                })
            await context.add_cookies(cookie_list)

            page = await context.new_page()
            target_profile_url = profile_url

            try:
                # 1. Test direct profile URL if provided
                direct_url_valid = False
                if target_profile_url:
                    resp = await page.goto(target_profile_url, wait_until="domcontentloaded", timeout=6000)
                    await page.wait_for_timeout(400)

                    current_url = page.url.lower()
                    if "login" in current_url or "checkpoint" in current_url:
                        result["session_expired"] = True
                        result["is_authenticated"] = False
                        result["reasoning"] = "[SAFETY LINE] Facebook session cookie rejected or expired by Meta. Re-authenticate in Investigator Session Vault."
                        return result

                    body_text = await page.inner_text("body")
                    body_lower = body_text.lower()
                    if not ("this content isn't available right now" in body_lower or "page not found" in body_lower or "isn't available" in body_lower):
                        page_title = await page.title()
                        clean_title = re.sub(r'^\(\d+\+?\)\s*', '', page_title).replace(" | Facebook", "").replace(" - Facebook", "").strip()
                        if clean_title.lower() not in ["facebook", "log in to facebook", "error", "welcome to facebook"]:
                            direct_url_valid = True

                # 2. If direct URL is invalid, 404, or not provided, run authenticated People Search
                if not direct_url_valid and target_name:
                    search_candidates = await search_facebook_people(page, target_name, known_corroborations)
                    if search_candidates:
                        top_match = search_candidates[0]
                        if top_match.get("score", 0) >= 0.70:
                            target_profile_url = top_match["url"]
                            result["profile_url"] = target_profile_url
                            await page.goto(target_profile_url, wait_until="domcontentloaded", timeout=6000)
                            await page.wait_for_timeout(400)

                            current_url = page.url.lower()
                            if "login" in current_url or "checkpoint" in current_url:
                                result["session_expired"] = True
                                result["is_authenticated"] = False
                                result["reasoning"] = "[SAFETY LINE] Facebook session expired during profile navigation. Re-authenticate in Session Vault."
                                return result

                if not target_profile_url:
                    result["reasoning"] = "No candidate Facebook profile found for target."
                    return result

                # 3. Extract comprehensive profile details and media assets
                extracted = await page.evaluate(r"""() => {
                    const data = {
                        name: '',
                        photos: [],
                        lives_in: '',
                        from_location: '',
                        education: '',
                        work: '',
                        birth_date: '',
                        friends_count: ''
                    };

                    const main = document.querySelector('div[role="main"]') || document.body;

                    // 1. Profile Name
                    const h1 = main.querySelector('h1');
                    if (h1 && h1.innerText.trim()) {
                        data.name = h1.innerText.trim();
                    }

                    // 2. Detect Cover Banner Photo (multilingual parent aria-labels, pagelets, and header banners)
                    const coverSelectors = [
                        'a[aria-label*="cover photo" i] img',
                        'a[aria-label*="omslagfoto" i] img',
                        'a[aria-label*="cover" i] img',
                        'a[aria-label*="omslag" i] img',
                        'div[aria-label*="cover photo" i] img',
                        'div[aria-label*="omslagfoto" i] img',
                        'div[data-pagelet="ProfileCoverPhoto"] img',
                        'div[data-pagelet*="Cover"] img',
                        'div[data-imgperflogname="profileCoverPhoto"] img'
                    ];
                    for (const sel of coverSelectors) {
                        for (const img of main.querySelectorAll(sel)) {
                            const src = img.src || '';
                            if (src && src.includes('fbcdn.net') && !data.photos.some(p => p.url === src)) {
                                data.photos.push({ type: 'cover', url: src });
                            }
                        }
                    }

                    // Fallback cover detection: inspect top header images with banner/cover links or large dimensions
                    if (!data.photos.some(p => p.type === 'cover')) {
                        for (const img of main.querySelectorAll('img')) {
                            const src = img.src || '';
                            if (!src.includes('fbcdn.net')) continue;
                            const a = img.closest('a');
                            const aAria = a ? (a.getAttribute('aria-label') || '').toLowerCase() : '';
                            const imgAria = (img.getAttribute('aria-label') || '').toLowerCase();
                            const alt = (img.alt || '').toLowerCase();
                            if (aAria.includes('cover') || aAria.includes('omslag') || imgAria.includes('cover') || imgAria.includes('omslag') || alt.includes('cover') || alt.includes('omslag')) {
                                if (!data.photos.some(p => p.url === src)) {
                                    data.photos.push({ type: 'cover', url: src });
                                }
                            } else if (src.includes('t39.30808-6') && a && a.href && a.href.includes('/photo/')) {
                                const rect = img.getBoundingClientRect();
                                if (rect.top < 500 && (rect.width > 300 || img.naturalWidth > 300)) {
                                    if (!data.photos.some(p => p.url === src)) {
                                        data.photos.push({ type: 'cover', url: src });
                                    }
                                }
                            }
                        }
                    }

                    // 3. Detect Profile Avatar (SVG image in profile link, profile picture aria-label, -1 CDN format)
                    for (const svgImg of main.querySelectorAll('svg image, image')) {
                        const src = svgImg.getAttribute('xlink:href') || svgImg.getAttribute('href');
                        if (!src || !src.includes('fbcdn.net')) continue;
                        const a = svgImg.closest('a');
                        const aria = svgImg.closest('[aria-label]') ? (svgImg.closest('[aria-label]').getAttribute('aria-label') || '') : '';
                        if (aria.toLowerCase().includes('switch profile') || aria.toLowerCase().includes('available voices')) continue;
                        if (svgImg.closest('nav') || svgImg.closest('header')) continue;
                        if ((a && a.href && a.href.includes('/photo/')) || aria.toLowerCase().includes('profile') || aria.toLowerCase().includes('profielfoto')) {
                            if (!data.photos.some(p => p.url === src)) {
                                data.photos.push({ type: 'avatar', url: src });
                            }
                        }
                    }

                    for (const img of main.querySelectorAll('img[alt*="profile picture" i], img[alt*="profielfoto" i], div[aria-label*="profile picture" i] img, div[aria-label*="profielfoto" i] img, a[aria-label*="profile picture" i] img, a[aria-label*="profielfoto" i] img')) {
                        const src = img.src || '';
                        if (src && src.includes('fbcdn.net') && !data.photos.some(p => p.url === src)) {
                            data.photos.push({ type: 'avatar', url: src });
                        }
                    }

                    // 4. Biographical Details
                    const allSpans = Array.from(main.querySelectorAll('span, div, a'));
                    for (const el of allSpans) {
                        const t = (el.innerText || '').trim();
                        if (!t) continue;
                        const low = t.toLowerCase();
                        if ((low.startsWith('lives in ') || low.startsWith('woont in ')) && !data.lives_in) {
                            if (t.length < 90 && !t.includes('\n')) data.lives_in = t;
                        }
                        if ((low.startsWith('from ') || low.startsWith('komt uit ')) && !data.from_location) {
                            if (t.length < 90 && !t.includes('\n')) data.from_location = t;
                        }
                        if ((low.startsWith('studied at ') || low.startsWith('went to ') || low.startsWith('studeerde aan ') || low.startsWith('heeft gestudeerd aan ') || low.startsWith('ging naar ') || low.includes('university') || low.includes('college') || low.includes('hogeschool') || low.includes('universiteit') || low.includes('auas')) && !data.education) {
                            if (t.length < 90 && !t.includes('\n')) data.education = t;
                        }
                        if ((low.startsWith('works at ') || low.startsWith('werkt bij ') || low.startsWith('werkte bij ') || low.startsWith('former ')) && !data.work) {
                            if (t.length < 90 && !t.includes('\n')) data.work = t;
                        }
                        if ((t.includes('January ') || t.includes('February ') || t.includes('March ') || t.includes('April ') || t.includes('May ') || t.includes('June ') || t.includes('July ') || t.includes('August ') || t.includes('September ') || t.includes('October ') || t.includes('November ') || t.includes('December ') || t.includes('januari') || t.includes('februari') || t.includes('maart') || t.includes('mei') || t.includes('juni') || t.includes('juli') || t.includes('augustus') || t.includes('oktober')) && /\d{4}/.test(t)) {
                            if (t.length < 35 && !data.birth_date) data.birth_date = t;
                        }
                        if ((low.includes('friends') || low.includes('vrienden')) && /\d+\s+(?:friends|vrienden)/i.test(t) && !data.friends_count) {
                            data.friends_count = t.split('â€¢')[0].trim();
                        }
                    }

                    return data;
                }""")

                # 3b. If education, location, or work was not present in main timeline intro, probe about tab
                if target_profile_url and (not extracted.get("education") or not extracted.get("lives_in") or not extracted.get("work")):
                    try:
                        about_url = target_profile_url + ("/about" if "?" not in target_profile_url else "&sk=about")
                        await page.goto(about_url, wait_until="domcontentloaded", timeout=6000)
                        await page.wait_for_timeout(800)
                        about_data = await page.evaluate(r"""() => {
                            const res = { education: '', lives_in: '', from_location: '', work: '' };
                            const nodes = Array.from(document.querySelectorAll('span, a, h3, div')).map(el => (el.innerText || '').trim()).filter(t => t.length > 2 && t.length < 90);
                            for (const t of nodes) {
                                const low = t.toLowerCase();
                                if (!res.education && (low.includes('university') || low.includes('college') || low.includes('hogeschool') || low.includes('universiteit') || low.includes('studeerde') || low.includes('studied') || low.includes('auas'))) {
                                    if (!t.includes('\n')) res.education = t;
                                }
                                if (!res.lives_in && (low.includes('woont in') || low.includes('lives in') || low.includes('current city'))) {
                                    const clean = t.replace(/(?:Location|Current city|Hometown)\s*/gi, '').trim();
                                    if (clean && !clean.includes('\n')) res.lives_in = clean;
                                }
                                if (!res.from_location && (low.includes('hometown') || low.includes('komt uit') || low.includes('from '))) {
                                    const clean = t.replace(/(?:Hometown|Komt uit)\s*/gi, '').trim();
                                    if (clean && !clean.includes('\n')) res.from_location = clean;
                                }
                                if (!res.work && (low.includes('werkt bij') || low.includes('works at') || low.includes('werkzaam bij'))) {
                                    if (!t.includes('\n')) res.work = t;
                                }
                            }
                            return res;
                        }""")
                        if about_data.get("education") and not extracted.get("education"):
                            extracted["education"] = about_data["education"]
                        if about_data.get("lives_in") and not extracted.get("lives_in"):
                            extracted["lives_in"] = about_data["lives_in"]
                        if about_data.get("from_location") and not extracted.get("from_location"):
                            extracted["from_location"] = about_data["from_location"]
                        if about_data.get("work") and not extracted.get("work"):
                            extracted["work"] = about_data["work"]
                    except Exception as e_about:
                        logger.debug(f"Facebook about navigation notice: {e_about}")

                # Fallback name from page title if h1 is empty
                page_title = await page.title()
                clean_title = re.sub(r'^\(\d+\+?\)\s*', '', page_title).replace(" | Facebook", "").replace(" - Facebook", "").strip()
                result["full_name"] = extracted.get("name") or (clean_title if clean_title.lower() != "facebook" else target_name)
                result["lives_in"] = extracted.get("lives_in")
                result["from_location"] = extracted.get("from_location")
                result["education"] = extracted.get("education")
                result["work"] = extracted.get("work")
                result["birth_date"] = extracted.get("birth_date")

                summary_tokens = []
                if result["lives_in"]: summary_tokens.append(result["lives_in"])
                if result["education"]: summary_tokens.append(result["education"])
                if result["work"]: summary_tokens.append(result["work"])
                if result["birth_date"]: summary_tokens.append(f"Born {result['birth_date']}")
                result["details_summary"] = " â€¢ ".join(summary_tokens)

                # Helper to process, enhance resolution, and perceptually verify Facebook images
                seen_photo_bases = set()

                def _add_facebook_photo(raw_u: str, source_label: str, caption: str = "", is_avatar: bool = False, is_cover: bool = False):
                    if not raw_u or not raw_u.startswith("http"):
                        return
                    # Strip thumbnail dimension constraints to retrieve high-resolution assets from Facebook CDN
                    high_res = re.sub(r'&ctp=[sp]\d+x\d+', '', raw_u)
                    clean_base = high_res.split("?")[0]
                    if clean_base in seen_photo_bases:
                        return
                    seen_photo_bases.add(clean_base)

                    feat = extract_image_perceptual_features(high_res)
                    if not feat.get("is_accessible"):
                        feat = extract_image_perceptual_features(raw_u)
                        if not feat.get("is_accessible"):
                            return
                        high_res = raw_u

                    w = feat.get("width", 0)
                    h = feat.get("height", 0)
                    is_sq = feat.get("is_square_or_portrait", False)

                    if w < 48 or h < 48:
                        return

                    if is_cover or "banner" in source_label.lower() or "cover" in source_label.lower():
                        classification = "WEBSITE_BANNER_OR_ASSET"
                    elif is_sq and feat.get("center_skin_ratio", 0) >= 0.08:
                        classification = "REAL_HUMAN_PORTRAIT"
                    elif not is_sq:
                        classification = "WEBSITE_BANNER_OR_ASSET"
                    else:
                        classification = "CARTOON_OR_AVATAR"

                    conf = 0.95 if (is_avatar or classification == "REAL_HUMAN_PORTRAIT") else 0.90
                    result["photos"].append({
                        "platform": "Facebook",
                        "badge": "facebook.com",
                        "source": source_label,
                        "image_url": high_res,
                        "thumbnail_url": raw_u,
                        "profile_url": target_profile_url,
                        "label": f"{source_label} ({result['full_name']})",
                        "caption": caption,
                        "classification": classification,
                        "confidence": conf,
                        "is_verified": True,
                        "reverse_search_links": build_reverse_image_search_links(high_res),
                        "_feat": feat
                    })

                # 1. Process header photos (current avatar and cover banner)
                for p_item in extracted.get("photos", []):
                    u = p_item.get("url")
                    p_type = p_item.get("type", "photo")
                    lbl = "Facebook Profile Avatar" if p_type == "avatar" else "Facebook Cover Banner"
                    _add_facebook_photo(u, lbl, is_avatar=(p_type == "avatar"), is_cover=(p_type == "cover"))

                # 2. Extract target's uploaded timeline photos
                photos_tab_url = f"{target_profile_url}&sk=photos" if "profile.php" in target_profile_url else f"{target_profile_url.rstrip('/')}/photos"
                try:
                    await page.goto(photos_tab_url, wait_until="domcontentloaded", timeout=2500)
                    await page.wait_for_timeout(300)
                    timeline_uploads = await page.evaluate(r"""() => {
                        const res = [];
                        for (const a of document.querySelectorAll('a[href*="/photo/"], a[href*="photo.php"]')) {
                            const img = a.querySelector('img');
                            if (img && img.src && img.src.includes('fbcdn.net')) {
                                res.push({
                                    src: img.src,
                                    alt: img.alt || '',
                                    aria: a.getAttribute('aria-label') || ''
                                });
                            }
                        }
                        return res;
                    }""")
                    for tu in timeline_uploads:
                        cap = tu.get("alt") or tu.get("aria") or ""
                        _add_facebook_photo(tu["src"], "Facebook Uploaded Photo", caption=cap)
                except Exception as ex_photos:
                    print(f"[*] Timeline photos tab navigation notice: {ex_photos}")

                # 3. Extract target's photo albums (Historical Profile Pictures, Cover Photos, Uploads)
                albums_tab_url = f"{target_profile_url}&sk=photos_albums" if "profile.php" in target_profile_url else f"{target_profile_url.rstrip('/')}/photos_albums"
                try:
                    await page.goto(albums_tab_url, wait_until="domcontentloaded", timeout=2500)
                    await page.wait_for_timeout(300)
                    album_links = await page.evaluate(r"""() => {
                        const res = [];
                        for (const a of document.querySelectorAll('a[href*="/media/set/"], a[href*="sk=photos_album"]')) {
                            const t = (a.innerText || a.getAttribute('aria-label') || '').toLowerCase();
                            res.push({ href: a.href, text: t });
                        }
                        return res;
                    }""")

                    key_albums = []
                    for alb in album_links:
                        href = alb.get("href", "")
                        if not ("/media/set/" in href or "sk=photos_album" in href):
                            continue
                        t = alb.get("text", "").lower()
                        if "profile picture" in t or "profielfoto" in t:
                            key_albums.append((href, "Facebook Historical Profile Picture"))
                        elif "cover photo" in t or "omslagfoto" in t:
                            key_albums.append((href, "Facebook Historical Cover Photo"))
                        else:
                            first_line = t.splitlines()[0].strip() if t else "Album"
                            key_albums.append((href, f"Facebook Album Photo ({first_line[:25]})"))

                    for a_url, a_label in key_albums[:3]:
                        try:
                            await page.goto(a_url, wait_until="domcontentloaded", timeout=8000)
                            await page.wait_for_timeout(600)
                            a_imgs = await page.evaluate(r"""() => {
                                const res = [];
                                for (const a of document.querySelectorAll('a[href*="/photo/"], a[href*="photo.php"]')) {
                                    const img = a.querySelector('img');
                                    if (img && img.src && img.src.includes('fbcdn.net')) {
                                        res.push({ src: img.src, alt: img.alt || '' });
                                    }
                                }
                                return res;
                            }""")
                            for ai in a_imgs:
                                _add_facebook_photo(ai["src"], a_label, caption=ai.get("alt", ""))
                        except Exception as ex_single_alb:
                            print(f"[*] Album scrape notice ({a_label}): {ex_single_alb}")
                except Exception as ex_albums:
                    print(f"[*] Albums tab navigation notice: {ex_albums}")

                result["is_verified"] = len(result["photos"]) > 0 or bool(result["details_summary"])
                result["reasoning"] = (
                    f"Successfully authenticated via session tokens. Extracted Facebook profile for '{result['full_name']}' "
                    f"({len(result['photos'])} photos/uploads, {result['details_summary'] or 'timeline intelligence'})."
                )

            except Exception as e_page:
                result["reasoning"] = f"Error during Facebook page navigation: {e_page}"
            finally:
                await browser.close()

    except Exception as e:
        result["reasoning"] = f"Playwright automation error: {e}"

    if result.get("is_verified"):
        _FB_SCRAPE_CACHE[cache_key] = (time.time(), result)
    return result
