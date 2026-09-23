import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.live_osint import (
    extract_candidate_aliases_from_profile,
    corroborate_candidate_profile,
    check_platform_footprint
)

# 1. Test profile alias extraction
mock_steam_profile = {
    'platform': 'Steam',
    'handle': 'sazeku',
    'persona_name': 'Poes',
    'custom_url': 'sazeku',
    'bio': 'Follow me on twitter: @sazekugamer or discord: sazeku#1234. Also check https://twitch.tv/sazekulive',
    'real_name': '(SELL) SHORT | LONG (BUY)'
}

aliases = extract_candidate_aliases_from_profile(mock_steam_profile, known_handles={'sazeku', 'sazeku123'})
print('Extracted aliases:', [a['alias'] for a in aliases])
assert any(a['alias'] == 'Poes' for a in aliases), 'Failed to extract Poes'
assert any(a['alias'] == 'sazekugamer' for a in aliases), 'Failed to extract sazekugamer'
assert any(a['alias'] == 'sazekulive' for a in aliases), 'Failed to extract sazekulive'

# 2. Test corroboration for vanity URL match
truth_corpus = {
    "names": {"jordin", "zwaan"},
    "locations": {"netherlands"},
    "countries": {"NL"}
}
is_verified, score, reason, is_match = corroborate_candidate_profile(
    mock_steam_profile, 
    truth_corpus, 
    provenance="authenticated_stem"
)
print('Steam Corroboration:', is_verified, score, reason)
assert is_verified is True, 'Steam vanity match should be verified!'
assert score >= 0.85, 'Confidence should be >= 0.85'

# 3. Test check_platform_footprint for steam live probe
footprint = check_platform_footprint('sazeku')
steam_match = next((p for p in footprint if p['platform'] == 'Steam'), None)
print('Steam Footprint Result Platform:', steam_match['platform'])
print('Steam Persona:', steam_match.get('persona_name'))
assert steam_match is not None, 'Steam profile should be returned for sazeku'
assert steam_match.get('persona_name') == 'Poes', f'Expected persona Poes, got {steam_match.get("persona_name")}'

print('\n[+] ALL RECURSIVE ALIAS HARVESTING & STEAM LIVE PROBE TESTS PASSED!')
