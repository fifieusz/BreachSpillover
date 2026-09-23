"""
BreachSpillover - Multi-Country Telecom & Civil Directory Reconnaissance Engine
Provides E.164 phone intelligence, carrier detection, and direct national registry
routing for Norway, Sweden, Denmark, Poland, USA/Canada, UK, Germany, and international.
"""

import re
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional, Tuple

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Country codes & metadata
COUNTRY_CODE_MAP = {
    "+47": {"iso": "NO", "country": "Norway", "currency": "NOK", "continent": "Europe"},
    "+46": {"iso": "SE", "country": "Sweden", "currency": "SEK", "continent": "Europe"},
    "+45": {"iso": "DK", "country": "Denmark", "currency": "DKK", "continent": "Europe"},
    "+48": {"iso": "PL", "country": "Poland", "currency": "PLN", "continent": "Europe"},
    "+1":  {"iso": "US", "country": "United States / Canada", "currency": "USD", "continent": "North America"},
    "+44": {"iso": "GB", "country": "United Kingdom", "currency": "GBP", "continent": "Europe"},
    "+49": {"iso": "DE", "country": "Germany", "currency": "EUR", "continent": "Europe"},
    "+33": {"iso": "FR", "country": "France", "currency": "EUR", "continent": "Europe"},
    "+31": {"iso": "NL", "country": "Netherlands", "currency": "EUR", "continent": "Europe"},
    "+358": {"iso": "FI", "country": "Finland", "currency": "EUR", "continent": "Europe"},
}

def parse_and_detect_phone(raw_phone: str) -> Dict[str, Any]:
    """
    Cleans raw telephone strings and extracts international dialing prefix,
    ISO country code, national number, line type heuristic, and E.164 formatting.
    """
    if not raw_phone:
        return {"is_valid": False, "raw": "", "country": "Unknown", "iso": "UNKNOWN"}

    cleaned = re.sub(r"[^\d+]", "", raw_phone.strip())
    # Normalize leading 00 to +
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    
    detected_prefix = None
    country_info = None

    # Sort prefixes by length descending so +358 is checked before +35
    for prefix in sorted(COUNTRY_CODE_MAP.keys(), key=lambda x: -len(x)):
        if cleaned.startswith(prefix):
            detected_prefix = prefix
            country_info = COUNTRY_CODE_MAP[prefix]
            break

    # If no leading +, inspect typical national lengths
    if not detected_prefix:
        digits_only = re.sub(r"\D", "", cleaned)
        if len(digits_only) == 8:
            # 8 digits is standard Norwegian or Danish
            detected_prefix = "+47"
            country_info = COUNTRY_CODE_MAP["+47"]
            cleaned = "+47" + digits_only
        elif len(digits_only) == 9:
            # 9 digits is standard Polish
            detected_prefix = "+48"
            country_info = COUNTRY_CODE_MAP["+48"]
            cleaned = "+48" + digits_only
        elif len(digits_only) == 10 and digits_only.startswith("0"):
            # Swedish, UK, or German local format (070..., 07..., 01...)
            detected_prefix = "+46"
            country_info = COUNTRY_CODE_MAP["+46"]
            cleaned = "+46" + digits_only[1:]
        elif len(digits_only) == 10:
            # US 10-digit standard
            detected_prefix = "+1"
            country_info = COUNTRY_CODE_MAP["+1"]
            cleaned = "+1" + digits_only

    if not country_info:
        country_info = {"iso": "GLOBAL", "country": "International", "currency": "", "continent": "Global"}
        detected_prefix = "+" + re.match(r"\+(\d{1,3})", cleaned).group(1) if cleaned.startswith("+") else ""

    digits_only = re.sub(r"\D", "", cleaned)
    
    # Line type heuristic
    line_type = "Mobile / Cellular"
    if detected_prefix == "+47":
        # In Norway, mobile numbers traditionally begin with 4xx or 9xx
        nat = digits_only[2:] if digits_only.startswith("47") else digits_only
        if nat and nat[0] in ("4", "9"):
            line_type = "Norwegian Mobile"
        else:
            line_type = "Norwegian Landline / Fixed VoIP"
    elif detected_prefix == "+48":
        # In Poland, standard 9 digits
        line_type = "Polish Mobile / Telecommunication"
    elif detected_prefix == "+46":
        nat = digits_only[2:] if digits_only.startswith("46") else digits_only
        if nat and nat.startswith("7"):
            line_type = "Swedish Mobile"
        else:
            line_type = "Swedish Geographic Landline"
    elif detected_prefix == "+1":
        line_type = "North American Numbering Plan (NANP)"

    return {
        "is_valid": len(digits_only) >= 7,
        "raw": raw_phone,
        "e164": cleaned if cleaned.startswith("+") else "+" + cleaned,
        "country_prefix": detected_prefix,
        "iso": country_info["iso"],
        "country_name": country_info["country"],
        "continent": country_info.get("continent", "Global"),
        "line_type": line_type,
        "digits_only": digits_only
    }


def get_country_directories(
    query: str,
    country_iso: Optional[str] = None,
    query_type: str = "auto"
) -> List[Dict[str, Any]]:
    """
    Returns high-accuracy national civil registries and telephone directories
    tailored to the target's country code or inferred region.
    """
    clean_q = query.strip()
    if not clean_q:
        return []

    is_phone = bool(re.search(r"\d{3,}", clean_q))
    iso = (country_iso or "").upper().strip()

    # If iso is not supplied and query is a phone number, detect automatically
    if not iso and is_phone:
        parsed = parse_and_detect_phone(clean_q)
        iso = parsed.get("iso", "GLOBAL")

    encoded_q = urllib.parse.quote(clean_q)
    encoded_quote = urllib.parse.quote(f'"{clean_q}"')
    digits_only = re.sub(r"\D", "", clean_q)

    # Dictionary of authoritative country directories
    all_directories = {
        "NO": [
            {
                "country": "Norway",
                "flag": "NO",
                "name": "Opplysningen 1881",
                "category": "Civil & Phone Registry",
                "badge": "1881.no",
                "description": "Norway's definitive public telephone, residential address, and civil records index.",
                "url": f"https://www.1881.no/?query={encoded_q}&type=person" if not is_phone else f"https://www.1881.no/?query={digits_only[-8:]}",
                "is_primary": True
            },
            {
                "country": "Norway",
                "flag": "NO",
                "name": "Gule Sider Person",
                "category": "Address Directory",
                "badge": "gulesider.no",
                "description": "Eniro Norway public yellow/white pages directory for residential addresses and mobile listings.",
                "url": f"https://www.gulesider.no/person/resultat/{encoded_q}",
                "is_primary": False
            }
        ],
        "SE": [
            {
                "country": "Sweden",
                "flag": "SE",
                "name": "Hitta.se",
                "category": "Civil Registry & Telephone",
                "badge": "hitta.se",
                "description": "Sweden's premier citizen lookup: residential addresses, telecom numbers, and cohabitants.",
                "url": f"https://www.hitta.se/s%C3%B6k?vad={encoded_q}&typ=pers",
                "is_primary": True
            },
            {
                "country": "Sweden",
                "flag": "SE",
                "name": "Ratsit Person",
                "category": "Civil Registry",
                "badge": "ratsit.se",
                "description": "Authoritative Swedish open civil register: birthdays, registered addresses, and corporate filings.",
                "url": f"https://www.ratsit.se/sok/person?vem={encoded_q}",
                "is_primary": False
            },
            {
                "country": "Sweden",
                "flag": "SE",
                "name": "Eniro Sverige",
                "category": "Phone Directory",
                "badge": "eniro.se",
                "description": "Swedish telephone white pages and reverse number directory.",
                "url": f"https://www.eniro.se/personer/{encoded_q}" if not is_phone else f"https://www.eniro.se/telefonnummer/{digits_only[-9:]}",
                "is_primary": False
            }
        ],
        "DK": [
            {
                "country": "Denmark",
                "flag": "DK",
                "name": "Krak Person",
                "category": "National Directory",
                "badge": "krak.dk",
                "description": "Denmark's primary public telephone and civil address directory.",
                "url": f"https://www.krak.dk/person/resultat/{encoded_q}" if not is_phone else f"https://www.krak.dk/telefonnummer/{digits_only[-8:]}",
                "is_primary": True
            },
            {
                "country": "Denmark",
                "flag": "DK",
                "name": "De Gule Sider Danmark",
                "category": "White Pages",
                "badge": "degulesider.dk",
                "description": "Danish residential telecom and person lookup index.",
                "url": f"https://www.degulesider.dk/person/resultat/{encoded_q}",
                "is_primary": False
            }
        ],
        "PL": [
            {
                "country": "Poland",
                "flag": "PL",
                "name": "Infonumer.pl",
                "category": "Phone Lookup & Caller ID",
                "badge": "infonumer.pl",
                "description": "Polish reverse phone directory, caller reputation, and business registration index.",
                "url": f"https://infonumer.pl/numer/{digits_only[-9:]}" if is_phone else f"https://infonumer.pl/szukaj?q={encoded_q}",
                "is_primary": True
            },
            {
                "country": "Poland",
                "flag": "PL",
                "name": "Książka Telefoniczna",
                "category": "White Pages",
                "badge": "ksiazka-telefoniczna.com.pl",
                "description": "National Polish telephone and residential citizen directory.",
                "url": f"https://ksiazka-telefoniczna.com.pl/?s={encoded_q}",
                "is_primary": False
            },
            {
                "country": "Poland",
                "flag": "PL",
                "name": "Panorama Firm / Baza Osób",
                "category": "Business & Sole Traders",
                "badge": "panoramafirm.pl",
                "description": "Poland's corporate and registered sole proprietorship directory (CEIDG lookup).",
                "url": f"https://panoramafirm.pl/szukaj?q={encoded_q}",
                "is_primary": False
            }
        ],
        "US": [
            {
                "country": "United States",
                "flag": "US",
                "name": "NumLookup",
                "category": "Reverse Phone & Carrier API",
                "badge": "numlookup.com",
                "description": "Free US/Canada reverse phone lookup: owner name, carrier network, and line status.",
                "url": f"https://www.numlookup.com/",
                "is_primary": True
            },
            {
                "country": "United States",
                "flag": "US",
                "name": "TruePeopleSearch",
                "category": "Public Records & Addresses",
                "badge": "truepeoplesearch.com",
                "description": "Comprehensive US public records aggregator: past addresses, relatives, and phone records.",
                "url": f"https://www.truepeoplesearch.com/results?name={encoded_q}" if not is_phone else f"https://www.truepeoplesearch.com/results?phoneno={digits_only[-10:]}",
                "is_primary": False
            },
            {
                "country": "United States",
                "flag": "US",
                "name": "FastPeopleSearch",
                "category": "Public Directory",
                "badge": "fastpeoplesearch.com",
                "description": "High-speed US white pages and contact genealogy index.",
                "url": f"https://www.fastpeoplesearch.com/name/{encoded_q.replace('%20', '-')}" if not is_phone else f"https://www.fastpeoplesearch.com/{digits_only[-10:]}",
                "is_primary": False
            }
        ],
        "GB": [
            {
                "country": "United Kingdom",
                "flag": "GB",
                "name": "Who-Called.co.uk",
                "category": "Reverse Phone & Spam Intelligence",
                "badge": "who-called.co.uk",
                "description": "United Kingdom reverse telephone lookup, spam score, and caller identification.",
                "url": f"https://who-called.co.uk/Number/{digits_only[-10:] if is_phone else encoded_q}",
                "is_primary": True
            },
            {
                "country": "United Kingdom",
                "flag": "GB",
                "name": "192.com People Search",
                "category": "Electoral Roll & Civil Directory",
                "badge": "192.com",
                "description": "UK Electoral Roll and Companies House executive person directory.",
                "url": f"https://www.192.com/people/search/?name={encoded_q}",
                "is_primary": False
            }
        ],
        "DE": [
            {
                "country": "Germany",
                "flag": "DE",
                "name": "Das Telefonbuch",
                "category": "National Phone Directory",
                "badge": "dastelefonbuch.de",
                "description": "Germany's official national telephone and postal address book.",
                "url": f"https://www.dastelefonbuch.de/Personen/{encoded_q}" if not is_phone else f"https://www.dastelefonbuch.de/Rueckwaerts-Suche/{digits_only}",
                "is_primary": True
            },
            {
                "country": "Germany",
                "flag": "DE",
                "name": "Tellows Deutschland",
                "category": "Reverse Caller ID",
                "badge": "tellows.de",
                "description": "German reverse phone caller identification, line risk, and geographic exchange.",
                "url": f"https://www.tellows.de/num/{digits_only if is_phone else encoded_q}",
                "is_primary": False
            }
        ]
    }

    # Universal search operators that work across every country
    universal_tools = [
        {
            "country": "Universal",
            "flag": "INTL",
            "name": "Sync.me Global Reverse Lookup",
            "category": "Global Caller ID",
            "badge": "sync.me",
            "description": "International reverse phone directory covering 100+ countries.",
            "url": f"https://sync.me/search/?number={digits_only}" if is_phone else f"https://sync.me/",
            "is_primary": False
        },
        {
            "country": "Universal",
            "flag": "DORK",
            "name": "Exact Telephony Google Dork",
            "category": "Search Operators",
            "badge": "google.com",
            "description": "Searches for raw paste site leaks, forum posts, and documents mentioning this phone or name.",
            "url": f"https://www.google.com/search?q={encoded_quote}",
            "is_primary": False
        }
    ]

    results = []
    # If a specific country is matched, prioritize its directories first
    if iso in all_directories:
        results.extend(all_directories[iso])
    
    # Append remaining European / global directories for broad cross-referencing
    for k, dirs in all_directories.items():
        if k != iso:
            results.extend(dirs)
            
    results.extend(universal_tools)
    return results


def query_live_international_telecom(
    query_text: str,
    country_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for international telecom and citizen directory intelligence.
    Extracts phone metadata, executes live scraper for Norway 1881 / Poland when applicable,
    and returns organized, 1-click directory dispatchers.
    """
    parsed = parse_and_detect_phone(query_text)
    detected_iso = country_hint.upper() if country_hint else parsed.get("iso", "GLOBAL")

    directories = get_country_directories(
        query=query_text,
        country_iso=detected_iso
    )

    # If query is a Norwegian name or number, execute live 1881 probe
    live_records = []
    if detected_iso == "NO" or parsed.get("country_prefix") == "+47":
        from backend.live_osint import query_1881_directory
        try:
            live_records = query_1881_directory(query_text)
        except Exception:
            pass

    return {
        "success": True,
        "query": query_text,
        "telecom_profile": parsed,
        "detected_country": parsed.get("country_name", "International"),
        "detected_iso": detected_iso,
        "live_records": live_records,
        "directories": directories
    }
