import re
import urllib.request
import json

def check_emojis(filepath):
    content = open(filepath, encoding='utf-8').read()
    emojis = re.findall(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff]', content)
    return len(emojis), emojis[:5]

print("=== 1. ZERO EMOJI CHECK ===")
for path in ['frontend/index.html', 'frontend/static/css/style.css', 'frontend/static/js/app.v17.js']:
    count, samples = check_emojis(path)
    print(f"{path}: {count} emojis found {samples if count else '[PASS]'}")
    assert count == 0, f"Found emojis in {path}"

print("\n=== 2. DOM & UI LAYOUT VERIFICATION ===")
resp = urllib.request.urlopen('http://127.0.0.1:8000/')
html = resp.read().decode('utf-8')

# Assertions
assert 'ai-copilot-drawer' in html, "ai-copilot-drawer missing from index.html"
assert 'ai-copilot-floating-btn' in html, "ai-copilot-floating-btn missing"
assert 'copilot-panel-dossier' in html, "copilot-panel-dossier missing"
assert 'copilot-panel-chat' in html, "copilot-panel-chat missing"
assert 'id="severity-badge"' not in html, "Redundant severity-badge should be removed from target headline"
assert 'id="target-workplace-wrap"' not in html, "Workplace wrap should be removed from target email subline"
assert 'id="ai-review-section"' not in html, "Old inline ai-review-section should be removed"
assert 'btn-open-copilot' in html, "Header copilot button missing"

print("All DOM structural assertions passed!")

print("\n=== 3. COPILOT API CHAT ENDPOINT TEST ===")
copilot_payload = json.dumps({
    "message": "What is the highest risk exposure for this target?",
    "email": "filipos123.91@gmail.com",
    "scan_data": {"employee": {"full_name": "Filip Niewiadomski", "corporate_email": "filipos123.91@gmail.com"}, "spillover_score": {"numeric_score": 75, "level": "HIGH"}},
    "history": []
}).encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/ai/copilot',
    data=copilot_payload,
    headers={'Content-Type': 'application/json'}
)
resp_copilot = urllib.request.urlopen(req, timeout=15)
res_data = json.loads(resp_copilot.read().decode('utf-8'))
print("Copilot Status Code:", resp_copilot.status)
reply_text = res_data.get('reply') or res_data.get('response') or str(res_data)
print("Copilot Response Preview:", reply_text[:120], "...")
assert resp_copilot.status == 200, "Copilot API failed"

print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
