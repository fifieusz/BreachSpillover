import sys, os
sys.path.insert(0, os.path.abspath("."))

from backend.database import get_connection, get_employee_pivots
from backend.main import search_exposure

print("=== Running full scan for: 3gbxdd@gmail.com (Amir Secic) ===")
res = search_exposure(
    email="3gbxdd@gmail.com",
    known_name="Amir Secic",
    refresh=True,
    audit_mode=True
)

emp = res.get("employee", {})
print(f"Target Full Name: {emp.get('full_name')}")
print(f"Target Email:     {emp.get('corporate_email')}")
print(f"Spillover Score:  {res.get('spillover_score', {}).get('score')}")

conn = get_connection()
pivots = get_employee_pivots(emp.get("id"))
conn.close()

print(f"\nTotal Pivots Found: {len(pivots)}")
verified_pivots = [p for p in pivots if "[STATUS: VERIFIED]" in (p.get("context_note") or "")]
suspected_pivots = [p for p in pivots if "[STATUS: CANDIDATE]" in (p.get("context_note") or "")]

print(f"\n--- Verified Pivots ({len(verified_pivots)}) ---")
for p in verified_pivots:
    print(f"  [{p.get('pivot_type')}] {p.get('pivot_value')} (Conf: {p.get('confidence_score')})")
    print(f"     Note: {p.get('context_note')[:100]}")

print(f"\n--- Suspected Candidate Pivots ({len(suspected_pivots)}) ---")
for p in suspected_pivots[:5]:
    print(f"  [{p.get('pivot_type')}] {p.get('pivot_value')} (Conf: {p.get('confidence_score')})")

# Assert that no stranger accounts appear in verified pivots
strangers = ["carlos steve garcia", "afan secic", "gbx due diligence"]
bad_hits = []
for p in verified_pivots:
    v_low = (p.get("pivot_value") or "").lower()
    c_low = (p.get("context_note") or "").lower()
    for s in strangers:
        if s in v_low or s in c_low:
            bad_hits.append((s, p))

print(f"\nFalse-Positive Stranger Check in Verified Pivots: {len(bad_hits)} found.")
if bad_hits:
    print("FAILED! Stranger accounts found in verified pivots:", bad_hits)
else:
    print("SUCCESS! Zero false-positive stranger accounts in verified pivots.")
