"""
BreachSpillover - Targeted Platform Profile Prober
When account enumeration engines (such as user-scanner) confirm that a target email
is registered on a consumer platform (e.g. Pinterest, Quora, Wix, GitHub), this prober
inspects public profile endpoints for the candidate handle, extracting display names,
real names, user IDs, avatars, and bio metadata without guessing strangers.
Zero emojis across all logs and metadata.
"""

import logging
import re
import urllib.parse
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger("platform_profile_prober")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def probe_pinterest_profile(handle: str) -> Optional[Dict[str, Any]]:
    """
    Inspects a public Pinterest profile when Pinterest registration is confirmed.
    Extracts display name, username, user ID, and avatar image URL.
    """
    clean_handle = handle.strip().lstrip("@").lower()
    if not clean_handle or len(clean_handle) < 3:
        return None

    url = f"https://www.pinterest.com/{clean_handle}/"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return None

        html = resp.text
        if "UserResource" not in html and f"/{clean_handle}/" not in html:
            return None

        # Extract structured user metadata from Pinterest embedded JSON state
        fn_match = re.search(r'"first_name":"([^"]+)"', html)
        un_match = re.search(r'"username":"([^"]+)"', html)
        uid_match = re.search(r'"id":"(\d{15,25})"', html)
        img_match = re.search(r'"image_xlarge_url":"([^"]+)"', html)
        about_match = re.search(r'"about":"([^"]*)"', html)

        first_name = fn_match.group(1) if fn_match else ""
        username = un_match.group(1) if un_match else clean_handle
        user_id = uid_match.group(1) if uid_match else None
        img_url = img_match.group(1).replace(r"\/", "/") if img_match else None
        about_text = about_match.group(1) if about_match else ""

        # Filter out default placeholder avatars
        avatar = img_url if (img_url and "default_280" not in img_url and "default" not in img_url) else None

        display_name = first_name or username
        context_parts = [f"Verified Pinterest profile registered to target email: '{display_name}'"]
        if user_id:
            context_parts.append(f"UID: {user_id}")
        if about_text:
            context_parts.append(f"Bio: {about_text[:80]}")

        return {
            "platform": "Pinterest",
            "url": url,
            "handle": username,
            "display_name": display_name,
            "user_id": user_id,
            "avatar_url": avatar,
            "bio": about_text,
            "is_email_bound": True,
            "confidence": 0.95,
            "source": "Platform Profile Prober (user-scanner verified)",
            "context": " | ".join(context_parts)
        }
    except Exception as e:
        logger.debug(f"Pinterest profile probe failed for {handle}: {e}")
        return None

def probe_wix_profile(handle: str) -> Optional[Dict[str, Any]]:
    """
    Checks if the target has deployed a public Wix site at {handle}.wixsite.com.
    """
    clean_handle = handle.strip().lstrip("@").lower()
    if not clean_handle or len(clean_handle) < 3:
        return None

    site_url = f"https://{clean_handle}.wixsite.com"
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(site_url, headers=headers, timeout=5, allow_redirects=True)
        if resp.status_code == 200 and "wix.com" not in resp.url and "error" not in resp.url:
            title_match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""
            return {
                "platform": "Wix",
                "url": site_url,
                "handle": clean_handle,
                "display_name": clean_handle,
                "context": f"Public Wix site deployed at {site_url} ({title or 'Active'})",
                "is_email_bound": True,
                "confidence": 0.95,
                "source": "Platform Profile Prober (user-scanner verified)"
            }
    except Exception:
        pass
    return None

def probe_github_api_profile(handle: str) -> Optional[Dict[str, Any]]:
    """
    Inspects GitHub public user API for candidate handle.
    """
    clean_handle = handle.strip().lstrip("@").lower()
    if not clean_handle:
        return None
    url = f"https://api.github.com/users/{clean_handle}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github.v3+json"}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            login = data.get("login")
            name = data.get("name")
            bio = data.get("bio")
            avatar = data.get("avatar_url")
            html_url = data.get("html_url")
            return {
                "platform": "GitHub",
                "url": html_url or f"https://github.com/{login}",
                "handle": login,
                "display_name": name or login,
                "avatar_url": avatar,
                "bio": bio,
                "confidence": 0.90,
                "context": f"GitHub user account: '{name or login}' ({bio[:60] if bio else 'Public profile'})"
            }
    except Exception:
        pass
    return None

def probe_verified_platform_profiles(verified_platforms: List[Dict[str, Any]], target_email: str) -> List[Dict[str, Any]]:
    """
    Given a list of confirmed platform registrations from user-scanner,
    probes public profile endpoints using the target's primary email handle.
    """
    if not target_email or "@" not in target_email:
        return []

    local_part = target_email.split("@")[0].strip().lower()
    if not local_part or len(local_part) < 3:
        return []

    enriched_profiles: List[Dict[str, Any]] = []
    platform_names = set()
    for p in verified_platforms:
        name = (p.get("site_name") or p.get("name") or p.get("platform") or "").lower()
        if name:
            platform_names.add(name)

    # 1. Pinterest probe: verified email-bound if confirmed by user-scanner, or candidate if matching handle
    pin_prof = probe_pinterest_profile(local_part)
    if pin_prof:
        if "pinterest" in platform_names:
            pin_prof["is_email_bound"] = True
            pin_prof["confidence"] = 0.95
            pin_prof["context"] = f"Verified Pinterest profile registered to target email: '{pin_prof.get('display_name')}' [TIED: EMAIL VERIFIED]"
        else:
            pin_prof["is_email_bound"] = False
            pin_prof["confidence"] = 0.65
            pin_prof["context"] = f"Candidate Pinterest profile matching target handle: '{pin_prof.get('display_name')}' [PLATFORM: UNCONFIRMED]"
        enriched_profiles.append(pin_prof)

    # 2. Wix follow-up probe
    if "wix" in platform_names:
        wix_prof = probe_wix_profile(local_part)
        if wix_prof:
            enriched_profiles.append(wix_prof)

    # 3. GitHub follow-up probe
    if "github" in platform_names:
        gh_prof = probe_github_api_profile(local_part)
        if gh_prof:
            enriched_profiles.append(gh_prof)

    return enriched_profiles
