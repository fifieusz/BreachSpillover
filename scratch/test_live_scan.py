import urllib.request
import json
import time

t0 = time.time()
url = 'http://127.0.0.1:8000/api/scan?email=jordinzwaan2016@gmail.com'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(r.read().decode('utf-8'))
    print(f"Scan completed in {time.time()-t0:.2f}s")
    print(f"Direct Leaks: {len(data.get('direct_leaks', []))}")
    print(f"Total Pivots: {len(data.get('pivots', []))}")
    ptypes = set(p['pivot_type'] for p in data.get('pivots', []))
    print(f"Pivot Types: {ptypes}")
    for p in data.get('pivots', [])[:10]:
        print(f" - [{p['pivot_type']}] {p['pivot_value']}")
