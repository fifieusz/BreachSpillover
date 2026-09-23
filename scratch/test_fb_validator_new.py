import urllib.parse
import re
from typing import Dict, Any, List, Optional

FB_DISALLOWED_SLUGS = {
    "login", "login.php", "recover", "help", "policies", "sharer", "share", "groups", "pages",
    "settings", "watch", "marketplace", "events", "company_creation", "photo.php", "permalink.php",
    "story.php", "hashtag", "messages", "me", "about", "public", "directory", "places",
    "games", "saved", "fundraisers", "index.php", "checkpoint", "dialog", "plugins", "tr", "ads",
    "business", "careers", "privacy", "terms", "legal", "security", "support", "gaming", "live",
    "reel", "reels", "stories", "share", "sharer.php"
}

def extract_valid_facebook_profile(
    url: str,
    title: str = "",
    snippet: str = "",
    target_name: str = "",
    target_email: str = "",
    known_handles: Optional[List[str]] = None
) -> Optional[Dict[str, str]]:
    if not url or "facebook.com" not in url.lower():
        return None

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return None

    netloc = parsed.netloc.lower()
    if netloc not in ["facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com"]:
        return None

    path = parsed.path.strip("/")
    if not path and not parsed.query:
        return None

    segments = path.split("/") if path else []
    
    # Handle profile.php?id=12345
    profile_id = None
    if path.lower() == "profile.php":
        qs = urllib.parse.parse_qs(parsed.query)
        profile_id = qs.get("id", [None])[0]
        if not profile_id or not profile_id.isdigit():
            return None
        target_slug = f"profile.php?id={profile_id}"
        clean_profile_url = f"https://www.facebook.com/profile.php?id={profile_id}"
    elif segments:
        first_seg = segments[0]
        # Handle /people/First-Last/12345 or /people/First-Last
        if first_seg.lower() == "people" and len(segments) > 1:
            slug = segments[1]
            num_id = segments[2] if len(segments) > 2 else ""
            if num_id and num_id.isdigit():
                clean_profile_url = f"https://www.facebook.com/people/{slug}/{num_id}"
                target_slug = f"{slug}-{num_id}"
            else:
                clean_profile_url = f"https://www.facebook.com/people/{slug}"
                target_slug = slug
        elif first_seg.lower() in FB_DISALLOWED_SLUGS:
            return None
        else:
            target_slug = first_seg
            clean_profile_url = f"https://www.facebook.com/{first_seg}"
    else:
        return None

    # Validate target_slug contains valid characters (allow hyphens, dots, underscores, alphanumeric)
    slug_only = target_slug.split("?")[0]
    if not re.match(r'^[a-zA-Z0-9._-]{3,100}$', slug_only):
        return None

    # Strict target verification if target attributes provided
    if target_name:
        clean_target = target_name.lower().strip()
        name_parts = clean_target.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        combined_text = f"{title} {snippet} {target_slug}".lower()
        local_part = target_email.split("@")[0].lower() if "@" in target_email else ""
        handles = [h.lower().strip() for h in (known_handles or []) if h]
        if local_part:
            handles.append(local_part)

        # 1. Full name match in snippet/title (both first and last name MUST be distinct tokens)
        name_matched = False
        if first_name and last_name and len(first_name) >= 3 and len(last_name) >= 3:
            if re.search(rf'\b{re.escape(first_name)}\b', combined_text) and re.search(rf'\b{re.escape(last_name)}\b', combined_text):
                name_matched = True

        # 2. Slug matches target handle or full name pattern (e.g. jordin-zwaan-10000990... or jordin.zwaan)
        slug_matched = False
        slug_clean = slug_only.replace(".", "").replace("-", "").replace("_", "").lower()
        if any(h.replace(".", "").replace("-", "").lower() in slug_clean for h in handles if len(h) >= 4):
            slug_matched = True
        elif first_name and last_name:
            if first_name in slug_clean and last_name in slug_clean:
                slug_matched = True

        # If neither name nor handle matches, this is a false positive / stranger profile
        if not name_matched and not slug_matched:
            return None

    return {
        "platform": "Facebook",
        "url": clean_profile_url,
        "handle": target_slug,
        "context": f"Public Facebook Profile verified against target identity: '{title or target_slug}'"
    }

# Test cases:
test_cases = [
    ("https://www.facebook.com/Jordin-Zwaan-100009907727146", "Jordin Zwaan", "Jordin Zwaan ; Lives in Wolvega"),
    ("https://www.facebook.com/people/Jordin-Zwaan/100009907727146", "Jordin Zwaan", ""),
    ("https://www.facebook.com/jordin.zwaan", "Jordin Zwaan", ""),
    ("https://www.facebook.com/profile.php?id=100009907727146", "Jordin Zwaan", "Jordin Zwaan"),
    ("https://www.facebook.com/public/Jordan-van-der-Zwaan/", "Jordin Zwaan", ""), # Should be REJECTED (disallowed slug / name mismatch)
    ("https://www.facebook.com/Zwaan91/", "Jordin Zwaan", "Zwaan"), # Should be REJECTED (no Jordin)
    ("https://www.facebook.com/joris.zwaan/", "Jordin Zwaan", "Joris Zwaan"), # Should be REJECTED (Joris != Jordin)
]

for url, name, ctx in test_cases:
    res = extract_valid_facebook_profile(url, title=ctx, target_name=name)
    print(f"URL: {url}")
    print(f"  -> Validated: {res is not None} | {res['url'] if res else 'REJECTED'}")
