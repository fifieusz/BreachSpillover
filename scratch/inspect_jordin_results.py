import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.main import search_exposure

res = search_exposure('jordinzwaan2016@gmail.com', audit_mode=True)
print('=== PIVOTS ===')
for p in res.get('pivots', []):
    print(f"{p.get('pivot_type')}: {p.get('pivot_value')} (conf: {p.get('confidence_score')}) | note: {p.get('context_note')[:60] if p.get('context_note') else ''}")

print('\n=== CANDIDATE_PROFILES ===')
for c in res.get('candidate_profiles', []):
    print(f"{c.get('platform')}: @{c.get('handle')} | conf: {c.get('confidence')} | verified: {c.get('is_verified')} | reason: {c.get('reason')}")

print('\n=== GRAPH NODES ===')
for n in res.get('graph', {}).get('nodes', []):
    data = n.get('data', {})
    if 'Steam' in data.get('label', '') or 'Poes' in data.get('label', '') or 'sazeku' in data.get('label', ''):
        print(f"Node id={data.get('id')} label={data.get('label')} type={data.get('type')}")
