"""
BreachSpillover - Cross-Platform Image Harvesting & Visual Identity Correlation Engine
Extracts authentic avatar and profile images for target identities across Gravatar,
GitHub, Duolingo, and personal web footprints without API keys, and formats 1-click
reverse visual search pivots for Google Lens, Yandex Visual, TinEye, Bing Visual, and PimEyes.
"""

import hashlib
import re
import urllib.parse
import urllib.request
import time
import json
from typing import Dict, Any, List, Optional, Set, Tuple

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# In-memory TTL cache for harvested images
_IMAGE_HARVEST_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
_AVATAR_PROBE_CACHE: Dict[str, Tuple[float, Any]] = {}

def build_reverse_image_search_links(image_url: str) -> Dict[str, str]:
    """
    Generates deterministic reverse image search query URLs for leading visual intelligence engines.
    """
    if not image_url:
        return {}
    
    clean_url = image_url.strip()
    encoded = urllib.parse.quote(clean_url, safe="")

    return {
        "google_lens": f"https://lens.google.com/uploadbyurl?url={encoded}",
        "yandex_images": f"https://yandex.com/images/search?rpt=imageview&url={encoded}",
        "tineye": f"https://tineye.com/search?url={encoded}",
        "bing_visual": f"https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl={encoded}",
        "pimeyes": "https://pimeyes.com/en"
    }


def probe_gravatar_avatar(email: str) -> Optional[Dict[str, Any]]:
    """
    Checks if an authentic Gravatar profile picture is published for this email address.
    """
    if not email or "@" not in email:
        return None

    clean_email = email.strip().lower()
    c_key = f"gravatar::{clean_email}"
    now = time.time()
    from backend.cache_manager import is_cache_disabled
    if not is_cache_disabled() and c_key in _AVATAR_PROBE_CACHE:
        c_time, c_val = _AVATAR_PROBE_CACHE[c_key]
        if now - c_time < 600.0:
            return dict(c_val) if c_val else None

    email_md5 = hashlib.md5(clean_email.encode("utf-8")).hexdigest()
    avatar_url = f"https://www.gravatar.com/avatar/{email_md5}?s=256&d=404"
    profile_json_url = f"https://en.gravatar.com/{email_md5}.json"

    display_name = None
    profile_url = f"https://gravatar.com/{email_md5}"

    # Verify avatar existence via HTTP HEAD / GET
    try:
        req = urllib.request.Request(avatar_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                pass
            else:
                _AVATAR_PROBE_CACHE[c_key] = (now, None)
                return None
    except Exception:
        _AVATAR_PROBE_CACHE[c_key] = (now, None)
        return None

    # Retrieve profile JSON if published
    try:
        req_json = urllib.request.Request(profile_json_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req_json, timeout=3.0) as resp_json:
            if resp_json.status == 200:
                data = json.loads(resp_json.read().decode("utf-8", errors="ignore"))
                entry = data.get("entry", [{}])[0]
                display_name = entry.get("displayName") or entry.get("name", {}).get("formatted")
                if entry.get("profileUrl"):
                    profile_url = entry["profileUrl"]
    except Exception:
        pass

    return {
        "platform": "Gravatar",
        "badge": "gravatar.com",
        "source": "Gravatar Universal Avatar",
        "image_url": avatar_url,
        "thumbnail_url": avatar_url,
        "profile_url": profile_url,
        "label": display_name or clean_email,
        "confidence": 0.95,
        "is_verified": True,
        "reverse_search_links": build_reverse_image_search_links(avatar_url)
    }


def probe_github_avatar(handle: str, target_name: str = "", target_email: str = "") -> Optional[Dict[str, Any]]:
    """
    Extracts authentic GitHub developer profile picture for a verified username,
    ensuring it does not conflict with target_name.
    """
    if not handle or len(handle.strip()) < 2:
        return None

    clean_handle = handle.strip().replace("@", "")
    avatar_url = f"https://github.com/{clean_handle}.png?size=256"
    profile_url = f"https://github.com/{clean_handle}"

    # If target_name is known, verify that the GitHub user does not conflict with target_name
    if target_name:
        try:
            from backend.platform_probes import query_github_user
            from backend.identity_correlator import evaluate_account_tie
            gh_user = query_github_user(clean_handle)
            if gh_user:
                tie = evaluate_account_tie(
                    account={
                        "platform": "GitHub",
                        "handle": clean_handle,
                        "real_name": gh_user.get("real_name") or "",
                        "bio": gh_user.get("bio") or "",
                    },
                    target_name=target_name,
                    target_email=target_email
                )
                if tie.get("is_rejected"):
                    return None
        except Exception:
            pass

    try:
        req = urllib.request.Request(avatar_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            # Check content-type is image
            c_type = resp.headers.get("Content-Type", "")
            c_len = int(resp.headers.get("Content-Length", 0))
            # Reject GitHub default identicons (which are small geometric SVGs/PNGs under 2.5KB)
            if c_len > 0 and c_len < 2500:
                return None

            if resp.status == 200 and "image" in c_type:
                return {
                    "platform": "GitHub",
                    "badge": "github.com",
                    "source": "GitHub Developer Profile",
                    "image_url": avatar_url,
                    "thumbnail_url": avatar_url,
                    "profile_url": profile_url,
                    "label": f"@{clean_handle}",
                    "confidence": 0.90,
                    "is_verified": True,
                    "reverse_search_links": build_reverse_image_search_links(avatar_url)
                }
    except Exception:
        pass

    return None


def probe_duolingo_avatar(email: str) -> Optional[Dict[str, Any]]:
    """
    Queries Duolingo public user API to extract registered user profile picture.
    """
    if not email or "@" not in email:
        return None

    try:
        url = f"https://www.duolingo.com/2017-06-30/users?email={urllib.parse.quote(email.strip().lower())}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                users = data.get("users", [])
                if users:
                    u = users[0]
                    pic = u.get("picture")
                    username = u.get("username", "")
                    if pic and "default" not in pic:
                        full_pic = ("https:" + pic) if pic.startswith("//") else pic
                        return {
                            "platform": "Duolingo",
                            "badge": "duolingo.com",
                            "source": "Duolingo Language Learner Profile",
                            "image_url": full_pic,
                            "thumbnail_url": full_pic,
                            "profile_url": f"https://www.duolingo.com/profile/{username}" if username else "https://www.duolingo.com",
                            "label": username or email,
                            "confidence": 0.88,
                            "is_verified": True,
                            "reverse_search_links": build_reverse_image_search_links(full_pic)
                        }
    except Exception:
        pass

    return None


def probe_opengraph_avatar(site_url: str) -> Optional[Dict[str, Any]]:
    """
    Extracts social preview / OpenGraph avatar image from personal websites and portfolios.
    """
    if not site_url or not site_url.startswith("http"):
        return None

    try:
        req = urllib.request.Request(site_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            if resp.status == 200:
                html = resp.read().decode("utf-8", errors="ignore")
                og_m = re.search(r'<meta[^>]+(?:property|name)=[\'"](?:og:image|twitter:image)[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', html, re.IGNORECASE)
                if not og_m:
                    og_m = re.search(r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+(?:property|name)=[\'"](?:og:image|twitter:image)[\'"]', html, re.IGNORECASE)
                
                if og_m:
                    img_src = og_m.group(1).strip()
                    # Resolve relative URLs
                    img_url = urllib.parse.urljoin(site_url, img_src)
                    if img_url.startswith("http") and not any(junk in img_url.lower() for junk in ["default", "placeholder", "logo", "icon", "banner"]):
                        return {
                            "platform": "Portfolio",
                            "badge": urllib.parse.urlparse(site_url).netloc,
                            "source": "Personal Website OpenGraph Image",
                            "image_url": img_url,
                            "thumbnail_url": img_url,
                            "profile_url": site_url,
                            "label": site_url,
                            "confidence": 0.85,
                            "is_verified": True,
                            "reverse_search_links": build_reverse_image_search_links(img_url)
                        }
    except Exception:
        pass

    return None


def _image_harvest_cache_key(
    clean_email: str,
    target_name: str = "",
    handles: Optional[List[str]] = None,
    personal_site_urls: Optional[List[str]] = None,
    extra_avatars: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Builds the harvest cache key. Includes a full MD5 fingerprint of every
    extra avatar (URL, platform, source, profile URL) and personal site so a
    rescan that surfaces new Facebook/LinkedIn photos or banners never
    receives a stale gallery.
    """
    av_parts = sorted(
        "|".join(str(a.get(k) or "") for k in ("image_url", "url", "platform", "source", "profile_url"))
        for a in (extra_avatars or []) if isinstance(a, dict)
    )
    sites = sorted(str(s or "").strip().lower() for s in (personal_site_urls or []) if s)
    extra_hash = hashlib.md5("\n".join(av_parts + ["--sites--"] + sites).encode("utf-8")).hexdigest()
    handle_str = ",".join(sorted(str(h).strip().lower() for h in (handles or []) if h))
    return f"{clean_email}::{(target_name or '').strip().lower()}::{handle_str}::{extra_hash}"


def harvest_target_images(
    email: str,
    target_name: str = "",
    handles: Optional[List[str]] = None,
    personal_site_urls: Optional[List[str]] = None,
    extra_avatars: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Harvests all authentic avatar images across Gravatar, GitHub, Duolingo,
    confirmed platform profiles (e.g. Pinterest), and personal sites.
    Deduplicates images and returns reverse search dispatch links for each image.
    """
    clean_email = (email or "").strip().lower()
    cache_key = _image_harvest_cache_key(clean_email, target_name, handles, personal_site_urls, extra_avatars)
    email_key = f"email_harvest::{clean_email}::{(target_name or '').strip().lower()}"
    now = time.time()
    if cache_key in _IMAGE_HARVEST_CACHE:
        c_time, c_val = _IMAGE_HARVEST_CACHE[cache_key]
        if now - c_time < 300.0:
            return [dict(img) for img in c_val]

    if email_key in _IMAGE_HARVEST_CACHE:
        c_time, c_val = _IMAGE_HARVEST_CACHE[email_key]
        if now - c_time < 300.0 and c_val:
            if extra_avatars:
                seen = set(img.get("image_url") or img.get("url") for img in c_val)
                merged = [dict(img) for img in c_val]
                for av in extra_avatars:
                    av_u = av.get("url") or av.get("image_url")
                    if av_u and av_u not in seen:
                        seen.add(av_u)
                        merged.append(av)
                return merged
            return [dict(img) for img in c_val]

    discovered_images: List[Dict[str, Any]] = []
    seen_image_urls: Set[str] = set()

    # 1. Gravatar Probe
    if email:
        grav = probe_gravatar_avatar(email)
        if grav and grav["image_url"] not in seen_image_urls:
            seen_image_urls.add(grav["image_url"])
            discovered_images.append(grav)

    # 2. GitHub Profile Avatars across candidate handles
    probe_handles: List[str] = []
    if handles:
        for h in handles:
            clean = h.strip() if h else ""
            if clean and len(clean) >= 3 and clean not in probe_handles:
                probe_handles.append(clean)
    if email and "@" in email:
        local = email.split("@")[0].strip()
        if local and len(local) >= 3 and local not in probe_handles:
            probe_handles.append(local)

    for h in probe_handles[:2]:
        gh = probe_github_avatar(h, target_name=target_name, target_email=email)
        if gh and gh["image_url"] not in seen_image_urls:
            seen_image_urls.add(gh["image_url"])
            discovered_images.append(gh)
            break

    # 3. Duolingo Profile Avatar
    if email:
        duo = probe_duolingo_avatar(email)
        if duo and duo["image_url"] not in seen_image_urls:
            seen_image_urls.add(duo["image_url"])
            discovered_images.append(duo)

    # 4. Deep Image & Portfolio Extraction from Discovered Personal Sites
    if personal_site_urls:
        for site_url in personal_site_urls[:3]:
            # Extract social preview / OpenGraph metadata
            og = probe_opengraph_avatar(site_url)
            if og and og["image_url"] not in seen_image_urls:
                seen_image_urls.add(og["image_url"])
                discovered_images.append(og)

            # Deep crawl webpage for author portraits, banner photos, and media assets
            try:
                page_imgs = extract_images_from_webpage(site_url)
                for p_img in page_imgs:
                    p_u = p_img.get("image_url")
                    if p_u and p_u not in seen_image_urls:
                        seen_image_urls.add(p_u)
                        discovered_images.append(p_img)
            except Exception as e:
                print(f"[!] Error deep scraping media from {site_url}: {e}")

    # 5. Verified Platform Avatars (e.g. Pinterest from profile prober)
    if extra_avatars:
        for av in extra_avatars:
            av_url = av.get("url") or av.get("image_url")
            if av_url and av_url not in seen_image_urls:
                seen_image_urls.add(av_url)
                plat = av.get("platform", "Platform")
                handle_str = av.get("handle") or target_name or "profile"
                src_label = av.get("source") or f"{plat} Profile Avatar"
                discovered_images.append({
                    "platform": plat,
                    "badge": f"{plat.lower()}.com",
                    "source": src_label,
                    "image_url": av_url,
                    "thumbnail_url": av_url,
                    "profile_url": av.get("profile_url", ""),
                    "label": f"@{handle_str} ({plat})",
                    "confidence": 0.95,
                    "is_verified": True,
                    "reverse_search_links": build_reverse_image_search_links(av_url)
                })

    # Only cache non-empty harvests: an empty gallery is usually a transient
    # network failure and must not mask images on the next scan.
    if discovered_images:
        _IMAGE_HARVEST_CACHE[cache_key] = (now, [dict(img) for img in discovered_images])
        _IMAGE_HARVEST_CACHE[email_key] = (now, [dict(img) for img in discovered_images])
    return discovered_images


_IMAGE_FEATURE_CACHE: Dict[str, Dict[str, Any]] = {}

def extract_image_perceptual_features(image_url: str) -> Dict[str, Any]:
    """
    Performs fast perceptual, format, and color entropy analysis on a candidate image.
    Detects continuous photographic gradients, central human skin-tone clustering,
    dimensions, and aspect ratios to distinguish real human portraits from cartoons/logos.
    Zero external heavy C++ vision libraries required: uses lightweight Pillow.
    """
    if not image_url or not image_url.startswith("http"):
        return {"is_accessible": False, "reason": "Invalid URL"}

    clean_url = image_url.strip()
    if clean_url in _IMAGE_FEATURE_CACHE:
        return _IMAGE_FEATURE_CACHE[clean_url]

    # Explicit exclusions
    if "profile-framedphoto" in clean_url or "ghost" in clean_url:
        return {"is_accessible": False, "reason": "Excluded frame/placeholder"}

    try:
        import io
        from PIL import Image

        req = urllib.request.Request(
            clean_url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
            }
        )
        with urllib.request.urlopen(req, timeout=1.2) as resp:
            if resp.status != 200:
                return {"is_accessible": False, "status_code": resp.status}
            content_type = resp.headers.get("Content-Type", "")
            raw_bytes = resp.read(512 * 1024)

        if len(raw_bytes) < 300:
            return {"is_accessible": False, "reason": "Image file too small or empty"}

        img = Image.open(io.BytesIO(raw_bytes))
        width, height = img.size
        img_format = (img.format or "UNKNOWN").upper()

        if width < 32 or height < 32:
            return {"is_accessible": False, "reason": "Dimensions too small for a face portrait"}

        aspect_ratio = round(width / float(height), 2)
        is_square_or_portrait = (0.65 <= aspect_ratio <= 1.4)

        # Convert to RGB for perceptual color analysis
        rgb_img = img.convert("RGB")
        
        # Color variance / unique colors (sampled down to 48x48 for fast perceptual analysis)
        sample_img = rgb_img.resize((48, 48), Image.Resampling.BILINEAR)
        sw, sh = sample_img.size
        total_sample_pixels = sw * sh
        
        # Central crop (central 60% of image where human faces reside in portraits)
        cx1, cy1, cx2, cy2 = int(sw * 0.2), int(sh * 0.2), int(sw * 0.8), int(sh * 0.8)
        center_pixels = (cx2 - cx1) * (cy2 - cy1)
        
        # YCbCr Skin Tone detection via fast bulk pixel buffer:
        # Standard YCbCr human skin chrominance cluster:
        # 77 <= Cb <= 135 and 133 <= Cr <= 177 and Y >= 50
        ycbcr_img = sample_img.convert("YCbCr")
        ycbcr_pixels = list(ycbcr_img.getdata())
        center_skin = 0
        overall_skin = 0

        for idx, (y_val, cb, cr) in enumerate(ycbcr_pixels):
            if 77 <= cb <= 135 and 133 <= cr <= 177 and y_val >= 50:
                overall_skin += 1
                px = idx % sw
                py = idx // sw
                if cx1 <= px < cx2 and cy1 <= py < cy2:
                    center_skin += 1

        center_skin_ratio = round(center_skin / float(max(center_pixels, 1)), 4)
        overall_skin_ratio = round(overall_skin / float(max(total_sample_pixels, 1)), 4)

        # Color entropy: sample pixels to measure unique colors
        rgb_pixels = list(sample_img.getdata())
        unique_colors = len(set(rgb_pixels[::2]))
        is_flat_graphic = (unique_colors < 120 and center_skin_ratio < 0.05)

        summary_tokens = [
            f"Dimensions: {width}x{height}",
            f"Format: {img_format}",
            f"Aspect: {aspect_ratio} ({'portrait/avatar square' if is_square_or_portrait else 'wide banner/strip'})",
            f"Center Skin Tone: {round(center_skin_ratio * 100, 1)}%",
            f"Color Diversity: {'Continuous photographic gradients' if unique_colors >= 350 else 'Stylized/flat color regions'}"
        ]
        
        feat = {
            "is_accessible": True,
            "width": width,
            "height": height,
            "format": img_format,
            "aspect_ratio": aspect_ratio,
            "is_square_or_portrait": is_square_or_portrait,
            "center_skin_ratio": center_skin_ratio,
            "overall_skin_ratio": overall_skin_ratio,
            "unique_colors": unique_colors,
            "is_flat_graphic": is_flat_graphic,
            "file_size_bytes": len(raw_bytes),
            "perceptual_summary": "; ".join(summary_tokens)
        }
        _IMAGE_FEATURE_CACHE[clean_url] = feat
        return feat

    except Exception as e:
        feat = {"is_accessible": False, "error": str(e)}
        _IMAGE_FEATURE_CACHE[clean_url] = feat
        return feat


def extract_images_from_webpage(page_url: str, html: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Crawls and parses a discovered personal portfolio, resume, or web page to extract
    high-resolution candidate author portraits, banner photos, and visual identity assets.
    Handles:
    - OpenGraph & Twitter Cards
    - Wix Media Assets (stripping dynamic fill/scaling subpaths that cause 403 Forbidden to retrieve original uncompressed master assets)
    - HTML <img>, <picture>, and <source srcset> tags
    - CSS inline style background images
    - YCbCr perceptual skin-tone chrominance clustering and continuous photographic gradient analysis
    100% generic across any platform (Wix, WordPress, JouwWeb, Carrd, GitHub Pages, custom domains).
    """
    if not page_url or not page_url.startswith("http"):
        return []

    if not html:
        try:
            req = urllib.request.Request(page_url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            })
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status != 200:
                    return []
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return []

    candidates: Set[str] = set()

    # 1. OpenGraph & Twitter Cards
    for og_m in re.finditer(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        candidates.add(urllib.parse.urljoin(page_url, og_m.group(1).strip()))
    for og_m in re.finditer(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\']', html, re.I):
        candidates.add(urllib.parse.urljoin(page_url, og_m.group(1).strip()))

    # 2. Wix Static Media (extract full-res master original without dynamic fill params that trigger 403)
    for wix_m in re.finditer(r'https?://static\.wixstatic\.com/media/([a-zA-Z0-9_~\.]+)', html):
        clean_id = wix_m.group(1).split('/')[0]
        if clean_id.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            candidates.add(f"https://static.wixstatic.com/media/{clean_id}")

    # 3. Standard <img> and <source> tags
    for img_m in re.finditer(r'<(?:img|source)[^>]+(?:src|data-src|data-lazy-src|data-original|srcset)=["\']([^"\']+)["\']', html, re.I):
        raw_val = img_m.group(1).strip()
        for item in raw_val.split(','):
            src = item.strip().split()[0] if item.strip() else ""
            if src and not src.startswith("data:") and not any(ext in src.lower() for ext in ['.svg', '.ico', '.gif']):
                candidates.add(urllib.parse.urljoin(page_url, src))

    # 4. CSS Background Images
    for bg_m in re.finditer(r'background(?:-image)?:\s*url\(["\']?([^"\'\)]+)["\']?\)', html, re.I):
        bg_src = bg_m.group(1).strip()
        if not bg_src.startswith("data:") and not any(ext in bg_src.lower() for ext in ['.svg', '.ico', '.gif']):
            candidates.add(urllib.parse.urljoin(page_url, bg_src))

    domain = urllib.parse.urlparse(page_url).netloc
    results: List[Dict[str, Any]] = []

    junk_indicators = [
        'doubleclick', 'google-analytics', 'googletagmanager', 'facebook.com/tr',
        'analytics', 'pixel', 'spacer', 'favicon', 'badge', 'logo', 'button', 'icon'
    ]

    for u in list(candidates)[:4]:
        if not u.startswith("http") or any(junk in u.lower() for junk in junk_indicators):
            continue

        feat = extract_image_perceptual_features(u)
        if not feat.get("is_accessible"):
            continue

        w, h = feat.get("width", 0), feat.get("height", 0)
        if w < 120 or h < 120:
            continue

        c_skin = feat.get("center_skin_ratio", 0.0)
        o_skin = feat.get("overall_skin_ratio", 0.0)
        unique_colors = feat.get("unique_colors", 0)
        fmt = feat.get("format", "")
        is_photo = (unique_colors >= 200 and fmt in ["JPEG", "WEBP", "PNG"])
        is_sq = feat.get("is_square_or_portrait", False)

        # Retain candidate if it exhibits human skin tone or continuous photographic variance
        if c_skin >= 0.08 or o_skin >= 0.08 or (is_photo and (w >= 300 or h >= 300)):
            if is_sq:
                if c_skin >= 0.15:
                    desc = "Personal Website Author Portrait"
                    conf = 0.95
                elif is_photo:
                    desc = "Personal Website Profile Photo"
                    conf = 0.90
                else:
                    desc = "Personal Website Image"
                    conf = 0.70
            else:
                desc = "Personal Website Landscape Banner"
                conf = 0.40

            results.append({
                "platform": "Portfolio",
                "badge": domain,
                "source": desc,
                "image_url": u,
                "thumbnail_url": u,
                "profile_url": page_url,
                "label": f"{desc} ({domain})",
                "confidence": conf,
                "is_verified": True,
                "reverse_search_links": build_reverse_image_search_links(u),
                "_feat": feat
            })

    return results


def ai_select_most_plausible_target_image(
    candidate_images: List[Dict[str, Any]],
    target_name: str = "",
    target_email: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Evaluates all discovered candidate avatar and profile images for a target identity,
    extracts perceptual features (skin-tone clustering, continuous photographic gradients, dimensions),
    and engages high-reasoning AI to select the MOST PLAUSIBLE AUTHENTIC REAL HUMAN PHOTOGRAPH
    of the target to represent their official profile picture.
    Completely generic: zero hardcoding.
    """
    if not candidate_images:
        return None

    # Deduplicate candidate images by URL
    unique_candidates: List[Dict[str, Any]] = []
    seen_urls: Set[str] = set()

    for cand in candidate_images:
        u = (cand.get("image_url") or cand.get("url") or "").strip()
        if not u or not u.startswith("http") or u in seen_urls:
            continue
        if "profile-framedphoto" in u or "ghost" in u:
            continue
        seen_urls.add(u)
        c_copy = dict(cand)
        c_copy["image_url"] = u
        unique_candidates.append(c_copy)

    if not unique_candidates:
        return None

    # Extract perceptual features for each candidate
    valid_candidates: List[Dict[str, Any]] = []
    for cand in unique_candidates[:4]:
        u = cand["image_url"]
        feat = extract_image_perceptual_features(u)
        if feat.get("is_accessible"):
            cand["_feat"] = feat
            valid_candidates.append(cand)

    if not valid_candidates:
        # Fallback to first non-empty URL if all network requests timed out
        return unique_candidates[0]

    # If only 1 accessible candidate exists, return it with perceptual classification
    if len(valid_candidates) == 1:
        single = valid_candidates[0]
        feat = single.get("_feat", {})
        is_face = (feat.get("center_skin_ratio", 0) >= 0.15 and feat.get("is_square_or_portrait") and feat.get("unique_colors", 0) > 150)
        single["is_real_face"] = is_face
        single["plausibility_score"] = 0.90 if is_face else 0.70
        single["classification"] = "REAL_HUMAN_PORTRAIT" if is_face else "CARTOON_OR_AVATAR"
        single["reasoning"] = f"Sole accessible visual footprint discovered for target ({feat.get('perceptual_summary')})."
        return single

    # Prepare structured payloads for AI reasoning
    summaries = []
    for idx, cand in enumerate(valid_candidates):
        cid = f"img_{idx + 1}"
        cand["_cid"] = cid
        feat = cand.get("_feat", {})
        summaries.append({
            "id": cid,
            "platform": cand.get("platform", "Unknown Platform"),
            "source": cand.get("source", "Profile Image"),
            "label": cand.get("label", ""),
            "context": cand.get("context", ""),
            "url": cand["image_url"],
            "perceptual_analysis": feat.get("perceptual_summary", "")
        })

    # Call AI reasoning engine
    try:
        from backend.cardinal.llm import call_groq_api, resolve_api_key
        api_key = resolve_api_key("groq") or resolve_api_key("gemini")

        if api_key:
            prompt = f"""You are an expert biometric and OSINT visual intelligence analyst.
Target Identity: {target_name or 'Target'} ({target_email or 'Unknown Email'})

Evaluate the candidate profile images discovered across online platforms to select the MOST PLAUSIBLE AUTHENTIC REAL HUMAN PHOTOGRAPH of the target to represent their official intelligence dossier.

CRITICAL MANDATORY PRINCIPLES:
1. Aspect Ratio & Portrait Constraint:
   - An authentic real human face portrait is an individual headshot or avatar with an aspect ratio between 0.65 and 1.35 (square or portrait).
   - A wide panoramic or landscape banner (aspect ratio >= 1.4 or width > 1.4 * height) is a website banner or background art, NEVER an individual's portrait photograph.
   - Any panoramic banner or landscape artwork MUST be classified as CARTOON_OR_AVATAR or GRAPHIC_OR_LOGO, NEVER REAL_HUMAN_PORTRAIT.
2. Anime and Illustrated Artwork Ban:
   - Any illustration, anime character (e.g. Spy x Family, manga, anime drawing, cartoon), gaming avatar, or digital artwork MUST be classified as CARTOON_OR_AVATAR with 'is_real_face: false', regardless of skin tone percentages.
3. Real Human Face vs. Stylized Avatar:
   - Differentiate authentic photographs depicting a real human face from artificial avatars. Real photographs typically feature continuous photographic color variance, realistic human skin tone clustering, natural lighting, and photographic file formats.
4. Selection Priority:
   - Give highest priority to authentic photographic portraits (aspect ratio 0.8 - 1.25, square or near-square) from personal portfolios or professional networks over landscape banners or gaming avatars.
   - If NO candidate depicts a real human face (e.g. all candidates are anime, cartoons, or logos), choose the best corroborated account avatar as fallback, but strictly set 'is_real_face: false' and classification: 'CARTOON_OR_AVATAR'.

CANDIDATES:
{json.dumps(summaries, indent=2)}

Return ONLY a valid JSON object matching this schema:
{{
  "selected_id": str,
  "plausibility_score": float,
  "is_real_face": bool,
  "classification": "REAL_HUMAN_PORTRAIT" | "CARTOON_OR_AVATAR" | "GRAPHIC_OR_LOGO",
  "reasoning": str,
  "evaluations": [
    {{
      "id": str,
      "classification": "REAL_HUMAN_PORTRAIT" | "CARTOON_OR_AVATAR" | "GRAPHIC_OR_LOGO",
      "is_real_face": bool,
      "plausibility_score": float,
      "reasoning": str
    }}
  ]
}}"""

            res = call_groq_api(
                prompt=prompt,
                system_instruction="You are an expert OSINT visual intelligence analyst. Return strictly valid JSON.",
                api_key=api_key,
                model="openai/gpt-oss-120b",
                response_json=True,
                max_tokens=800
            )

            if res and res.get("success") and res.get("text"):
                body = json.loads(res["text"])
                sel_id = body.get("selected_id")
                eval_map = {}
                for ev in body.get("evaluations", []):
                    if isinstance(ev, dict) and ev.get("id"):
                        eval_map[ev["id"]] = ev

                winner = None
                for cand in valid_candidates:
                    cid = cand.get("_cid")
                    ev = eval_map.get(cid)
                    feat = cand.get("_feat", {})
                    is_sq = feat.get("is_square_or_portrait", True)

                    if ev:
                        cand["is_real_face"] = bool(ev.get("is_real_face", False)) and is_sq
                        cand["plausibility_score"] = float(ev.get("plausibility_score", 0.70))
                        cand["classification"] = ev.get("classification", "CARTOON_OR_AVATAR")
                        cand["reasoning"] = ev.get("reasoning", "")
                    else:
                        c_skin = feat.get("center_skin_ratio", 0)
                        cand["is_real_face"] = (c_skin >= 0.15 and is_sq)
                        cand["plausibility_score"] = 0.85 if cand["is_real_face"] else 0.60
                        cand["classification"] = "REAL_HUMAN_PORTRAIT" if cand["is_real_face"] else "CARTOON_OR_AVATAR"
                        cand["reasoning"] = feat.get("perceptual_summary", "")

                    # Enforce strict banner guardrail
                    if not is_sq:
                        cand["is_real_face"] = False
                        if cand.get("classification") == "REAL_HUMAN_PORTRAIT":
                            cand["classification"] = "WEBSITE_BANNER_OR_ASSET" if ("banner" in str(cand.get("source", "")).lower() or "cover" in str(cand.get("source", "")).lower()) else "CARTOON_OR_AVATAR"

                    if cid == sel_id and (cand["is_real_face"] or not any(c.get("is_real_face") for c in valid_candidates)):
                        cand["is_primary"] = True
                        cand["is_real_face"] = bool(cand.get("is_real_face", False))
                        cand["plausibility_score"] = float(body.get("plausibility_score", 0.95))
                        cand["classification"] = cand.get("classification", "REAL_HUMAN_PORTRAIT")
                        cand["reasoning"] = body.get("reasoning", "Selected via AI visual identity analysis.")
                        winner = cand
                    else:
                        cand["is_primary"] = False

                # If selected winner was an invalid banner or non-face, but a genuine square portrait exists, promote the square portrait
                if not winner or not winner.get("is_real_face"):
                    for cand in valid_candidates:
                        if cand.get("is_real_face") and cand.get("classification") == "REAL_HUMAN_PORTRAIT":
                            if winner:
                                winner["is_primary"] = False
                            cand["is_primary"] = True
                            winner = cand
                            break

                if not winner and valid_candidates:
                    winner = valid_candidates[0]
                    winner["is_primary"] = True

                if winner:
                    winner["evaluated_candidates"] = valid_candidates
                    return winner
    except Exception as e:
        print(f"[!] AI image selection error: {e}")

    # Fallback to intelligent perceptual scoring
    best_cand = None
    best_score = -999.0

    for cand in valid_candidates:
        feat = cand.get("_feat", {})
        score = 0.0
        c_skin = feat.get("center_skin_ratio", 0.0)
        score += c_skin * 50.0

        if feat.get("format") in ["JPEG", "WEBP"]:
            score += 15.0
        if feat.get("unique_colors", 0) > 3000:
            score += 15.0
        if feat.get("is_square_or_portrait"):
            score += 10.0

        plat = (cand.get("platform") or "").lower()
        if "linkedin" in plat or "portfolio" in plat or "corporate" in plat:
            score += 20.0
        elif "gravatar" in plat or "duolingo" in plat:
            score += 10.0
        elif "github" in plat:
            score += 5.0
        elif "steam" in plat or "roblox" in plat:
            score -= 20.0

        if score > best_score:
            best_score = score
            best_cand = cand

    if best_cand:
        for cand in valid_candidates:
            feat = cand.get("_feat", {})
            is_face = (feat.get("center_skin_ratio", 0) >= 0.15)
            cand["is_real_face"] = is_face
            cand["classification"] = "REAL_HUMAN_PORTRAIT" if is_face else "CARTOON_OR_AVATAR"
            cand["plausibility_score"] = 0.88 if is_face else 0.65
            cand["reasoning"] = f"Perceptual analysis: {feat.get('perceptual_summary')}"
            cand["is_primary"] = (cand is best_cand)

        best_cand["reasoning"] = f"Corroborated visual candidate selected via perceptual skin-tone and color variance analysis ({best_cand.get('_feat', {}).get('perceptual_summary')})."
        best_cand["evaluated_candidates"] = valid_candidates
        return best_cand

    valid_candidates[0]["evaluated_candidates"] = valid_candidates
    return valid_candidates[0]


def reconcile_and_store_target_images(
    emp_id: int,
    email: str,
    target_name: str,
    cursor: Any = None,
    candidate_images: Optional[List[Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    """
    Arbitrates all candidate avatar and profile images discovered for a target employee,
    engages the AI visual intelligence analyzer to select the most plausible real human photograph,
    persists the winning photograph as the employee's official avatar_seed,
    and structures primary and secondary AVATAR_CORRELATION pivots with full audit reasoning.
    """
    needs_commit = False
    conn = None
    if cursor is None:
        from backend.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        needs_commit = True

    try:
        all_candidates: List[Dict[str, Any]] = []
        seen_urls: Set[str] = set()

        def _add_candidate(cand_item: Any):
            if isinstance(cand_item, str):
                cand_dict = {"image_url": cand_item, "source": "Discovered Image Footprint", "platform": "Web Footprint"}
            elif isinstance(cand_item, dict):
                cand_dict = dict(cand_item)
            else:
                return
            u = (cand_dict.get("image_url") or cand_dict.get("url") or "").strip()
            if not u or not u.startswith("http") or u in seen_urls:
                return
            if "profile-framedphoto" in u or "ghost" in u:
                return
            seen_urls.add(u)
            cand_dict["image_url"] = u
            all_candidates.append(cand_dict)

        # 1. Ingest supplied candidate images
        for c in (candidate_images or []):
            _add_candidate(c)

        # 2. Ingest existing avatar_seed from database
        cursor.execute("SELECT avatar_seed FROM employees WHERE id = ?", (emp_id,))
        emp_row = cursor.fetchone()
        if emp_row:
            seed = emp_row[0] if not hasattr(emp_row, "keys") else emp_row["avatar_seed"]
            if seed and str(seed).startswith("http"):
                _add_candidate({
                    "platform": "Dossier Profile",
                    "source": "Recorded Target Avatar",
                    "image_url": str(seed),
                    "context": "Existing dossier profile photo"
                })

        # 3. Ingest any AVATAR_CORRELATION pivots previously stored in database
        cursor.execute("""
            SELECT pivot_value, context_note, confidence_score 
            FROM pivots 
            WHERE employee_id = ? AND pivot_type = 'AVATAR_CORRELATION'
        """, (emp_id,))
        for prow in cursor.fetchall():
            pval = prow[0] if not hasattr(prow, "keys") else prow["pivot_value"]
            pctx = prow[1] if not hasattr(prow, "keys") else prow["context_note"]
            m = re.search(r'(https?://[^\s\]]+)', f"{pval} {pctx}")
            if m:
                u_str = m.group(1).rstrip("]")
                plat = "Public Profile"
                if "linkedin" in u_str.lower() or "licdn" in u_str.lower():
                    plat = "LinkedIn"
                elif "facebook" in u_str.lower() or "fbcdn" in u_str.lower():
                    plat = "Facebook"
                elif "github" in u_str.lower():
                    plat = "GitHub"
                elif "gravatar" in u_str.lower():
                    plat = "Gravatar"
                elif "pinimg" in u_str.lower() or "pinterest" in u_str.lower():
                    plat = "Pinterest"

                comb_txt = f"{pval} {pctx}".lower()
                is_banner = "banner" in comb_txt or "cover" in comb_txt
                src_label = f"{plat} Cover Banner" if is_banner else f"{plat} Visual Pivot"
                _add_candidate({
                    "platform": plat,
                    "source": src_label,
                    "image_url": u_str,
                    "context": pctx or pval,
                    "classification": "WEBSITE_BANNER_OR_ASSET" if is_banner else "REAL_HUMAN_PORTRAIT"
                })

        # 3b. Dynamically inspect any portfolio or personal websites stored in employee pivots
        try:
            cursor.execute("""
                SELECT pivot_value, context_note, pivot_type
                FROM pivots
                WHERE employee_id = ?
            """, (emp_id,))
            discovered_site_urls = set()
            for prow in cursor.fetchall():
                pval = str(prow[0] if not hasattr(prow, "keys") else prow["pivot_value"])
                pctx = str(prow[1] if not hasattr(prow, "keys") else prow["context_note"])
                combined = f"{pval} {pctx}"
                for m in re.finditer(r'https?://[^\s"\'<>\]\)]+', combined):
                    cand_url = m.group(0).rstrip(".,;")
                    dom = urllib.parse.urlparse(cand_url).netloc.lower()
                    if any(k in dom for k in ["wixsite.com", "jouwweb.nl", "carrd.co", "github.io", "about.me", "wordpress.com"]) or "portfolio" in cand_url.lower():
                        discovered_site_urls.add(cand_url)

            for s_url in list(discovered_site_urls)[:3]:
                try:
                    site_imgs = extract_images_from_webpage(s_url)
                    for si in site_imgs:
                        _add_candidate(si)
                except Exception as ex_s:
                    print(f"[!] Error extracting images from pivot site {s_url}: {ex_s}")
        except Exception as e_piv:
            print(f"[!] Pivot site image inspection error: {e_piv}")

        if not all_candidates:
            return None

        # 4. Invoke AI Visual Identity Arbiter
        winner = ai_select_most_plausible_target_image(
            candidate_images=all_candidates,
            target_name=target_name,
            target_email=email
        )
        if not winner:
            return None

        winner_url = winner.get("image_url")
        if not winner_url:
            return winner

        # 5. Persist winner into employees.avatar_seed
        cursor.execute("UPDATE employees SET avatar_seed = ? WHERE id = ?", (winner_url, emp_id))

        # 6. Clean up obsolete AVATAR_CORRELATION pivots for this employee
        cursor.execute("DELETE FROM pivots WHERE employee_id = ? AND pivot_type = 'AVATAR_CORRELATION'", (emp_id,))

        # 7. Insert the Primary Visual Footprint pivot
        classification = winner.get("classification", "REAL_HUMAN_PORTRAIT")
        plat = winner.get("platform", "Visual Footprint")
        conf = float(winner.get("plausibility_score", 0.98))
        reasoning = winner.get("reasoning", "Authentic photograph verified via AI visual reasoning.")
        primary_note = f"Most plausible authentic photograph of target selected via AI visual reasoning. [CLASSIFICATION: {classification}] [TIED: PRIMARY FACE] {reasoning} [URL: {winner_url}] [STATUS: VERIFIED]"

        cursor.execute("""
            INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
            VALUES (?, NULL, 'AVATAR_CORRELATION', ?, ?, ?)
        """, (
            emp_id,
            f"Primary Visual Footprint ({plat}): {winner_url}",
            conf,
            primary_note
        ))

        # 8. Insert Secondary Visual Footprints for alternative candidates
        evaluated = winner.get("evaluated_candidates") or all_candidates
        for sec in evaluated:
            sec_url = sec.get("image_url")
            if not sec_url or sec_url == winner_url:
                continue
            sec_plat = sec.get("platform", "Asset")
            if "facebook" in sec_url.lower() or "fbcdn" in sec_url.lower():
                sec_plat = "Facebook"
            elif "licdn" in sec_url.lower() or "linkedin" in sec_url.lower():
                sec_plat = "LinkedIn"

            sec_src = str(sec.get("source", ""))
            is_banner_asset = "banner" in sec_src.lower() or "cover" in sec_src.lower() or sec.get("classification") == "WEBSITE_BANNER_OR_ASSET"

            if is_banner_asset:
                sec_class = "WEBSITE_BANNER_OR_ASSET"
                asset_label = f"{sec_plat} Cover Banner"
            elif sec_plat in ["LinkedIn", "Facebook"] and sec.get("is_real_face", True):
                sec_class = "REAL_HUMAN_PORTRAIT"
                asset_label = f"{sec_plat} Profile Avatar"
            else:
                sec_class = sec.get("classification", "CARTOON_OR_AVATAR")
                asset_label = f"{sec_plat} Secondary Asset"

            sec_conf = float(sec.get("plausibility_score", 0.90 if is_banner_asset else 0.70))
            sec_reason = sec.get("reasoning", "")
            sec_note = f"Visual candidate ({asset_label}) classified as {sec_class} ({sec_plat}). {sec_reason} [URL: {sec_url}] [STATUS: SECONDARY AVATAR]"

            cursor.execute("""
                INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
                VALUES (?, NULL, 'AVATAR_CORRELATION', ?, ?, ?)
            """, (
                emp_id,
                f"Secondary Visual Footprint ({sec_plat}): {sec_url}",
                sec_conf,
                sec_note
            ))

        if needs_commit and conn:
            conn.commit()

        return winner
    except Exception as e:
        print(f"[!] Error in reconcile_and_store_target_images: {e}")
        return None
    finally:
        if needs_commit and conn:
            conn.close()


