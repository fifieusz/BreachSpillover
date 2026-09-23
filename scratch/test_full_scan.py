import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.main import search_exposure
import json

print("[*] Running search_exposure for jordinzwaan2016@gmail.com...")
res = search_exposure(email="jordinzwaan2016@gmail.com", audit_mode=True)

print("\n=== SEARCH EXPOSURE RESULT ===")
print("Employee:", res.get("employee"))

print("\nPhysical Footprints:")
for f in res.get("physical_footprints", []):
    print("  ->", f.get("address_line"), "| City:", f.get("city"), "| Country:", f.get("country"))

print("\nPivots:")
for p in res.get("pivots", []):
    if any(k in p.get("pivot_type", "") for k in ["PROFILE", "WORKPLACE", "EMAIL"]):
        print(f"  [{p.get('pivot_type')}] {p.get('pivot_value')} | {p.get('context_note', '')[:90]}")
