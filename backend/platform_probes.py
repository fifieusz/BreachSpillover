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
    """Queries Steam Community XML profile endpoint for authentic gamer personas (handles vanity URLs, SteamID64, and full URLs)."""
    raw_h = (handle or "").strip()
    if not raw_h:
        return None

    # Handle full Steam Community URLs
    if "steamcommunity.com" in raw_h:
        m_id = re.search(r'steamcommunity\.com/id/([a-zA-Z0-9_\-\.]+)', raw_h, re.I)
        m_prof = re.search(r'steamcommunity\.com/profiles/(\d{15,25})', raw_h, re.I)
        if m_id:
            clean_h = m_id.group(1).strip()
            url = f"https://steamcommunity.com/id/{urllib.parse.quote(clean_h)}/?xml=1"
        elif m_prof:
            clean_h = m_prof.group(1).strip()
            url = f"https://steamcommunity.com/profiles/{clean_h}/?xml=1"
        else:
            return None
    elif re.match(r'^\d{16,20}$', raw_h):
        clean_h = raw_h
        url = f"https://steamcommunity.com/profiles/{clean_h}/?xml=1"
    else:
        clean_h = raw_h.strip()
        if len(clean_h) < 3:
            return None
        url = f"https://steamcommunity.com/id/{urllib.parse.quote(clean_h)}/?xml=1"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/xml,text/xml"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                xml = resp.read().decode("utf-8", errors="ignore")
                steam_id_m = re.search(r'<steamID><!\[CDATA\[(.*?)\]\]></steamID>', xml) or re.search(r'<steamID>(.*?)</steamID>', xml)
                if not steam_id_m:
                    return None

                persona = steam_id_m.group(1).strip()
                id64_m = re.search(r'<steamID64>(.*?)</steamID64>', xml)
                steam_id_64 = id64_m.group(1).strip() if id64_m else None

                custom_url_m = re.search(r'<customURL><!\[CDATA\[(.*?)\]\]></customURL>', xml) or re.search(r'<customURL>(.*?)</customURL>', xml)
                custom_url = custom_url_m.group(1).strip() if custom_url_m else None

                real_m = re.search(r'<realname><!\[CDATA\[(.*?)\]\]></realname>', xml) or re.search(r'<realname>(.*?)</realname>', xml)
                real_name = real_m.group(1).strip() if real_m else None

                loc_m = re.search(r'<location><!\[CDATA\[(.*?)\]\]></location>', xml) or re.search(r'<location>(.*?)</location>', xml)
                loc_str = loc_m.group(1).strip() if loc_m else None

                avatar_m = re.search(r'<avatarFull><!\[CDATA\[(.*?)\]\]></avatarFull>', xml) or re.search(r'<avatarFull>(.*?)</avatarFull>', xml)
                avatar_u = avatar_m.group(1).strip() if avatar_m else None

                sum_m = re.search(r'<summary><!\[CDATA\[(.*?)\]\]></summary>', xml, re.DOTALL) or re.search(r'<summary>(.*?)</summary>', xml, re.DOTALL)
                summary_raw = sum_m.group(1).strip() if sum_m else ""
                clean_summary = re.sub(r'<[^>]+>', ' ', summary_raw).strip()

                final_url = f"https://steamcommunity.com/id/{custom_url}" if custom_url else (f"https://steamcommunity.com/profiles/{steam_id_64}" if steam_id_64 else f"https://steamcommunity.com/id/{clean_h}")

                ctx_parts = []
                if steam_id_64:
                    ctx_parts.append(f"SteamID64: {steam_id_64}")
                if persona:
                    ctx_parts.append(f"Persona: '{persona}'")
                if real_name:
                    ctx_parts.append(f"Real Name: {real_name}")
                if loc_str:
                    ctx_parts.append(f"Location: {loc_str}")
                if clean_summary:
                    ctx_parts.append(f"Bio: {clean_summary[:120]}")

                # Short handle vanity collision protection
                is_short = len(clean_h) <= 4 and not re.match(r'^\d+$', clean_h)
                is_persona_discordant = is_short and persona.lower() != clean_h.lower()

                return {
                    "platform": "Steam",
                    "handle": custom_url or clean_h,
                    "url": final_url,
                    "profile_url": final_url,
                    "persona_name": persona,
                    "name": persona,
                    "custom_url": custom_url,
                    "steam_id_64": steam_id_64,
                    "real_name": real_name,
                    "location": loc_str,
                    "summary": clean_summary,
                    "avatar_url": avatar_u,
                    "is_verified": bool(not is_persona_discordant and (persona or real_name)),
                    "is_suspected": bool(is_persona_discordant),
                    "confidence": 0.50 if is_persona_discordant else (0.90 if real_name else 0.85),
                    "context": f"Active Steam Community gaming profile ({' • '.join(ctx_parts)})"
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
        with urllib.request.urlopen(req, timeout=1.5) as resp:
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
    """
    Queries Keybase public directory for cryptographic proofs and cross-platform identity links.
    Extracts verified Twitter, GitHub, Reddit, HackerNews, and personal domain attestations.
    """
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
                    proofs = user_data.get("proofs_summary", {}).get("all", [])

                    linked_proofs = []
                    proof_tokens = []
                    for p in proofs:
                        ptype = p.get("proof_type")
                        ntag = p.get("nametag")
                        surl = p.get("service_url")
                        if ptype and ntag:
                            linked_proofs.append({
                                "platform": ptype,
                                "handle": ntag,
                                "url": surl
                            })
                            proof_tokens.append(f"{ptype}:{ntag}")

                    ctx_parts = [f"Keybase verified identity '{clean_h}'"]
                    if prof.get("full_name"):
                        ctx_parts.append(f"Name: {prof.get('full_name')}")
                    if proof_tokens:
                        ctx_parts.append(f"Cryptographic proofs: {', '.join(proof_tokens[:5])}")

                    return {
                        "platform": "Keybase",
                        "handle": clean_h,
                        "real_name": prof.get("full_name"),
                        "location": prof.get("location"),
                        "bio": prof.get("bio"),
                        "url": f"https://keybase.io/{clean_h}",
                        "linked_identities": linked_proofs,
                        "is_verified": True,
                        "confidence": 0.98,
                        "context": " - ".join(ctx_parts)
                    }
    except Exception:
        pass
    return None


def query_hackernews_user(handle: str) -> Optional[Dict[str, Any]]:
    """
    Queries official Hacker News Firebase REST API for authentic developer/founder accounts.
    Extracts karma rating, account creation epoch, and biographical submissions.
    """
    clean_h = handle.strip().lower()
    if not clean_h or len(clean_h) < 2:
        return None

    url = f"https://hacker-news.firebaseio.com/v0/user/{urllib.parse.quote(clean_h)}.json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                raw = resp.read().decode("utf-8", errors="ignore")
                if not raw or raw.strip() == "null":
                    return None
                data = json.loads(raw)
                if data and isinstance(data, dict) and data.get("id"):
                    hn_id = data.get("id")
                    karma = data.get("karma", 0)
                    about_raw = data.get("about", "")
                    # Clean html tags from about text
                    about_clean = re.sub(r'<[^>]+>', ' ', about_raw).strip() if about_raw else ""
                    sub_count = len(data.get("submitted", []))

                    ctx = f"Hacker News tech account '{hn_id}' (Karma: {karma}, Submissions: {sub_count})"
                    if about_clean:
                        ctx += f" - Bio: {about_clean[:120]}"

                    return {
                        "platform": "HackerNews",
                        "handle": hn_id,
                        "url": f"https://news.ycombinator.com/user?id={hn_id}",
                        "display_name": hn_id,
                        "bio": about_clean or None,
                        "karma": karma,
                        "created": data.get("created"),
                        "submitted_count": sub_count,
                        "is_verified": karma > 5,
                        "confidence": 0.90 if karma > 10 else 0.80,
                        "context": ctx
                    }
    except Exception:
        pass
    return None


def query_wayback_snapshots(target_url: str) -> Optional[Dict[str, Any]]:
    """
    Queries Wayback Machine Availability API to uncover archived historical snapshots
    of target personal domains, portfolios, or deleted social footprints.
    """
    clean_u = (target_url or "").strip()
    if not clean_u or "." not in clean_u:
        return None
    if not clean_u.startswith("http"):
        clean_u = f"https://{clean_u}"

    api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(clean_u)}"
    req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                snap = data.get("archived_snapshots", {}).get("closest")
                if snap and snap.get("available"):
                    ts = snap.get("timestamp", "")
                    formatted_ts = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else ts
                    return {
                        "platform": "Wayback Machine",
                        "target_url": clean_u,
                        "archive_url": snap.get("url"),
                        "timestamp": formatted_ts,
                        "status": snap.get("status"),
                        "is_verified": True,
                        "confidence": 0.95,
                        "context": f"Internet Archive Wayback Machine preserves historical snapshot from {formatted_ts}"
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


def query_gravatar_handle(handle: str) -> Optional[Dict[str, Any]]:
    """Queries Gravatar Public JSON API by handle/username for verified avatars, display names, and locations."""
    clean_h = handle.strip().lower()
    if not clean_h or len(clean_h) < 3:
        return None

    url = f"https://en.gravatar.com/{urllib.parse.quote(clean_h)}.json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                entries = data.get("entry", [])
                if entries:
                    ent = entries[0]
                    disp = ent.get("displayName")
                    pref_user = ent.get("preferredUsername") or clean_h
                    loc = ent.get("currentLocation")
                    about = ent.get("aboutMe")
                    prof_url = ent.get("profileUrl") or f"https://gravatar.com/{pref_user}"
                    photos = ent.get("photos", [])
                    photo_url = photos[0].get("value") if photos else None

                    ctx_parts = [f"Gravatar verified handle '@{pref_user}'"]
                    if disp:
                        ctx_parts.append(f"Display Name: {disp}")
                    if loc:
                        ctx_parts.append(f"Location: {loc}")

                    return {
                        "platform": "Gravatar",
                        "handle": pref_user,
                        "url": prof_url,
                        "display_name": disp,
                        "real_name": disp if (disp and " " in disp) else None,
                        "location": loc,
                        "bio": about,
                        "avatar_url": photo_url,
                        "is_verified": True,
                        "confidence": 0.95,
                        "context": " - ".join(ctx_parts)
                    }
    except Exception:
        pass
    return None


def query_twitch_channel(handle: str) -> Optional[Dict[str, Any]]:
    """Queries Twitch public channel page for verified streamer presence and bio descriptions."""
    clean_h = handle.strip().lower()
    if not clean_h or len(clean_h) < 3:
        return None

    url = f"https://www.twitch.tv/{urllib.parse.quote(clean_h)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                html = resp.read().decode("utf-8", errors="ignore")
                m_title = re.search(r'<title>(.*?)</title>', html)
                title = m_title.group(1).strip() if m_title else ""
                # Non-existent or generic channels only output "Twitch"
                if title and title != "Twitch" and clean_h in title.lower():
                    import html as html_lib
                    m_desc = re.search(r'property="og:description"\s+content="([^"]*)"', html) or re.search(r'name="description"\s+content="([^"]*)"', html)
                    raw_desc = m_desc.group(1).strip() if m_desc else ""
                    desc = html_lib.unescape(raw_desc)
                    desc = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50-\u2b55\u203c-\u3299]', '', desc).strip()
                    title = html_lib.unescape(title)
                    title = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50-\u2b55\u203c-\u3299]', '', title).strip()

                    m_img = re.search(r'property="og:image"\s+content="([^"]*)"', html)
                    avatar = m_img.group(1).strip() if m_img else None

                    return {
                        "platform": "Twitch",
                        "handle": clean_h,
                        "url": url,
                        "display_name": clean_h,
                        "bio": desc,
                        "avatar_url": avatar,
                        "is_verified": True,
                        "confidence": 0.90,
                        "context": f"Active Twitch channel: {title}" + (f" - Bio: {desc[:100]}" if desc else "")
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
    Chess.com, Steam, Roblox, GitHub, GitLab, DockerHub, Duolingo, Keybase, Telegram, Gravatar, and Twitch.
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
        probe_funcs = [
            query_chess_profile,
            query_steam_xml_profile,
            query_roblox_user,
            query_github_user,
            query_gitlab_user,
            query_dockerhub_user,
            query_duolingo_user,
            query_keybase_user,
            query_telegram_profile,
            query_gravatar_handle,
            query_twitch_channel,
            query_hackernews_user
        ]
        hits = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as sub_ex:
            f_hits = [sub_ex.submit(fn, h) for fn in probe_funcs]
            for fut in concurrent.futures.as_completed(f_hits):
                try:
                    res = fut.result()
                    if res:
                        hits.append(res)
                except Exception:
                    pass
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
