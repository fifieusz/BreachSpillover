import re
from urllib.parse import urlparse

piv_jouwweb = {
    'pivot_type': 'PUBLIC_PROFILE',
    'pivot_value': 'Portfolio: jordinzwaan',
    'context_note': 'Verified personal portfolio with matching name and details [URL: https://jordinzwaan.jouwweb.nl] [STATUS: VERIFIED]'
}
piv_steam = {
    'pivot_type': 'PUBLIC_PROFILE',
    'pivot_value': "Steam: @sazeku (Persona: 'Poes')",
    'context_note': "Active Steam Community gaming profile (SteamID64: 76561198385773342 • Persona: 'Poes') [URL: https://steamcommunity.com/id/sazeku] [STATUS: VERIFIED]"
}

def check_card(piv):
    m = re.search(r'\[URL:\s*(https?://[^\]]+)\]', piv['context_note'])
    url = m.group(1) if m else None
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    pathname = (parsed.path or '').rstrip('/')
    is_user_subdomain = any(s in host for s in ['.jouwweb.nl', '.github.io', '.carrd.co', '.wixsite.com']) or 'portfolio' in piv['pivot_value'].lower()
    is_root_domain = not is_user_subdomain and (not pathname)
    is_presence_only = (piv['pivot_type'] == 'ACCOUNT_REGISTRATION') and (not url or is_root_domain)
    is_steam = 'steam' in piv['pivot_value'].lower()
    tag = 'VERIFIED STEAM PROFILE' if is_steam else ('EMAIL REGISTRATION VERIFIED' if is_presence_only else 'LIVE OSINT PROFILE')
    print(piv['pivot_value'])
    print(f'  URL: {url}')
    print(f'  is_user_subdomain: {is_user_subdomain}')
    print(f'  is_root_domain: {is_root_domain}')
    print(f'  is_presence_only: {is_presence_only}')
    print(f'  Tag: {tag}')
    print(f'  Has "View Verified Profile" button: {not is_presence_only and bool(url)}')

check_card(piv_jouwweb)
check_card(piv_steam)
