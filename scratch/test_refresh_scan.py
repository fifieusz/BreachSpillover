import sys
sys.path.insert(0, '.')
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
print("Querying /api/search?email=jordinzwaan2016@gmail.com&refresh=true ...")
resp = client.get('/api/search?email=jordinzwaan2016@gmail.com&refresh=true')
data = resp.json()
print("Pivots count:", len(data.get("pivots", [])))
for p in data.get("pivots", []):
    val = p.get("pivot_value", "")
    val_low = val.lower()
    if any(k in val_low for k in ["steam", "portfolio", "sazeku"]):
        print(f"[{p.get('pivot_type')}] {val} | Conf: {p.get('confidence_score')} | Context: {(p.get('context_note') or '')[:90]}")
