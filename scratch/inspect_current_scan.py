from backend.main import app
from fastapi.testclient import TestClient
import json

client = TestClient(app)
resp = client.get('/api/search?email=jordinzwaan2016@gmail.com&audit_mode=true')
data = resp.json()
print('Total pivots:', len(data.get('pivots', [])))
for p in data.get('pivots', []):
    val = p.get('pivot_value', '')
    ptype = p.get('pivot_type', '')
    conf = p.get('confidence_score')
    ctx = (p.get('context_note') or '')[:100]
    print(f"[{ptype}] {val} | Conf: {conf} | Context: {ctx}")

print('\nDiscovered Profiles:')
for dp in data.get('discovered_profiles', []):
    print(dp)

print('\nSuspected Profiles:')
for sp in data.get('suspected_profiles', []):
    print(sp)
