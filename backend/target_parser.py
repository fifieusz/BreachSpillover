"""
BreachSpillover - Universal Target Manifest & Multi-Vector Query Parser
Extracts structured intelligence targets (Email, Phone, Name, Handle, Geo)
from single or composite queries and coordinates multi-pillar investigation routing.
"""

import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

from backend.telecom_recon import reverse_phone_lookup, COUNTRY_CODE_MAP

@dataclass
class TargetManifest:
    raw_query: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    phone_e164: Optional[str] = None
    phone_digits: Optional[str] = None
    phone_country: Optional[str] = None
    phone_carrier: Optional[str] = None
    phone_recon: Optional[Dict[str, Any]] = None
    
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    domain: Optional[str] = None
    
    # Classification & Routing
    target_type: str = "UNKNOWN"  # EMAIL, PHONE, NAME, USERNAME, DOMAIN, COMPOSITE
    active_pillars: List[str] = field(default_factory=list)  # EMAIL, TELECOM, IDENTITY, HANDLE, FUSION
    
    # Storage & Entity Keys
    canonical_email: str = ""
    canonical_display_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "email": self.email,
            "phone": self.phone_e164 or self.phone,
            "phone_digits": self.phone_digits,
            "phone_country": self.phone_country,
            "phone_carrier": self.phone_carrier,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "city": self.city,
            "country": self.country,
            "domain": self.domain,
            "target_type": self.target_type,
            "active_pillars": self.active_pillars,
            "canonical_email": self.canonical_email,
            "canonical_display_name": self.canonical_display_name,
            "has_email": bool(self.email),
            "has_phone": bool(self.phone_e164 or self.phone),
            "has_name": bool(self.name),
            "has_username": bool(self.username),
            "has_fusion": "FUSION" in self.active_pillars
        }


def parse_target_manifest(
    raw_query: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
    username: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None
) -> TargetManifest:
    """
    Parses arbitrary target intel from explicit arguments and/or a raw query string.
    Deconstructs composite queries (e.g. 'John Doe john@example.com +212772014831')
    into distinct vectors and builds a unified TargetManifest.
    """
    raw = (raw_query or "").strip()
    
    # 0. Validate and normalize explicit inputs
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    out_email = None
    if email and isinstance(email, str) and email.strip():
        e_cand = email.strip().lower()
        if re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', e_cand):
            out_email = e_cand
        else:
            # If explicit email parameter contains other tokens (composite) and raw was empty, use it
            if not raw:
                raw = e_cand
            elif e_cand.lower().strip() != raw.lower().strip() and e_cand not in raw:
                raw = f"{raw} {e_cand}"

    out_phone = None
    if phone and isinstance(phone, str) and phone.strip():
        p_cand = phone.strip()
        p_dig = re.sub(r'\D', '', p_cand)
        if 7 <= len(p_dig) <= 15:
            out_phone = p_cand
        else:
            if not raw:
                raw = p_cand
            elif p_cand.lower().strip() != raw.lower().strip() and p_cand not in raw:
                raw = f"{raw} {p_cand}"

    out_name = name.strip() if (name and isinstance(name, str) and name.strip()) else None
    out_username = username.strip().lstrip("@") if (username and isinstance(username, str) and username.strip()) else None
    out_city = city.strip() if (city and isinstance(city, str) and city.strip()) else None
    out_country = country.strip() if (country and isinstance(country, str) and country.strip()) else None
    out_domain = None

    remainder = raw

    # 1. Extract Email from raw query if not explicitly passed
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    if not out_email and remainder:
        email_match = re.search(email_regex, remainder)
        if email_match:
            out_email = email_match.group(0).lower()
            remainder = remainder[:email_match.start()] + " " + remainder[email_match.end():]
    elif out_email and remainder:
        # If email was explicitly passed or already known, remove from remainder
        remainder = re.sub(re.escape(out_email), ' ', remainder, flags=re.IGNORECASE)

    # 2. Extract Phone Number from raw query if not explicitly passed
    phone_recon = None
    if not out_phone and remainder:
        # Check for explicit international phone (e.g. +212 772 014831 or +1-415-555-0199)
        intl_phone_match = re.search(r'(\+\d[\d\s\-\(\)\.]{5,20}\d)', remainder)
        if intl_phone_match:
            candidate = intl_phone_match.group(1).strip()
            digits = re.sub(r'\D', '', candidate)
            if 7 <= len(digits) <= 15:
                out_phone = candidate
                remainder = remainder[:intl_phone_match.start()] + " " + remainder[intl_phone_match.end():]
        else:
            # Check if entire remainder is pure numeric or dial-formatted
            clean_digits = re.sub(r'\D', '', remainder)
            if not re.search(r'[a-zA-Z]', remainder) and 7 <= len(clean_digits) <= 15 and re.match(r'^[+\d\s\-\(\)\.\/]+$', remainder.strip()):
                out_phone = remainder.strip()
                remainder = ""

    if out_phone:
        try:
            phone_recon = reverse_phone_lookup(out_phone)
        except Exception:
            phone_recon = None

    # 3. Extract @handle if present
    if not out_username and remainder:
        handle_match = re.search(r'(?:^|\s)@([a-zA-Z0-9_\-\.]{3,30})\b', remainder)
        if handle_match:
            out_username = handle_match.group(1).strip()
            remainder = remainder[:handle_match.start()] + " " + remainder[handle_match.end():]

    # Clean up punctuation and excess spaces in remainder
    remainder = re.sub(r'[\(\)<>,;:\[\]"\'`]+', ' ', remainder).strip()
    remainder = re.sub(r'\s+', ' ', remainder)

    # 4. Check if remainder is a pure web domain
    known_tlds = [".com", ".net", ".org", ".io", ".co", ".ai", ".gov", ".edu", ".pl", ".de", ".uk", ".dev", ".app", ".nl", ".fr"]
    if remainder and not out_email and not out_name and "." in remainder and not " " in remainder:
        if any(remainder.lower().endswith(tld) for tld in known_tlds):
            out_domain = remainder.lower()
            remainder = ""

    # 5. Extract Name and Location hints from remaining text
    if remainder and not out_name:
        # Check if known country or city name is at the end of remainder
        tokens = remainder.split()
        if len(tokens) >= 2:
            last_token = tokens[-1].lower()
            # Common country names
            matched_geo = False
            for code, meta in COUNTRY_CODE_MAP.items():
                c_name = meta["country"].lower()
                if last_token in c_name or c_name == last_token:
                    if not out_country:
                        out_country = meta["country"]
                    tokens = tokens[:-1]
                    matched_geo = True
                    break
            
            # Common major world cities if not matched as country
            if not matched_geo and not out_city:
                common_cities = {
                    "casablanca": ("Casablanca", "Morocco"),
                    "rabat": ("Rabat", "Morocco"),
                    "marrakech": ("Marrakech", "Morocco"),
                    "tangier": ("Tangier", "Morocco"),
                    "oslo": ("Oslo", "Norway"),
                    "bergen": ("Bergen", "Norway"),
                    "stockholm": ("Stockholm", "Sweden"),
                    "gothenburg": ("Gothenburg", "Sweden"),
                    "copenhagen": ("Copenhagen", "Denmark"),
                    "warsaw": ("Warsaw", "Poland"),
                    "krakow": ("Krakow", "Poland"),
                    "gdansk": ("Gdansk", "Poland"),
                    "wroclaw": ("Wroclaw", "Poland"),
                    "london": ("London", "United Kingdom"),
                    "manchester": ("Manchester", "United Kingdom"),
                    "paris": ("Paris", "France"),
                    "lyon": ("Lyon", "France"),
                    "berlin": ("Berlin", "Germany"),
                    "munich": ("Munich", "Germany"),
                    "hamburg": ("Hamburg", "Germany"),
                    "amsterdam": ("Amsterdam", "Netherlands"),
                    "rotterdam": ("Rotterdam", "Netherlands"),
                    "groningen": ("Groningen", "Netherlands"),
                    "madrid": ("Madrid", "Spain"),
                    "barcelona": ("Barcelona", "Spain"),
                    "rome": ("Rome", "Italy"),
                    "milan": ("Milan", "Italy"),
                    "new york": ("New York", "United States"),
                    "los angeles": ("Los Angeles", "United States"),
                    "chicago": ("Chicago", "United States"),
                    "toronto": ("Toronto", "Canada"),
                    "dubai": ("Dubai", "United Arab Emirates"),
                    "tokyo": ("Tokyo", "Japan")
                }
                if last_token in common_cities:
                    c_name, c_cntry = common_cities[last_token]
                    out_city = c_name
                    if not out_country:
                        out_country = c_cntry
                    tokens = tokens[:-1]
        
        # Check if remainder contains letters and could be a person's name
        cleaned_cand = " ".join(tokens).strip()
        if cleaned_cand and re.search(r'[a-zA-Z]{2,}', cleaned_cand):
            out_name = cleaned_cand

    # Split name into first and last if available
    first_name = None
    last_name = None
    if out_name:
        n_tokens = out_name.split()
        if len(n_tokens) == 1:
            first_name = n_tokens[0].title()
        elif len(n_tokens) >= 2:
            first_name = n_tokens[0].title()
            last_name = " ".join(n_tokens[1:]).title()

    # Determine Active Pillars
    pillars: List[str] = []
    vector_count = 0
    if out_email:
        pillars.append("EMAIL")
        vector_count += 1
    if out_phone:
        pillars.append("TELECOM")
        vector_count += 1
    if out_name:
        pillars.append("IDENTITY")
        vector_count += 1
    if out_username:
        pillars.append("HANDLE")
        vector_count += 1
    if out_domain:
        pillars.append("DOMAIN")
        vector_count += 1

    if vector_count > 1:
        pillars.append("FUSION")

    # Determine Target Type
    if vector_count > 1:
        target_type = "COMPOSITE"
    elif out_phone:
        target_type = "PHONE"
    elif out_email:
        target_type = "EMAIL"
    elif out_domain:
        target_type = "DOMAIN"
    elif out_name:
        target_type = "NAME"
    elif out_username:
        target_type = "USERNAME"
    else:
        target_type = "UNKNOWN"

    # Extract Phone Metadata
    p_e164 = phone_recon.get("e164") if phone_recon else (out_phone if out_phone and out_phone.startswith("+") else None)
    p_digits = phone_recon.get("digits_only") if phone_recon else (re.sub(r'\D', '', out_phone) if out_phone else None)
    p_country = phone_recon.get("country") if phone_recon else out_country
    p_carrier = phone_recon.get("carrier") if phone_recon else None

    # Derive Canonical Storage Keys
    if out_email:
        canonical_email = out_email
    elif p_digits:
        canonical_email = f"phone.{p_digits}@osint.local"
    elif out_username:
        canonical_email = f"{out_username.lower()}@osint.local"
    elif out_name:
        slug = re.sub(r'[^a-zA-Z0-9._-]', '.', out_name.lower()).strip('.')
        canonical_email = f"{slug}@osint.local"
    elif out_domain:
        canonical_email = f"target@{out_domain}"
    else:
        canonical_email = "target@osint.local"

    # Derive Canonical Display Name
    if out_name:
        canonical_display_name = out_name
    elif phone_recon:
        intl_fmt = phone_recon.get("international_format") or p_e164 or out_phone
        carrier_str = f" ({p_carrier}, {p_country})" if p_carrier and p_country else ""
        canonical_display_name = f"Telecom Target {intl_fmt}{carrier_str}"
    elif out_email:
        canonical_display_name = out_email
    elif out_username:
        canonical_display_name = f"@{out_username}"
    else:
        canonical_display_name = raw or "Unknown Target"

    return TargetManifest(
        raw_query=raw,
        email=out_email,
        phone=out_phone,
        phone_e164=p_e164,
        phone_digits=p_digits,
        phone_country=p_country,
        phone_carrier=p_carrier,
        phone_recon=phone_recon,
        name=out_name,
        first_name=first_name,
        last_name=last_name,
        username=out_username,
        city=out_city,
        country=out_country or p_country,
        domain=out_domain,
        target_type=target_type,
        active_pillars=pillars,
        canonical_email=canonical_email,
        canonical_display_name=canonical_display_name
    )
