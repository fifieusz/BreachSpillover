import sys
sys.path.insert(0, '.')
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
resp = client.get('/api/search?email=jordinzwaan2016@gmail.com')
data = resp.json()
print("=== VERIFIED TARGET PROFILES ===")
for p in data.get("pivots", []):
    v = p.get("pivot_value", "")
    if any(k in v.lower() for k in ["steam", "portfolio", "sazeku", "jouwweb"]):
        ptype = p.get("pivot_type")
        conf = p.get("confidence_score")
        ctx = (p.get("context_note") or "")[:85]
        print(f"Type: {ptype:<20} | Val: {v:<35} | Conf: {conf} | Ctx: {ctx}")
