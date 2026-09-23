import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import parse_name_from_email, get_or_create_identity_profile
from backend.live_osint import derive_full_names
from backend.web_dork_recon import execute_ai_dork_recon

client = TestClient(app)

def test_name_splitting():
    print("[*] Testing Compound Given-Name Splitting...")
    n1 = parse_name_from_email("jordinzwaan2016@gmail.com")
    print(f"  jordinzwaan2016 -> {n1}")
    assert n1 == "Jordin Zwaan", f"Expected 'Jordin Zwaan', got '{n1}'"

    n2 = parse_name_from_email("alexmorgan@cybercorp.io")
    print(f"  alexmorgan -> {n2}")
    assert n2 == "Alex Morgan", f"Expected 'Alex Morgan', got '{n2}'"

    d1 = derive_full_names("jordinzwaan2016@gmail.com", set())
    print(f"  derive_full_names -> {d1}")
    assert "Jordin Zwaan" in d1, f"Expected 'Jordin Zwaan' in {d1}"
    print("[+] Name splitting tests passed.")

def test_ai_dork_recon():
    print("\n[*] Testing AI-Assisted Web Dork Reconnaissance...")
    intel = execute_ai_dork_recon("Jordin Zwaan", "jordinzwaan2016@gmail.com")
    print(f"  Corroborated: {intel.get('is_corroborated')}")
    print(f"  Location: {intel.get('location')}")
    print(f"  Workplace: {intel.get('workplace')}")
    print(f"  Profiles: {len(intel.get('profiles', []))}")
    assert intel.get("is_corroborated") is True, "Expected target to be corroborated"
    assert intel.get("location") is not None, "Expected location to be identified"
    loc_str = str(intel.get("location", {})).lower()
    assert "netherland" in loc_str or "amsterdam" in loc_str, f"Expected Netherlands in location, got {intel.get('location')}"
    print("[+] AI Web Dork Recon tests passed.")

def test_api_friend_search():
    print("\n[*] Testing /api/search for friend (jordinzwaan2016@gmail.com)...")
    resp = client.get("/api/search?email=jordinzwaan2016@gmail.com&audit_mode=true")
    assert resp.status_code == 200
    data = resp.json()

    emp = data.get("employee", {})
    print(f"  Full Name: {emp.get('full_name')}")
    print(f"  Job Title: {emp.get('job_title')}")
    print(f"  Department: {emp.get('department')}")
    assert emp.get("full_name") == "Jordin Zwaan"

    footprints = data.get("physical_footprints", [])
    print(f"  Physical Footprints Count: {len(footprints)}")
    assert len(footprints) >= 1, "Expected location footprint to be present from OSINT recon"
    print(f"  Discovered Location: {footprints[0].get('city')}, {footprints[0].get('country')}")

    pivots = data.get("pivots", [])
    has_social_pivot = any(p.get("pivot_type") in ("WORKPLACE", "PUBLIC_PROFILE") for p in pivots)
    print(f"  Has Social / OSINT Pivot: {has_social_pivot}")
    assert has_social_pivot
    print("[+] Friend identity enriched with location, workplace, and social pivots successfully!")

def test_api_clean_search():
    print("\n[*] Testing /api/search for clean uncompromised email...")
    resp = client.get("/api/search?email=authenticated.clean.testuser99@cybercorp.io&audit_mode=true")
    assert resp.status_code == 200
    data = resp.json()
    score = data.get("spillover_score", {}).get("score")
    print(f"  Spillover Score: {score}")
    assert score == 0, f"Expected 0 score, got {score}"
    assert len(data.get("credentials", [])) == 0
    assert len(data.get("physical_footprints", [])) == 0
    print("[+] Clean target returned 0 score cleanly.")

if __name__ == "__main__":
    test_name_splitting()
    test_ai_dork_recon()
    test_api_clean_search()
    test_api_friend_search()
    print("\n=======================================================")
    print("ALL VERIFICATION SUITES PASSED FLAWLESSLY!")
    print("=======================================================")
