import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_filip_norway_lookup():
    print("[*] Testing filipos123.91@gmail.com with anchor known_city='Sarpsborg'...")
    resp = client.get("/api/search?email=filipos123.91@gmail.com&audit_mode=true&known_city=Sarpsborg")
    assert resp.status_code == 200, f"Status: {resp.status_code}"
    data = resp.json()
    
    emp = data.get("employee", {})
    print(f"[*] Employee: {emp.get('full_name')} ({emp.get('corporate_email')})")
    
    dorks = data.get("osint_dorks", [])
    print(f"[*] Total Dorks: {len(dorks)}")
    dork_titles = [d.get("title") for d in dorks]
    print(f"[*] Sample Dorks: {dork_titles[:6]}")
    has_1881 = any("1881" in t for t in dork_titles)
    print(f"[*] Has 1881 Dork: {has_1881}")
    
    print("[+] Norway directory and dorking check complete.")

if __name__ == "__main__":
    test_filip_norway_lookup()
