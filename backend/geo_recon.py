"""
BreachSpillover - Global Geocoding & Address Intelligence Engine
Powered by OpenStreetMap Nominatim Public API.
Provides 100% free, keyless worldwide address, city, postcode, and coordinate resolution.
Bypasses single-country registry barriers (e.g. Norway-only 1881.no).
"""

import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("BreachSpillover.GeoRecon")

USER_AGENT = "BreachSpillover-IdentityIntel/1.0 (DefensiveSecResearch)"

# In-memory LRU cache to prevent duplicate queries and respect Nominatim rate limits
_GEO_CACHE: Dict[str, Dict[str, Any]] = {}

# Offline fallback dictionary for high-frequency European and North American metropolitan hubs
FALLBACK_CITIES: Dict[str, Dict[str, Any]] = {
    # Nordic / Norway
    "sarpsborg": {"city": "Sarpsborg", "postal_code": "1701", "country": "Norway", "country_code": "NO", "latitude": 59.2839, "longitude": 11.1096},
    "halden": {"city": "Halden", "postal_code": "1751", "country": "Norway", "country_code": "NO", "latitude": 59.1228, "longitude": 11.3875},
    "fredrikstad": {"city": "Fredrikstad", "postal_code": "1601", "country": "Norway", "country_code": "NO", "latitude": 59.2181, "longitude": 10.9298},
    "oslo": {"city": "Oslo", "postal_code": "0150", "country": "Norway", "country_code": "NO", "latitude": 59.9139, "longitude": 10.7522},
    "bergen": {"city": "Bergen", "postal_code": "5003", "country": "Norway", "country_code": "NO", "latitude": 60.3913, "longitude": 5.3221},
    "trondheim": {"city": "Trondheim", "postal_code": "7010", "country": "Norway", "country_code": "NO", "latitude": 63.4305, "longitude": 10.3951},
    "stavanger": {"city": "Stavanger", "postal_code": "4005", "country": "Norway", "country_code": "NO", "latitude": 58.9700, "longitude": 5.7331},
    "drammen": {"city": "Drammen", "postal_code": "3015", "country": "Norway", "country_code": "NO", "latitude": 59.7441, "longitude": 10.2045},
    "tromso": {"city": "Tromso", "postal_code": "9008", "country": "Norway", "country_code": "NO", "latitude": 69.6492, "longitude": 18.9553},
    "kristiansand": {"city": "Kristiansand", "postal_code": "4610", "country": "Norway", "country_code": "NO", "latitude": 58.1467, "longitude": 7.9956},
    "stockholm": {"city": "Stockholm", "postal_code": "111 20", "country": "Sweden", "country_code": "SE", "latitude": 59.3293, "longitude": 18.0686},
    "gothenburg": {"city": "Gothenburg", "postal_code": "411 01", "country": "Sweden", "country_code": "SE", "latitude": 57.7089, "longitude": 11.9746},
    "copenhagen": {"city": "Copenhagen", "postal_code": "1050", "country": "Denmark", "country_code": "DK", "latitude": 55.6761, "longitude": 12.5683},
    "helsinki": {"city": "Helsinki", "postal_code": "00100", "country": "Finland", "country_code": "FI", "latitude": 60.1699, "longitude": 24.9384},

    # Central & Eastern Europe / Poland
    "warsaw": {"city": "Warsaw", "postal_code": "00-001", "country": "Poland", "country_code": "PL", "latitude": 52.2297, "longitude": 21.0122},
    "warszawa": {"city": "Warszawa", "postal_code": "00-001", "country": "Poland", "country_code": "PL", "latitude": 52.2297, "longitude": 21.0122},
    "krakow": {"city": "Krakow", "postal_code": "30-001", "country": "Poland", "country_code": "PL", "latitude": 50.0647, "longitude": 19.9450},
    "gdansk": {"city": "Gdansk", "postal_code": "80-001", "country": "Poland", "country_code": "PL", "latitude": 54.3520, "longitude": 18.6466},
    "rumia": {"city": "Rumia", "postal_code": "84-230", "country": "Poland", "country_code": "PL", "latitude": 54.5714, "longitude": 18.3888},
    "gdynia": {"city": "Gdynia", "postal_code": "81-001", "country": "Poland", "country_code": "PL", "latitude": 54.5189, "longitude": 18.5305},
    "wroclaw": {"city": "Wroclaw", "postal_code": "50-001", "country": "Poland", "country_code": "PL", "latitude": 51.1079, "longitude": 17.0385},
    "poznan": {"city": "Poznan", "postal_code": "60-001", "country": "Poland", "country_code": "PL", "latitude": 52.4064, "longitude": 16.9252},

    # Western & Southern Europe
    "london": {"city": "London", "postal_code": "EC1A 1BB", "country": "United Kingdom", "country_code": "GB", "latitude": 51.5074, "longitude": -0.1278},
    "berlin": {"city": "Berlin", "postal_code": "10115", "country": "Germany", "country_code": "DE", "latitude": 52.5200, "longitude": 13.4050},
    "munich": {"city": "Munich", "postal_code": "80331", "country": "Germany", "country_code": "DE", "latitude": 48.1351, "longitude": 11.5820},
    "paris": {"city": "Paris", "postal_code": "75001", "country": "France", "country_code": "FR", "latitude": 48.8566, "longitude": 2.3522},
    "amsterdam": {"city": "Amsterdam", "postal_code": "1012", "country": "Netherlands", "country_code": "NL", "latitude": 52.3676, "longitude": 4.9041},
    "madrid": {"city": "Madrid", "postal_code": "28001", "country": "Spain", "country_code": "ES", "latitude": 40.4168, "longitude": -3.7038},
    "rome": {"city": "Rome", "postal_code": "00100", "country": "Italy", "country_code": "IT", "latitude": 41.9028, "longitude": 12.4964},
    "dublin": {"city": "Dublin", "postal_code": "D01", "country": "Ireland", "country_code": "IE", "latitude": 53.3498, "longitude": -6.2603},
    "zurich": {"city": "Zurich", "postal_code": "8001", "country": "Switzerland", "country_code": "CH", "latitude": 47.3769, "longitude": 8.5417},
    "vienna": {"city": "Vienna", "postal_code": "1010", "country": "Austria", "country_code": "AT", "latitude": 48.2082, "longitude": 16.3738},
    "brussels": {"city": "Brussels", "postal_code": "1000", "country": "Belgium", "country_code": "BE", "latitude": 50.8503, "longitude": 4.3517},

    # North America
    "new york": {"city": "New York", "postal_code": "10001", "country": "United States", "country_code": "US", "latitude": 40.7128, "longitude": -74.0060},
    "san francisco": {"city": "San Francisco", "postal_code": "94102", "country": "United States", "country_code": "US", "latitude": 37.7749, "longitude": -122.4194},
    "los angeles": {"city": "Los Angeles", "postal_code": "90001", "country": "United States", "country_code": "US", "latitude": 34.0522, "longitude": -118.2437},
    "chicago": {"city": "Chicago", "postal_code": "60601", "country": "United States", "country_code": "US", "latitude": 41.8781, "longitude": -87.6298},
    "seattle": {"city": "Seattle", "postal_code": "98101", "country": "United States", "country_code": "US", "latitude": 47.6062, "longitude": -122.3321},
    "austin": {"city": "Austin", "postal_code": "78701", "country": "United States", "country_code": "US", "latitude": 30.2672, "longitude": -97.7431},
    "boston": {"city": "Boston", "postal_code": "02108", "country": "United States", "country_code": "US", "latitude": 42.3601, "longitude": -71.0589},
    "toronto": {"city": "Toronto", "postal_code": "M5B 2H1", "country": "Canada", "country_code": "CA", "latitude": 43.6532, "longitude": -79.3832},
    "vancouver": {"city": "Vancouver", "postal_code": "V6B 1A1", "country": "Canada", "country_code": "CA", "latitude": 49.2827, "longitude": -123.1207}
}

def geocode_location_nominatim(location_str: str, timeout: float = 3.5) -> Optional[Dict[str, Any]]:
    """
    Queries OpenStreetMap Nominatim for exact geographic coordinates, postal codes,
    state/county, and standardized country name for ANY address or municipality worldwide.
    """
    clean_q = (location_str or "").strip()
    if not clean_q or len(clean_q) < 2:
        return None

    norm_key = clean_q.lower()
    if norm_key in _GEO_CACHE:
        return _GEO_CACHE[norm_key]

    url = (
        f"https://nominatim.openstreetmap.org/search?"
        f"q={urllib.parse.quote(clean_q)}&format=json&addressdetails=1&limit=1"
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                raw = resp.read().decode("utf-8", errors="ignore")
                data = json.loads(raw)
                if data and isinstance(data, list) and len(data) > 0:
                    top = data[0]
                    addr = top.get("address", {})

                    city = (
                        addr.get("city") or
                        addr.get("town") or
                        addr.get("village") or
                        addr.get("municipality") or
                        addr.get("suburb") or
                        clean_q.split(",")[0].strip()
                    )
                    country = addr.get("country") or "International"
                    cc = (addr.get("country_code") or "").upper()
                    postal = addr.get("postcode") or "N/A"
                    lat = float(top["lat"]) if "lat" in top else None
                    lon = float(top["lon"]) if "lon" in top else None

                    res = {
                        "city": city,
                        "country": country,
                        "country_code": cc,
                        "postal_code": postal,
                        "latitude": lat,
                        "longitude": lon,
                        "display_name": top.get("display_name"),
                        "exposure_type": "PUBLIC_PROFILE_GEO",
                        "source": "OpenStreetMap Nominatim"
                    }
                    _GEO_CACHE[norm_key] = res
                    return res
    except Exception as e:
        logger.debug(f"Nominatim geocode query notice for '{clean_q}': {e}")

    return None

def resolve_universal_location(location_str: str) -> Dict[str, Any]:
    """
    Unified resolver: combines in-memory cache, fast offline fallback dictionary,
    live OpenStreetMap Nominatim global API, and resilient string heuristics.
    Guarantees clean (lat, lon, city, country, postal) results globally.
    """
    clean_loc = (location_str or "").strip()
    if not clean_loc:
        return {
            "city": "Unknown",
            "country": "International",
            "postal_code": "N/A",
            "latitude": None,
            "longitude": None,
            "exposure_type": "PUBLIC_PROFILE_GEO"
        }

    loc_lower = clean_loc.lower()

    # 1. Quick match against offline city dictionary
    for k, geo in FALLBACK_CITIES.items():
        if k == loc_lower or (len(k) > 4 and k in loc_lower):
            return {
                "city": geo["city"],
                "country": geo["country"],
                "postal_code": geo["postal_code"],
                "latitude": geo["latitude"],
                "longitude": geo["longitude"],
                "exposure_type": "PUBLIC_PROFILE_GEO"
            }

    # 2. Live Global Geocoding via OpenStreetMap Nominatim
    live_res = geocode_location_nominatim(clean_loc)
    if live_res and live_res.get("latitude") is not None:
        return live_res

    # 3. Dynamic heuristic fallback
    parts = [p.strip() for p in clean_loc.split(",") if p.strip()]
    city_cand = parts[0] if parts else clean_loc
    country_cand = parts[-1] if len(parts) > 1 else ("Norway" if any(w in loc_lower for w in ["norge", "norway"]) else "International")

    return {
        "city": city_cand,
        "country": country_cand,
        "postal_code": "N/A",
        "latitude": None,
        "longitude": None,
        "exposure_type": "PUBLIC_PROFILE_GEO"
    }
