import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

queries = [
    'site:facebook.com "Jordin Zwaan"',
    '"Jordin Zwaan" facebook',
    'Jordin Zwaan facebook',
    'Jordin Zwaan Wolvega'
]

for q in queries:
    url = "https://www.bing.com/search?q=" + urllib.parse.quote(q)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"\n=== Bing: {q} ===")
            # Look for <h2><a href="...">...</a></h2>
            items = re.findall(r'<li class="b_algo"[^>]*>[\s\S]*?<h2><a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a></h2>[\s\S]*?<p[^>]*>([\s\S]*?)</p>', html)
            print(f"Found {len(items)} results")
            for href, raw_t, raw_s in items[:5]:
                t = re.sub(r'<[^>]+>', '', raw_t).strip()
                s = re.sub(r'<[^>]+>', '', raw_s).strip()
                print(f"  Title: {t}")
                print(f"  URL: {href}")
                print(f"  Snippet: {s[:120]}")
    except Exception as e:
        print(f"Bing failed for {q}: {e}")
