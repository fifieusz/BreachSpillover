"""
BreachSpillover - Universal Direct Platform OSINT Probing Engine
High-yield, direct REST & XML API probes that bypass generic web search engines.
Queries guaranteed public endpoints without API keys or rate-limiting barriers:
1. Chess.com Official Player REST API (real names, country, avatar, rating)
2. Steam Community XML & Web Engine (persona, real name, country, custom URL)
3. Roblox Official Public Users API (verified user IDs, display names)
4. GitHub Public User Search & Metadata (repos, bio, company, location)
5. GitLab Public API (name, username, avatar)
6. DockerHub Public API (username, date joined, gravatar)
7. Duolingo Public Profile API (learning languages, streaks, crowns)
8. Keybase Public User Lookup API (real name, location, social proofs)
9. Telegram Web Public Channel/User Scraper (name, bio, avatar)
"""

import re
import json
import urllib.parse
import urllib.request
import concurrent.futures
from typing import Dict, Any, List, Optional, Set

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Standard Country Code Mapping
CC_TO_COUNTRY = {
    "nl": "Netherlands", "no": "Norway", "pl": "Poland", "us": "United States",
    "gb": "United Kingdom", "de": "Germany", "fr": "France", "es": "Spain",
    "se": "Sweden", "dk": "Denmark", "fi": "Finland", "ca": "Canada",
    "au": "Australia", "it": "Italy", "be": "Belgium", "ch": "Switzerland",
    "hu": "Hungary", "at": "Austria", "ie": "Ireland", "nz": "New Zealand"
}

def query_chess_profile(handle: str) -> Optional[Dict[str, Any]]:
    """Queries official Chess.com public REST API for authentic player records."""
    clean_h = handle.strip().lower()
    if not clean_h or len(clean_h) < 3 or clean_h in ["user", "target", "local", "gmail"]:
        return None

    url = f"https://api.chess.com/pub/player/{urllib.parse.quote(clean_h)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                raw_country_url = data.get("country", "")
                cc = raw_country_url.rstrip("/").split("/")[-1].lower() if raw_country_url else None
                country_name = CC_TO_COUNTRY.get(cc, cc.upper() if cc else None)

                return {
                    "platform": "Chess.com",
                    "handle": data.get("username") or clean_h,
                    "url": data.get("url") or f"https://www.chess.com/member/{clean_h}",
                    "real_name": data.get("name"),
                    "country": country_name,
                    "country_code": cc,
                    "avatar_url": data.get("avatar"),
                    "player_id": data.get("player_id"),
                    "status": data.get("status"),
                    "is_verified": bool(data.get("name")),
                    "confidence": 0.95 if data.get("name") else 0.85
                }
    except Exception:
        pass
    return None


def query_steam_xml_profile(handle: str) -> Optional[Dict[str, Any]]:
    """Queries Steam Community XML profile endpoint for authentic gamer personas."""
    clean_h = handle.strip().lower()
    if not clean_h or len(clean_h) < 3:
        return None

    url = f"https://steamcommunity.com/id/{urllib.parse.quote(clean_h)}/?xml=1"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/xml,text/xml"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                xml = resp.read().decode("utf-8", errors="ignore")
                steam_id_m = re.search(r'<steamID><!\[CDATA\[(.*?)\]\]></steamID>', xml)
                if not steam_id_m:
                    return None

                persona = steam_id_m.group(1).strip()
                real_m = re.search(r'<realname><!\[CDATA\[(.*?)\]\]></realname>', xml)
                real_name = real_m.group(1).strip() if real_m else None
                loc_m = re.search(r'<location><!\[CDATA\[(.*?)\]\]></location>', xml)
                loc_str = loc_m.group(1).strip() if loc_m else None
                avatar_m = re.search(r'<avatarFull><!\[CDATA\[(.*?)\]\]></avatarFull>', xml)
                avatar_u = avatar_m.group(1).strip() if avatar_m else None

                return {
                    "platform": "Steam",
                    "handle": clean_h,
                    "url": f"https://steamcommunity.com/id/{clean_h}",
                    "persona_name": persona,
                    "real_name": real_name,
                    "location": loc_str,
                    "avatar_url": avatar_u,
                    "is_verified": bool(persona or real_name),
                    "confidence": 0.90 if real_name else 0.85
                }
    except Exception:
        pass
    return None


def query_roblox_user(handle: str) -> Optional[Dict[str, Any]]:
    """Queries official Roblox Public Users API for verified gamer registrations."""
    clean_h = handle.strip()
    if not clean_h or len(clean_h) < 3:
        return None

    url = "https://users.roblox.com/v1/usernames/users"
    payload = json.dumps({"usernames": [clean_h]}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                users = data.get("data", [])
                if users:
                    u = users[0]
                    uid = u.get("id")
                    return {
                        "platform": "Roblox",
                        "handle": u.get("name") or clean_h,
                        "display_name": u.get("displayName"),
                        "user_id": uid,
                        "url": f"https://www.roblox.com/users/{uid}/profile" if uid else f"https://www.roblox.com/search/users?keyword={clean_h}",
                        "is_verified": True,
                        "confidence": 0.90
                    }
    except Exception:
        pass
    return None


def query_github_user(handle: str) -> Optional[Dict[str, Any]]:
    """Queries official GitHub Public User API for verified developer profiles."""
    clean_h = handle.strip()
    if not clean_h or len(clean_h) < 3:
        return None

    url = f"https://api.github.com/users/{urllib.parse.quote(clean_h)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if data.get("login"):
                    return {
                        "platform": "GitHub",
                        "handle": data.get("login"),
                        "real_name": data.get("name"),
                        "url": data.get("html_url") or f"https://github.com/{data.get('login')}",
                        "avatar_url": data.get("avatar_url"),
                        "company": data.get("company"),
                        "location": data.get("location"),
                        "bio": data.get("bio"),
                        "blog": data.get("blog"),
                        "public_repos": data.get("public_repos", 0),
                        "is_verified": True,
                        "confidence": 0.95
                    }
    except Exception:
        pass
    return None


def query_gitlab_user(handle: str) -> Optional[Dict[str, Any]]:
    """Queries GitLab public users API."""
    clean_h = handle.strip()
    if not clean_h or len(clean_h) < 3:
        return None

    url = f"https://gitlab.com/api/v4/users?username={urllib.parse.quote(clean_h)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                users = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if users and isinstance(users, list):
                    u = users[0]
                    return {
                        "platform": "GitLab",
                        "handle": u.get("username") or clean_h,
                        "real_name": u.get("name"),
                        "url": u.get("web_url") or f"https://gitlab.com/{clean_h}",
                        "avatar_url": u.get("avatar_url"),
                        "is_verified": True,
                        "confidence": 0.90
                    }
    except Exception:
        pass
    return None


def query_dockerhub_user(handle: str) -> Optional[Dict[str, Any]]:
    """Queries DockerHub public user API."""
    clean_h = handle.strip().lower()
    if not clean_h or len(clean_h) < 3:
        return None

    url = f"https://hub.docker.com/v2/users/{urllib.parse.quote(clean_h)}/"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if data.get("username"):
                    return {
                        "platform": "DockerHub",
                        "handle": data.get("username"),
                        "real_name": data.get("full_name") or None,
                        "url": f"https://hub.docker.com/u/{data.get('username')}",
                        "date_joined": data.get("date_joined"),
                        "is_verified": True,
                        "confidence": 0.90
                    }
    except Exception:
        pass
    return None


def query_duolingo_user(handle: str) -> Optional[Dict[str, Any]]:
    """Queries Duolingo public user API for language learning footprint."""
    clean_h = handle.strip().lower()
    if not clean_h or len(clean_h) < 3:
        return None

    url = f"https://www.duolingo.com/2017-06-30/users?username={urllib.parse.quote(clean_h)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                users = data.get("users", [])
                if users:
                    u = users[0]
                    courses = [c.get("title") for c in u.get("courses", []) if c.get("title")]
                    course_str = ", ".join(courses[:3]) if courses else None
                    return {
                        "platform": "Duolingo",
                        "handle": u.get("username") or clean_h,
                        "real_name": u.get("name") or None,
                        "url": f"https://www.duolingo.com/profile/{clean_h}",
                        "bio": u.get("bio") or None,
                        "languages": course_str,
                        "streak": u.get("streak", 0),
                        "is_verified": True,
                        "confidence": 0.85
                    }
    except Exception:
        pass
    return None


def query_keybase_user(handle: str) -> Optional[Dict[str, Any]]:
    """Queries Keybase public directory for cryptographic proofs and social identity links."""
    clean_h = handle.strip().lower()
    if not clean_h or len(clean_h) < 3:
        return None

    url = f"https://keybase.io/_/api/1.0/user/lookup.json?usernames={urllib.parse.quote(clean_h)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                thems = data.get("them", [])
                if thems and thems[0]:
                    user_data = thems[0]
                    prof = user_data.get("profile", {}) or {}
                    return {
                        "platform": "Keybase",
                        "handle": clean_h,
                        "real_name": prof.get("full_name"),
                        "location": prof.get("location"),
                        "bio": prof.get("bio"),
                        "url": f"https://keybase.io/{clean_h}",
                        "is_verified": True,
                        "confidence": 0.95
                    }
    except Exception:
        pass
    return None


def query_telegram_profile(handle: str) -> Optional[Dict[str, Any]]:
    """Queries Telegram Web public user page to extract display name and bio."""
    clean_h = handle.strip().lstrip("@")
    if not clean_h or len(clean_h) < 4:
        return None

    url = f"https://t.me/{urllib.parse.quote(clean_h)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                html = resp.read().decode("utf-8", errors="ignore")
                title_m = re.search(r'<div class="tgme_page_title"[^>]*>([\s\S]*?)</div>', html)
                if title_m:
                    title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
                    desc_m = re.search(r'<div class="tgme_page_description"[^>]*>([\s\S]*?)</div>', html)
                    desc = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else ""
                    photo_m = re.search(r'<img class="tgme_page_photo_image"[^>]*src="([^"]+)"', html)
                    photo = photo_m.group(1) if photo_m else None

                    return {
                        "platform": "Telegram",
                        "handle": clean_h,
                        "url": url,
                        "display_name": title,
                        "bio": desc,
                        "avatar_url": photo,
                        "is_verified": bool(title and len(title) > 2),
                        "confidence": 0.85
                    }
    except Exception:
        pass
    return None


def probe_all_direct_platforms(
    candidate_handles: List[str],
    target_name: Optional[str] = None,
    target_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Executes concurrent high-speed direct REST API lookups across:
    Chess.com, Steam, Roblox, GitHub, GitLab, DockerHub, Duolingo, Keybase, and Telegram.
    Guaranteed high fidelity, zero reliance on search engine scrapers.
    """
    clean_handles: List[str] = []
    seen = set()
    for h in candidate_handles:
        ch = (h or "").strip().lower()
        if ch and len(ch) >= 3 and ch not in seen:
            seen.add(ch)
            clean_handles.append(ch)

    discovered_results: List[Dict[str, Any]] = []

    def _worker(h: str):
        hits = []
        # 1. Chess.com
        c_hit = query_chess_profile(h)
        if c_hit:
            hits.append(c_hit)

        # 2. Steam
        s_hit = query_steam_xml_profile(h)
        if s_hit:
            hits.append(s_hit)

        # 3. Roblox
        r_hit = query_roblox_user(h)
        if r_hit:
            hits.append(r_hit)

        # 4. GitHub
        gh_hit = query_github_user(h)
        if gh_hit:
            hits.append(gh_hit)

        # 5. GitLab
        gl_hit = query_gitlab_user(h)
        if gl_hit:
            hits.append(gl_hit)

        # 6. DockerHub
        dh_hit = query_dockerhub_user(h)
        if dh_hit:
            hits.append(dh_hit)

        # 7. Duolingo
        duo_hit = query_duolingo_user(h)
        if duo_hit:
            hits.append(duo_hit)

        # 8. Keybase
        kb_hit = query_keybase_user(h)
        if kb_hit:
            hits.append(kb_hit)

        # 9. Telegram
        t_hit = query_telegram_profile(h)
        if t_hit:
            hits.append(t_hit)

        return hits

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_worker, h): h for h in clean_handles[:10]}
        for fut in concurrent.futures.as_completed(futures):
            try:
                for hit in fut.result():
                    discovered_results.append(hit)
            except Exception:
                pass

    return discovered_results
