"""
BreachSpillover - Generic Identity Signal Primitives

Pure, deterministic, target-agnostic helpers shared by the AI Cardinal arbiter
(`backend/ai_cardinal.py`) and the entity resolution clustering engine
(`backend/entity_resolution.py`).

Design rules:
- ZERO hardcoded target names, usernames, emails, or keyword blacklists.
- Every decision is derived from the target's own anchors (legal name tokens,
  email localpart, authenticated handles) or from universal linguistic markers
  (explicit pronoun declarations).
- Visual media detection is structural (pivot type / image URL shape), never a
  guess about the person behind the account.
"""

import math
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

_EMOJI_RE = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50-\u2b55\u203c-\u3299]')

# Data-hygiene sentinels emitted by scrapers / APIs when a field is empty.
# These are NOT identity blacklists: they are literal "no value" markers.
NULL_SENTINELS = frozenset({"", "none", "null", "nil", "undefined", "unknown", "nan", "n/a", "na"})


def strip_symbols(val: Any) -> str:
    """Strips emojis and non-printable surrogate characters."""
    if not val:
        return ""
    return _EMOJI_RE.sub("", str(val)).strip()


def ascii_fold(val: Any) -> str:
    """Folds accents/diacritics to ASCII and lowercases (e.g. 'Jürgen' -> 'jurgen')."""
    if not val:
        return ""
    decomposed = unicodedata.normalize("NFKD", strip_symbols(val))
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def name_tokens(name: Any) -> List[str]:
    """Returns ordered, normalised alphabetic tokens (len >= 2) of a human name."""
    return [t for t in re.findall(r"[a-z]+", ascii_fold(name)) if len(t) >= 2]


def split_given_family(name: Any) -> Tuple[str, str]:
    """Splits a name into (given, family). Family is empty for mononyms."""
    toks = name_tokens(name)
    if not toks:
        return "", ""
    if len(toks) == 1:
        return toks[0], ""
    return toks[0], toks[-1]


DOMAIN_TLDS = frozenset({
    "com", "org", "net", "io", "nl", "de", "uk", "fr", "pl", "no", "se", "be",
    "eu", "edu", "gov", "mil", "co", "info", "online", "xyz", "app", "dev",
    "me", "ai", "tv", "cc", "ru", "cn", "jp", "local", "lan", "site", "live", "store"
})


def is_domain_or_url(val: Any) -> bool:
    """Detects whether a token is a web domain, hostname, or URL rather than a human handle."""
    if not val:
        return False
    s = str(val).strip().lower().lstrip("@")
    if s.startswith(("http://", "https://", "ftp://", "www.")):
        return True
    domain_part = s.split("/")[0].split("?")[0]
    if "." in domain_part:
        parts = domain_part.split(".")
        if parts[-1] in DOMAIN_TLDS:
            return True
        if len(parts) >= 3 and any(p in DOMAIN_TLDS for p in parts):
            return True
    return False


def normalize_handle(handle: Any) -> str:
    """Canonical handle form: no '@', lowercase, no URL path, trimmed separators."""
    if not handle:
        return ""
    raw = str(handle).strip()
    if is_domain_or_url(raw):
        if "/" in raw:
            path_part = raw.split("?")[0].rstrip("/").rsplit("/", 1)[-1]
            if path_part and not is_domain_or_url(path_part):
                h = ascii_fold(path_part).strip().lstrip("@").strip()
                return h.strip(" .-_+")
        return ""
    h = ascii_fold(raw).strip().lstrip("@").strip()
    h = h.split("?")[0].rstrip("/")
    if "/" in h:
        h = h.rsplit("/", 1)[-1]
    h = h.lstrip("@")
    cleaned = h.strip(" .-_+")
    if is_domain_or_url(cleaned):
        return ""
    return cleaned



def handle_stem(handle: Any) -> str:
    """Handle with trailing digits removed (original kept if the stem collapses below 3 chars)."""
    h = normalize_handle(handle)
    stem = re.sub(r"\d+$", "", h).strip(" .-_+")
    return stem if len(stem) >= 3 else h


def squash(handle: Any) -> str:
    """Letters-only projection of a handle ('j.doe_99' -> 'jdoe')."""
    return re.sub(r"[^a-z]", "", ascii_fold(handle))


def is_null_value(val: Any) -> bool:
    return ascii_fold(val).strip() in NULL_SENTINELS


def shannon_entropy(val: str) -> float:
    if not val:
        return 0.0
    probs = [float(val.count(c)) / len(val) for c in dict.fromkeys(val)]
    return -sum(p * math.log2(p) for p in probs)

# ---------------------------------------------------------------------------
# Name compatibility & namesake detection
# ---------------------------------------------------------------------------

def given_names_compatible(a: str, b: str) -> bool:
    """
    True when two given names can denote the same person: identical, an initial,
    or a prefix diminutive (e.g. 'alex' / 'alexander'). Purely structural.
    """
    a, b = ascii_fold(a).strip("."), ascii_fold(b).strip(".")
    if not a or not b:
        return True
    if a == b:
        return True
    if len(a) == 1 or len(b) == 1:
        return a[0] == b[0]
    return a.startswith(b) or b.startswith(a)


def detect_given_name_conflict(target_name: Any, candidate_name: Any) -> Optional[str]:
    """
    Returns the candidate's conflicting given name when the candidate shares the
    target's family name but carries an incompatible given name. None otherwise.
    """
    t_given, t_family = split_given_family(target_name)
    c_given, c_family = split_given_family(candidate_name)
    if not (t_given and t_family and c_given and c_family):
        return None
    if c_family != t_family:
        return None
    if given_names_compatible(t_given, c_given):
        return None
    return c_given


def _slug_tokens(url: str) -> List[str]:
    slug = (url or "").strip().lower().split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    slug = slug.lstrip("@")
    toks = [t for t in re.split(r"[-_.]+", ascii_fold(slug)) if t]
    # Drop trailing disambiguation suffixes that platforms append (ids, digits, hashes)
    while toks and re.search(r"\d", toks[-1]):
        toks.pop()
    return toks


def detect_slug_given_conflict(target_name: Any, url: Any) -> Optional[str]:
    """
    Detects vanity-slug namesakes such as '/in/<other-given>-<target-family>'.
    Returns the conflicting given-name token, or None.
    """
    t_given, t_family = split_given_family(target_name)
    if not (t_given and t_family and url):
        return None
    toks = _slug_tokens(str(url))
    if len(toks) < 2 or toks[-1] != t_family:
        return None
    first = toks[0]
    if len(first) < 3 or given_names_compatible(t_given, first):
        return None
    return first


# ---------------------------------------------------------------------------
# Demographic (pronoun) signals
# ---------------------------------------------------------------------------

# Explicit pronoun self-declarations. `\b` prevents 'he/' matching inside 'she/'.
_FEMALE_PRONOUN_RE = re.compile(r"\b(?:she\s*/\s*(?:her|hers|they|them)|her\s*/\s*she)\b")
_MALE_PRONOUN_RE = re.compile(r"\b(?:he\s*/\s*(?:him|his|they|them)|him\s*/\s*he)\b")
# Gendered self-descriptors (universal English role nouns, word-bounded).
_FEMALE_DESCRIPTOR_RE = re.compile(r"\b(?:woman|actress|mother|wife|girl|mom|mum|daughter|sister|grandmother)\b")
_MALE_DESCRIPTOR_RE = re.compile(r"\b(?:man|actor|father|husband|guy|boy|dad|son|brother|grandfather)\b")


def detect_declared_gender(text: Any, include_descriptors: bool = True) -> Optional[str]:
    """
    Returns 'male' / 'female' when the text unambiguously declares a gender,
    None when absent or contradictory. Explicit pronouns outrank descriptors.
    """
    blob = ascii_fold(text)
    if not blob:
        return None
    fem_p = bool(_FEMALE_PRONOUN_RE.search(blob))
    male_p = bool(_MALE_PRONOUN_RE.search(blob))
    if fem_p != male_p:
        return "female" if fem_p else "male"
    if fem_p and male_p:
        return None
    if not include_descriptors:
        return None
    fem_d = bool(_FEMALE_DESCRIPTOR_RE.search(blob))
    male_d = bool(_MALE_DESCRIPTOR_RE.search(blob))
    if fem_d != male_d:
        return "female" if fem_d else "male"
    return None


def normalize_gender(val: Any) -> str:
    g = ascii_fold(val).strip()
    if g in ("male", "m", "man", "he/him"):
        return "male"
    if g in ("female", "f", "woman", "she/her"):
        return "female"
    return "unknown"


def detect_demographic_contradiction(target_gender: Any, candidate_text: Any) -> Optional[str]:
    """Returns a human-readable contradiction reason, or None."""
    tg = normalize_gender(target_gender)
    if tg == "unknown":
        return None
    cg = detect_declared_gender(candidate_text, include_descriptors=True)
    if not cg or cg == tg:
        return None
    declared = "she/her" if cg == "female" else "he/him"
    return f"profile bio states '{declared}' conflicting with {tg} target identity"

# ---------------------------------------------------------------------------
# Target anchors & handle classification
# ---------------------------------------------------------------------------

HANDLE_PRIMARY_NAME = "PRIMARY_NAME"          # full-name or email-localpart form
HANDLE_NAME_PERMUTATION = "NAME_PERMUTATION"  # initial+surname style guess
HANDLE_BARE_SURNAME = "BARE_SURNAME"
HANDLE_BARE_GIVEN = "BARE_GIVEN"
HANDLE_ALIAS = "ALIAS"                        # not derived from the legal name
HANDLE_EMPTY = "EMPTY"


def email_localpart(email: Any) -> str:
    e = ascii_fold(email).strip()
    if "@" not in e:
        return ""
    return e.split("@", 1)[0].split("+", 1)[0]


def build_target_anchors(full_name: Any = "", email: Any = "") -> Dict[str, Any]:
    """
    Derives the target's primary stems strictly from the legal given/family
    name and the email localpart. No other source may define the core identity.
    """
    given, family = split_given_family(full_name)
    local = email_localpart(email)
    local_sq = squash(local)

    primary_forms: Set[str] = set()
    permutation_forms: Set[str] = set()
    if given and family:
        primary_forms.update({given + family, family + given})
        permutation_forms.update({given[0] + family, given + family[0], family + given[0], family + given[0:1]})
    if local_sq and len(local_sq) >= 3:
        primary_forms.add(local_sq)
    permutation_forms -= primary_forms

    stems: Set[str] = {s for s in (given, family) if s}
    if given and family:
        stems.update({given + family, f"{given}_{family}", f"{given}.{family}", f"{given}-{family}"})
    if local:
        stems.add(local)
        stems.add(handle_stem(local))
        if local_sq:
            stems.add(local_sq)

    return {
        "full_name": strip_symbols(full_name),
        "given": given,
        "family": family,
        "email_local": local,
        "primary_forms": primary_forms,
        "permutation_forms": permutation_forms,
        "primary_stems": {s for s in stems if s},
    }


def classify_handle(handle: Any, anchors: Dict[str, Any]) -> str:
    """Classifies a handle relative to the target's legal-name anchors."""
    sq = squash(handle)
    if not sq or is_null_value(handle):
        return HANDLE_EMPTY
    given, family = anchors.get("given", ""), anchors.get("family", "")
    if sq in anchors.get("primary_forms", set()):
        return HANDLE_PRIMARY_NAME
    if sq in anchors.get("permutation_forms", set()):
        return HANDLE_NAME_PERMUTATION
    if family and sq == family:
        return HANDLE_BARE_SURNAME
    if given and sq == given:
        return HANDLE_BARE_GIVEN
    return HANDLE_ALIAS


def is_name_derived_handle(handle: Any, anchors: Dict[str, Any]) -> bool:
    return classify_handle(handle, anchors) not in (HANDLE_ALIAS, HANDLE_EMPTY)

# ---------------------------------------------------------------------------
# Visual media segregation (structural detection)
# ---------------------------------------------------------------------------

MEDIA_PIVOT_TYPES = frozenset({"AVATAR_CORRELATION", "VISUAL_ASSET", "MEDIA_ASSET", "IMAGE_ASSET"})
MEDIA_CONTEXT_MARKERS = (
    "[status: secondary avatar]",
    "[status: primary avatar]",
    "[tied: primary face]",
    "[classification: real_human_portrait]",
    "[classification: website_banner_or_asset]",
    "[classification: cartoon_or_avatar]",
)
IMAGE_EXT_RE = re.compile(r"\.(?:jpe?g|png|gif|webp|avif|bmp|heic)(?:[?#]|$)", re.IGNORECASE)
# Image-serving CDN path shapes (infrastructure, not identities).
IMAGE_CDN_RE = re.compile(
    r"(?:/dms/image/|fbcdn\.net/|pbs\.twimg\.com/|avatars\.githubusercontent\.com/|gravatar\.com/avatar/"
    r"|i\.pinimg\.com/|cdninstagram\.com/|googleusercontent\.com/|ytimg\.com/|ggpht\.com/|steamstatic\.com/)",
    re.IGNORECASE,
)

URL_IN_TAG_RE = re.compile(r"\[URL:\s*(https?://[^\s\]]+)\]")
ANY_URL_RE = re.compile(r"(https?://[^\s\]\)'\"]+)")


def looks_like_image_url(url: Any) -> bool:
    u = str(url or "").strip()
    if not u.lower().startswith("http"):
        return False
    return bool(IMAGE_EXT_RE.search(u) or IMAGE_CDN_RE.search(u))


def extract_tagged_url(text: Any) -> str:
    m = URL_IN_TAG_RE.search(str(text or ""))
    return m.group(1).strip() if m else ""


def is_visual_media_pivot(pivot: Dict[str, Any]) -> bool:
    """
    A pivot is a visual media asset (avatar, banner, album photo) when its type
    is a media type, it carries a media classification tag, or its value is an
    image URL. Such pivots belong only to the media gallery, never to persona
    candidate ledgers.
    """
    if not isinstance(pivot, dict):
        return False
    pt = str(pivot.get("pivot_type") or "").upper()
    if pt in MEDIA_PIVOT_TYPES:
        return True
    pv = str(pivot.get("pivot_value") or "")
    pv_low = pv.lower()
    if "visual footprint" in pv_low:
        return True
    ctx_low = str(pivot.get("context_note") or "").lower()
    if any(m in ctx_low for m in MEDIA_CONTEXT_MARKERS):
        return True
    value_part = pv.split(":", 1)[1].strip() if ":" in pv and not pv_low.startswith("http") else pv
    return looks_like_image_url(value_part)


def is_visual_media_profile(profile: Dict[str, Any]) -> bool:
    """A 'profile' whose URL is an image asset is media, not an account."""
    if not isinstance(profile, dict):
        return False
    if str(profile.get("pivot_type") or "").upper() in MEDIA_PIVOT_TYPES:
        return True
    url = profile.get("url") or profile.get("profile_url") or ""
    return looks_like_image_url(url)

# ---------------------------------------------------------------------------
# Pivot parsing, binding evidence & alias mentions
# ---------------------------------------------------------------------------

PERSONA_ATTR_RE = re.compile(r"persona:\s*'([^']+)'", re.IGNORECASE)
ALIAS_VALUE_RE = re.compile(r"(?:online nickname|candidate alias|nickname|alias)\s*:\s*@?([a-z0-9_.\-]+)", re.IGNORECASE)

# Phrases the ingestion pipeline writes when an account is cryptographically or
# registration-bound to the target (commit author email, platform email lookup).
EMAIL_BINDING_MARKERS = (
    "exact email", "tied to target email", "registered to target email",
    "email-bound", "email bound", "email verified", "verified_email",
    "[tied: email verified]", "[platform: verified_email]", "registered account verified"
)
AUTH_BINDING_MARKERS = EMAIL_BINDING_MARKERS + (
    "author commit", "authenticated github", "repository owned", "commit-bound",
    "cryptographic proof", "[tied: cryptographic proof]", "[tied: commit proof]",
    "[tied: primary steam]"
)


def has_email_binding(text: Any) -> bool:
    low = str(text or "").lower()
    return any(m in low for m in EMAIL_BINDING_MARKERS)


def has_auth_binding(text: Any) -> bool:
    low = str(text or "").lower()
    return any(m in low for m in AUTH_BINDING_MARKERS)


def parse_pivot_account(pivot_value: Any) -> Tuple[str, str]:
    """Splits 'Platform: @handle (Persona: ...)' into ('Platform', 'handle')."""
    pv = str(pivot_value or "")
    if ":" not in pv:
        return "", normalize_handle(pv.split()[0]) if pv.strip() else ""
    plat, rest = pv.split(":", 1)
    rest = rest.strip()
    first = rest.split()[0] if rest else ""
    return plat.strip(), normalize_handle(first)


def extract_alias_mentions(pivot_value: Any, context_note: Any = "") -> List[str]:
    """
    Extracts explicitly declared alias personas from a pivot: nickname/alias
    declarations and in-game persona attributes ("Persona: 'X'").
    """
    found: List[str] = []
    pv = str(pivot_value or "")
    for rx in (ALIAS_VALUE_RE, PERSONA_ATTR_RE):
        for m in rx.finditer(pv):
            cand = m.group(1)
            if is_domain_or_url(cand):
                continue
            h = normalize_handle(cand)
            if h and h not in found and not is_null_value(h) and not is_domain_or_url(h):
                found.append(h)
    ctx_low = str(context_note or "").lower()
    if not found and "online alias" in ctx_low:
        _, h = parse_pivot_account(pv)
        if h and not is_domain_or_url(h):
            found.append(h)
    return found



def alias_matches_text(alias: str, handle: str, text: str) -> bool:
    """Boundary-aware alias membership test (avoids substring false positives)."""
    if not alias:
        return False
    if handle and (handle == alias or handle_stem(handle) == alias):
        return True
    if len(alias) >= 4 and handle and handle.startswith(alias):
        return True
    low = ascii_fold(text)
    pattern = r"(?<![a-z0-9])@?" + re.escape(alias) + r"(?![a-z])"
    return bool(re.search(pattern, low))


# ---------------------------------------------------------------------------
# Repeat-scan seeding of live scrape targets from persisted pivots
# ---------------------------------------------------------------------------

def canonical_profile_url(url: Any) -> str:
    """Scheme/host/trailing-slash/query-insensitive URL key (numeric `id=` queries are kept)."""
    raw = str(url or "").strip().lower().split("#")[0]
    id_match = re.search(r"[?&](id=\d+)", raw)
    u = raw.split("?")[0].rstrip("/")
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^(?:www\.|m\.|mobile\.|[a-z]{2}\.)", "", u)
    return f"{u}?{id_match.group(1)}" if id_match else u


def rank_seed_profile_urls(
    pivot_rows: List[Any],
    url_pattern: str,
    target_name: Any = "",
    excluded_urls: Optional[List[Any]] = None,
) -> List[str]:
    """
    Extracts previously persisted profile URLs matching `url_pattern` (a regex)
    so live browser scraping is re-seeded consistently on repeat scans.

    `pivot_rows` are (pivot_type, pivot_value, context_note) tuples or pivot
    dicts. Visual media assets, URLs whose vanity slug carries a conflicting
    given name, and URLs the arbiter isolated (`excluded_urls`) are never
    seeded. Ordering: authentication-bound > verified profile > suspected.
    """
    rx = re.compile(url_pattern, re.IGNORECASE)
    excluded = {canonical_profile_url(u) for u in (excluded_urls or []) if u}
    ranked: List[Tuple[int, int, str]] = []
    seen: set = set()
    for idx, row in enumerate(pivot_rows or []):
        if isinstance(row, dict):
            pt, pv, ctx = row.get("pivot_type"), row.get("pivot_value"), row.get("context_note")
        else:
            pt, pv, ctx = (list(row) + [None, None, None])[:3]
        piv = {"pivot_type": pt or "", "pivot_value": pv or "", "context_note": ctx or ""}
        if is_visual_media_pivot(piv):
            continue
        m = rx.search(f"{pv or ''} {ctx or ''}")
        if not m:
            continue
        url = m.group(0).rstrip("/")
        key = canonical_profile_url(url)
        if not key or key in seen or key in excluded or looks_like_image_url(url):
            continue
        if detect_slug_given_conflict(target_name, url):
            continue
        seen.add(key)
        if has_auth_binding(ctx):
            rank = 0
        elif str(pt or "").upper() == "PUBLIC_PROFILE" or "[status: verified]" in str(ctx or "").lower():
            rank = 1
        else:
            rank = 2
        ranked.append((rank, idx, url))
    ranked.sort()
    return [u for _, _, u in ranked]
