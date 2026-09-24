import sys
import os
import json
import re

# Ensure UTF-8 output encoding on Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, ".")

from backend.ai_engine import (
    call_groq_api,
    generate_ai_threat_dossier,
    resolve_api_key,
    GROQ_DEFAULT_MODEL
)
from backend.main import search_exposure

def test_ai_dossier():
    print("\n--- 1. TESTING AI THREAT DOSSIER GENERATION ---")
    key = resolve_api_key("groq")
    print(f"[*] Resolved Groq API Key: {'Present (' + key[:6] + '...)' if key else 'None'}")
    print(f"[*] Default model: {GROQ_DEFAULT_MODEL}")
    
    # Test a direct quick Groq call
    res = call_groq_api("Say 'Inference Operational' and nothing else.", "System test", key, max_tokens=20)
    print(f"[*] Direct Groq probe response: success={res.get('success')}, model={res.get('model')}, latency={res.get('latency_seconds')}s")
    if not res.get("success"):
        print(f"[!] Direct Groq error: {res.get('error')}")
    else:
        print(f"[*] Text: {res.get('text', '').strip()}")

    # Test full threat dossier generation on sample scan data
    sample_scan = {
        "employee": {
            "id": 999,
            "corporate_email": "test_target@example.com",
            "full_name": "Alex Mercer",
            "department": "Security Architecture"
        },
        "leaks": [
            {
                "service_name": "Canva",
                "breach_date": "2020-05-01",
                "exposed_fields": "email, password_hash, username"
            }
        ],
        "pivots": [
            {
                "pivot_type": "PUBLIC_PROFILE",
                "pivot_value": "GitHub: @alexmercer",
                "confidence_score": 0.95
            },
            {
                "pivot_type": "ACCOUNT_REGISTRATION",
                "pivot_value": "Pinterest: Registered Account",
                "confidence_score": 0.98
            }
        ],
        "passwords": ["Winter2020!"]
    }
    
    dossier = generate_ai_threat_dossier(sample_scan, api_key=key, force_refresh=True)
    print(f"[*] Threat Dossier Generated:")
    print(f"    - is_ai_generated: {dossier.get('is_ai_generated')}")
    print(f"    - provider: {dossier.get('provider')}")
    print(f"    - model: {dossier.get('model')}")
    print(f"    - notice: {dossier.get('notice')}")
    print(f"    - engine_label: {dossier.get('engine_label')}")
    print(f"    - verdict: {dossier.get('threat_level_verdict')}")
    summary_prev = str(dossier.get('executive_summary', ''))[:120].strip()
    print(f"    - executive_summary: {summary_prev}...")
    
    # Assert no emojis in dossier text
    raw_dossier_str = json.dumps(dossier)
    emoji_matches = re.findall(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50-\u2b55\u203c-\u3299]', raw_dossier_str)
    print(f"[*] Emojis in dossier: {len(emoji_matches)} ({emoji_matches})")
    assert len(emoji_matches) == 0, f"Found emojis: {emoji_matches}"
    assert "executive_summary" in dossier
    assert "threat_level_verdict" in dossier
    print("[+] AI Threat Dossier test PASSED successfully!")

def test_full_pipeline_synergy():
    print("\n--- 2. TESTING FULL PIPELINE & COMPONENT SYNERGY ---")
    email = "3gbxdd@gmail.com"
    print(f"[*] Running live search_exposure on: {email}")
    res = search_exposure(email=email, audit_mode=True, refresh=True)
    
    emp = res.get("employee", {})
    pivots = res.get("pivots", [])
    print(f"[+] Scanned Employee: {emp.get('full_name')} ({emp.get('corporate_email')})")
    print(f"[+] Total Pivots: {len(pivots)}")
    
    # Verify presence of user-scanner verified services
    verified_services = [p for p in pivots if "EMAIL VERIFIED" in str(p.get("context_note", ""))]
    print(f"[+] Verified Email-Bound Accounts ({len(verified_services)}):")
    for vs in verified_services:
        print(f"    -> {vs.get('pivot_value')} (Confidence: {vs.get('confidence_score')})")
        
    # Verify avatar correlations
    avatars = [p for p in pivots if p.get("pivot_type") == "AVATAR_CORRELATION"]
    print(f"[+] Discovered Avatars ({len(avatars)}):")
    for av in avatars:
        print(f"    -> {av.get('pivot_value')}")
        
    # Verify zero emojis across full response
    full_json = json.dumps(res)
    emoji_matches = re.findall(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50-\u2b55\u203c-\u3299]', full_json)
    print(f"[*] Total emojis across entire API response: {len(emoji_matches)}")
    assert len(emoji_matches) == 0, f"Found emojis in API response: {emoji_matches}"
    print("[+] Component synergy test PASSED successfully!")

if __name__ == "__main__":
    test_ai_dossier()
    test_full_pipeline_synergy()
