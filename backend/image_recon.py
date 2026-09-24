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
import json
from typing import Dict, Any, List, Optional, Set

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

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
    email_md5 = hashlib.md5(clean_email.encode("utf-8")).hexdigest()
    avatar_url = f"https://www.gravatar.com/avatar/{email_md5}?s=256&d=404"
    profile_json_url = f"https://en.gravatar.com/{email_md5}.json"

    display_name = None
    profile_url = f"https://gravatar.com/{email_md5}"

    # Verify avatar existence via HTTP HEAD / GET
    try:
        req = urllib.request.Request(avatar_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                pass
            else:
                return None
    except Exception:
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
                    platform="GitHub",
                    account_handle=clean_handle,
                    account_real_name=gh_user.get("real_name") or "",
                    account_bio=gh_user.get("bio") or "",
                    target_name=target_name,
                    target_email=target_email
                )
                if tie.get("is_rejected"):
                    return None
        except Exception:
            pass

    try:
        req = urllib.request.Request(avatar_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            # Check content-type is image
            c_type = resp.headers.get("Content-Type", "")
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

    for h in probe_handles[:5]:
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

    # 4. OpenGraph Images from Discovered Personal Sites
    if personal_site_urls:
        for site_url in personal_site_urls[:3]:
            og = probe_opengraph_avatar(site_url)
            if og and og["image_url"] not in seen_image_urls:
                seen_image_urls.add(og["image_url"])
                discovered_images.append(og)

    # 5. Verified Platform Avatars (e.g. Pinterest from profile prober)
    if extra_avatars:
        for av in extra_avatars:
            av_url = av.get("url") or av.get("image_url")
            if av_url and av_url not in seen_image_urls:
                seen_image_urls.add(av_url)
                plat = av.get("platform", "Platform")
                handle_str = av.get("handle") or target_name or "profile"
                discovered_images.append({
                    "platform": plat,
                    "badge": f"{plat.lower()}.com",
                    "source": f"{plat} Profile Avatar",
                    "image_url": av_url,
                    "thumbnail_url": av_url,
                    "profile_url": av.get("profile_url", ""),
                    "label": f"@{handle_str} ({plat})",
                    "confidence": 0.95,
                    "is_verified": True,
                    "reverse_search_links": build_reverse_image_search_links(av_url)
                })

    return discovered_images
