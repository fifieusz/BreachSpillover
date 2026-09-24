import sys, os
sys.path.insert(0, os.path.abspath("."))
import sqlite3
from backend.main import search_exposure

def test_refresh_target(email):
    print(f"\n=======================================================")
    print(f"RUNNING REFRESH SEARCH ON: {email}")
    print(f"=======================================================")
    res = search_exposure(email=email, refresh=True)
    pivots = res.get("pivots", [])
    suspected = res.get("suspected_pivots", [])
    print(f"Target: {res.get('employee', {}).get('full_name')} ({email})")
    print(f"Verified Pivots Count: {len(pivots)}")
    print(f"Suspected Pivots Count: {len(suspected)}")

    print("\n--- Verified Pivots ---")
    for p in pivots:
        ptype = p.get("pivot_type")
        pval = p.get("pivot_value")
        conf = p.get("confidence_score")
        print(f"  [{ptype}] {pval} (conf: {conf})")

    print("\n--- Suspected Pivots (Sample first 8) ---")
    for sp in suspected[:8]:
        ptype = sp.get("pivot_type")
        pval = sp.get("pivot_value")
        conf = sp.get("confidence_score")
        print(f"  [SUSPECTED] {pval} (conf: {conf})")

test_refresh_target("yasir1kadhim@gmail.com")
test_refresh_target("filipos123.91@gmail.com")
