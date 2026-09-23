import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_jordin_live():
    print("[*] Testing jordinzwaan2016@gmail.com live verification...")
    resp = client.get("/api/search?email=jordinzwaan2016@gmail.com&audit_mode=true")
    assert resp.status_code == 200, f"Status: {resp.status_code}"
    data = resp.json()
    
    emp = data.get("employee", {})
    full_name = emp.get("full_name")
    print(f"[*] Deduced Employee Name: {full_name}")
    assert full_name == "Jordin Zwaan", f"Expected 'Jordin Zwaan', got '{full_name}'"
    
    pivots = data.get("pivots", [])
    pivot_vals = [p.get("pivot_value") for p in pivots]
    print(f"[*] Total Pivots: {len(pivots)}")
    has_full_name_pivot = any("Jordin Zwaan" in str(pv) for pv in pivot_vals)
    print(f"[*] Has Full Name Pivot: {has_full_name_pivot}")
    assert has_full_name_pivot, "Expected Full Name: Jordin Zwaan pivot"

    dorks = data.get("osint_dorks", [])
    print(f"[*] Total OSINT Dorks: {len(dorks)}")
    dork_titles = [d.get("title") for d in dorks]
    linkedin_dorks = [t for t in dork_titles if "LinkedIn" in t and "Jordin Zwaan" in t]
    images_dorks = [t for t in dork_titles if "Images Face Recon" in t and "Jordin Zwaan" in t]
    no1881_dorks = [t for t in dork_titles if "1881.no" in t]
    print(f"[*] LinkedIn Dork Found: {bool(linkedin_dorks)} -> {linkedin_dorks}")
    print(f"[*] Images Dork Found: {bool(images_dorks)} -> {images_dorks}")
    print(f"[*] 1881.no Dork Found: {bool(no1881_dorks)} -> {no1881_dorks}")
    assert linkedin_dorks, "Expected LinkedIn dork with deduced name"
    assert images_dorks, "Expected Images face recon dork with deduced name"

    # Check graph central node
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    central_node = next((n for n in nodes if n.get("id") == f"emp_{emp['id']}"), None)
    assert central_node is not None, "Central identity node not found"
    print(f"[*] Central Node Label:\n{central_node.get('label')}")
    assert "Jordin Zwaan" in central_node.get("label"), "Expected 'Jordin Zwaan' on central node label"

    print("[+] All verification checks for Jordin Zwaan passed successfully!")

if __name__ == "__main__":
    test_jordin_live()
