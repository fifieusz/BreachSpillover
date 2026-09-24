import urllib.request
import json
import time

resp = urllib.request.urlopen('http://127.0.0.1:8000/')
html = resp.read().decode('utf-8')

print('--- HTML DOM Verification ---', flush=True)
assert 'Breach Spillover' in html, 'Brand title missing'
assert 'brand-shield' not in html, 'Brand shield should be removed'
assert 'brand-subtitle' not in html, 'Brand subtitle should be removed'
assert 'Threat DB:' not in html, 'Threat DB counter should be removed'
assert 'btn-tools-modal' in html, 'Functions button missing'
assert 'cockpit-anchors-grid' in html, 'Upfront anchors grid missing'
assert 'id="anchor-name"' in html, 'anchor-name input missing'
assert 'id="anchor-username"' in html, 'anchor-username input missing'
assert 'id="anchor-phone"' in html, 'anchor-phone input missing'
assert 'id="anchor-city"' in html, 'anchor-city input missing'
assert 'summary-creds-list' in html, 'summary-creds-list missing'
assert 'summary-locations-list' in html, 'summary-locations-list missing'
assert 'summary-phones-list' in html, 'summary-phones-list missing'
assert 'summary-relatives-list' in html, 'summary-relatives-list missing'
assert 'summary-workplace-list' in html, 'summary-workplace-list missing'
assert 'ai-review-section' in html, 'ai-review-section missing'
assert 'tools-modal' in html, 'tools-modal missing'
assert '[VERIFIED PIVOTS]' in html, 'Pivots tab missing'
assert '[SUSPECTED CANDIDATES' in html, 'Suspected tab missing'
assert '[BREACH DISCLOSURES]' in html, 'Breach tab missing'
assert '[CREDENTIAL VAULT]' in html, 'Credentials tab missing'
assert '[GEOLOCATION &amp; MAP]' in html or '[GEOLOCATION & MAP]' in html, 'Map tab missing'
assert '[ATTACK CHAIN &amp; TIMELINE]' in html or '[ATTACK CHAIN & TIMELINE]' in html, 'Timeline tab missing'
print('All 23 HTML DOM structural assertions passed!', flush=True)

print('\n--- Fast Query Verification (alex.morgan@cybercorp.io) ---', flush=True)
req = urllib.request.urlopen('http://127.0.0.1:8000/api/search?email=alex.morgan@cybercorp.io&audit_mode=false', timeout=10)
data = json.loads(req.read().decode('utf-8'))
print('Target Name:', data['employee']['full_name'], flush=True)
print('Score Level:', data['spillover_score']['level'], '| Numeric Score:', data['spillover_score']['numeric_score'], flush=True)
print('Credentials count:', len(data.get('credentials', [])), flush=True)
print('\n--- Query Verification (filipos123.91@gmail.com) ---', flush=True)
t0 = time.time()
req2 = urllib.request.urlopen('http://127.0.0.1:8000/api/search?email=filipos123.91@gmail.com&audit_mode=false', timeout=5)
data2 = json.loads(req2.read().decode('utf-8'))
print(f"Target Name: {data2['employee']['full_name']} (Retrieved in {time.time()-t0:.2f}s)", flush=True)
print(f"Score Level: {data2['spillover_score']['level']} | Numeric Score: {data2['spillover_score']['numeric_score']}", flush=True)
print(f"Job title: '{data2['employee']['job_title']}' | Department: '{data2['employee']['department']}'", flush=True)
print('Credentials count:', len(data2.get('credentials', [])), flush=True)
print('Footprints count:', len(data2.get('physical_footprints', [])), flush=True)
print('Pivots count:', len(data2.get('pivots', [])), flush=True)

print('\nALL INTEGRATION TESTS COMPLETED SUCCESSFULLY!', flush=True)



