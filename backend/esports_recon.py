"""
BreachSpillover - Universal Competitive Gaming & Esports Reconnaissance Engine
Automates passive discovery of competitive esports profiles, tournament participation,
prize earnings, game disciplines, and verified gamertags across public esports registries.

Primary Source: EsportsEarnings.com
Discovers tournament aliases (e.g. @Djessir in Brawlhalla, @s1mple in CS2, @N0tail in Dota 2)
from real names or candidate handles and links them to competitive records.
Strictly authentic OSINT: Zero hardcoding, zero emojis.
"""

import re
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Common game title cleanups
DISCIPLINE_MAP = {
    "brawlhalla": "Brawlhalla",
    "counter-strike-2": "Counter-Strike 2",
    "counter-strike-global-offensive": "CS:GO",
    "dota-2": "Dota 2",
    "league-of-legends": "League of Legends",
    "valorant": "Valorant",
    "rocket-league": "Rocket League",
    "fortnite": "Fortnite",
    "super-smash-bros-ultimate": "Super Smash Bros. Ultimate",
    "super-smash-bros-melee": "Super Smash Bros. Melee",
    "street-fighter-6": "Street Fighter 6",
    "tekken-8": "Tekken 8",
    "rainbow-six-siege": "Rainbow Six Siege",
    "apex-legends": "Apex Legends",
    "overwatch-2": "Overwatch 2",
    "starcraft-ii": "StarCraft II"
}


def query_esports_earnings(
    target_name: str,
    known_handles: Optional[List[str]] = None,
    target_country: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Dynamically queries EsportsEarnings player database for competitive records
    matching a target individual's name or candidate aliases.
    Completely generic for any player globally.
    """
    results: List[Dict[str, Any]] = []
    seen_handles = set()

    clean_name = (target_name or "").strip()
    name_parts = [p.lower() for p in clean_name.split() if len(p) >= 2]
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) >= 2 else ""

    queries_to_try: List[str] = []
    if clean_name and len(clean_name) >= 3:
        queries_to_try.append(clean_name)
    if first_name and len(first_name) >= 3 and first_name != clean_name.lower():
        queries_to_try.append(first_name)
    for h in (known_handles or [])[:3]:
        h_clean = h.strip()
        if h_clean and len(h_clean) >= 3 and h_clean.lower() not in [q.lower() for q in queries_to_try]:
            queries_to_try.append(h_clean)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    for query in queries_to_try:
        url = f"https://www.esportsearnings.com/search?search={urllib.parse.quote(query)}&type=player"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            rows = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', html)
            for r in rows:
                plinks = re.findall(r'<a\s+[^>]*href="(/players/[^"]+)"[^>]*>([\s\S]*?)</a>', r)
                if not plinks:
                    continue

                handle = re.sub(r'<[^>]+>', '', plinks[0][1]).strip()
                rname = re.sub(r'<[^>]+>', '', plinks[1][1]).strip() if len(plinks) > 1 else handle
                purl = plinks[0][0]

                if not handle or handle.lower() in seen_handles:
                    continue

                # Flag / Country extraction
                flag_m = re.search(r'title="([^"]+)"\s+class="flag"', r) or re.search(r'<img\s+[^>]*title="([^"]+)"[^>]*flags', r)
                row_country = flag_m.group(1) if flag_m else None

                # Prize money extraction
                prize_m = re.search(r'\$[\d,]+\.\d{2}', r)
                row_prize = prize_m.group(0) if prize_m else "$0.00"

                # Disambiguation criteria
                rn_low = rname.lower()
                rn_parts = rn_low.split()
                h_low = handle.lower()

                matches_target = False

                # 1. Handle matches known handles
                if any(h_low == (kh or "").lower().strip() for kh in (known_handles or [])):
                    matches_target = True
                # 2. Both first and last name match or initial match (e.g. "Yasir K" matches "Yasir Kadhim")
                elif first_name and last_name:
                    if first_name in rn_low:
                        if last_name in rn_low:
                            matches_target = True
                        elif len(rn_parts) > 1:
                            last_seg = rn_parts[-1].rstrip(".")
                            if last_seg and last_name.startswith(last_seg):
                                matches_target = True
                # 3. Exact full name match
                elif clean_name.lower() == rn_low or rn_low in clean_name.lower():
                    matches_target = True

                if not matches_target:
                    continue

                # Consistency check with target country if known
                if target_country and row_country:
                    t_c = target_country.lower()
                    r_c = row_country.lower()
                    if t_c not in r_c and r_c not in t_c:
                        # Country conflict
                        continue

                # Deep fetch profile details for discipline and social channels
                full_player_url = f"https://www.esportsearnings.com{purl}"
                profile_details = fetch_player_profile_details(full_player_url, headers)

                seen_handles.add(h_low)
                results.append({
                    "gamertag": handle,
                    "real_name_match": rname,
                    "profile_url": full_player_url,
                    "game": profile_details.get("game", "Competitive Fighting Games / Esports"),
                    "earnings": profile_details.get("earnings") or row_prize,
                    "country": profile_details.get("country") or row_country or target_country or "International",
                    "social_links": profile_details.get("social_links", []),
                    "confidence_score": 0.95
                })
        except Exception:
            pass

        if results:
            break

    return results


def fetch_player_profile_details(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Fetches full player profile page to extract specific game title,
    career prize earnings, nationality flag, and verified external social links.
    """
    intel: Dict[str, Any] = {
        "game": "Competitive Esports",
        "earnings": None,
        "country": None,
        "social_links": []
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # 1. Country from 64px main header flag
        flag_m = (
            re.search(r'<img\s+[^>]*src="[^"]*/flags/64/([a-z]{2})\.png"[^>]*title="([^"]+)"', html) or
            re.search(r'<img\s+[^>]*title="([^"]+)"[^>]*src="[^"]*/flags/64/', html)
        )
        if flag_m:
            intel["country"] = flag_m.group(2) if len(flag_m.groups()) >= 2 else flag_m.group(1)

        # 2. Primary game discipline from /games/ URL slug
        game_slugs = re.findall(r'/games/(\d+-([a-z0-9_-]+))', html, re.IGNORECASE)
        if game_slugs:
            slug_name = game_slugs[0][1].lower()
            intel["game"] = DISCIPLINE_MAP.get(slug_name, slug_name.replace("-", " ").title())

        # 3. Exact total tournament earnings
        earnings_m = re.search(r'\$[\d,]+\.\d{2}', html)
        if earnings_m:
            intel["earnings"] = earnings_m.group(0)

        # 4. External social media links (Twitter/X, Twitch, YouTube, Discord)
        ext_links = re.findall(
            r'href=[\'"](https?://(?:twitter\.com|x\.com|twitch\.tv|youtube\.com|steamcommunity\.com)/[^\'"]+)[\'"]',
            html
        )
        for el in ext_links:
            if el not in intel["social_links"]:
                intel["social_links"].append(el)

    except Exception:
        pass

    return intel
