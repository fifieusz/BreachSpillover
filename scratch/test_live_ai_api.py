import urllib.request
import json

def test_live_ai_endpoints():
    print("[*] Testing live /api/ai/test-key endpoint...")
    req_probe = urllib.request.Request(
        "http://127.0.0.1:8000/api/ai/test-key",
        data=json.dumps({"api_key": "invalid_test_key_for_probe", "provider": "groq"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_probe, timeout=10) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        print(f"[+] Key probe responded: success={res.get('success')}, error={res.get('error')[:60]}...")

    print("[*] Testing live /api/ai/dossier endpoint with scan_data...")
    dummy_scan_data = {
        "employee": {
            "id": 1,
            "corporate_email": "jordinzwaan2016@gmail.com",
            "full_name": "Jordin Zwaan",
            "department": "Security Research",
            "job_title": "Security Analyst"
        },
        "spillover_score": {
            "overall_score": 68,
            "risk_level": "HIGH"
        },
        "leaks": [{"service_name": "LinkedIn 2021", "year": 2021}],
        "pivots": [{"pivot_type": "HANDLE", "pivot_value": "jordinzwaan"}]
    }

    req_dossier = urllib.request.Request(
        "http://127.0.0.1:8000/api/ai/dossier",
        data=json.dumps({
            "email": "jordinzwaan2016@gmail.com",
            "scan_data": dummy_scan_data
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_dossier, timeout=10) as resp:
        assert resp.status == 200
        dossier = json.loads(resp.read().decode("utf-8"))
        print("[+] Dossier received successfully!")
        print(f"[*] Engine: {dossier.get('engine_label')}")
        print(f"[*] Summary preview: {dossier.get('executive_summary')[:100]}...")
        assert "executive_summary" in dossier
        assert "persona_disambiguation" in dossier

    print("[*] Testing live /api/ai/copilot endpoint...")
    req_cop = urllib.request.Request(
        "http://127.0.0.1:8000/api/ai/copilot",
        data=json.dumps({
            "email": "jordinzwaan2016@gmail.com",
            "scan_data": dummy_scan_data,
            "message": "What is the highest attack vector for this target?"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_cop, timeout=10) as resp:
        assert resp.status == 200
        cop_res = json.loads(resp.read().decode("utf-8"))
        print("[+] Copilot response received successfully!")
        print(f"[*] Copilot reply preview: {cop_res.get('reply')[:100]}...")
        assert cop_res.get("success")

    print("[+] All live AI API endpoint checks passed perfectly!")

if __name__ == "__main__":
    test_live_ai_endpoints()
