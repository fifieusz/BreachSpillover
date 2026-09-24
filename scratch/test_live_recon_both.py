import sys
import os

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, ".")

from backend.main import search_exposure

def run_test_scan(email: str):
    print(f"\n=======================================================")
    print(f"=== TESTING OSINT SEARCH ENGINE FOR: {email} ===")
    print(f"=======================================================")
    
    # Run full search exposure endpoint with refresh=True to force fresh scan
    res = search_exposure(email=email, audit_mode=True, refresh=True)
    emp = res.get("employee", {})
    sc = res.get("spillover_score", {})
    footprints = res.get("physical_footprints", [])
    pivots = res.get("pivots", [])
    
    print(f"\n[+] Employee Profile in Response:")
    print(f"    ID: {emp.get('id')}")
    print(f"    Email: {emp.get('corporate_email')}")
    print(f"    Full Name: {emp.get('full_name')}")
    print(f"    Job / Dept: {emp.get('job_title')} | {emp.get('department')}")
    print(f"    Spillover Score: {sc.get('score')} ({sc.get('numeric_score')})")
    
    print(f"\n[+] Physical Footprints ({len(footprints)}):")
    for f in footprints:
        print(f"    -> {f.get('address_line')} ({f.get('city')}, {f.get('country')}) [Coords: {f.get('latitude')}, {f.get('longitude')}]")
        
    print(f"\n[+] Discovered Pivots ({len(pivots)}):")
    for p in pivots:
        ptype = p.get('pivot_type')
        val = str(p.get('pivot_value', '')).encode('ascii', 'replace').decode('ascii')
        ctx = str(p.get('context_note', '') or '')[:85].encode('ascii', 'replace').decode('ascii')
        print(f"    [{ptype}] {val}")
        print(f"        -> {ctx}")

if __name__ == "__main__":
    run_test_scan("sjoerdsikkema79@gmail.com")
    run_test_scan("xmister795@gmail.com")
