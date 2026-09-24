import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

queries = [
    '"Yasir1kadhim@gmail.com"',
    'Yasir1kadhim',
    '"Yasir Kadhim"',
    '"Yasir Ashraf Kadhim"',
    'Yasir Ashraf Kadhim Rotterdam',
    'site:drimble.nl Kadhim'
]

for q in queries:
    url = 'https://www.bing.com/search?q=' + urllib.parse.quote(q)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        print(f"=== Query: {q} ===")
        print(f"HTML len: {len(html)}")
        # Find titles
        h2s = re.findall(r'<h2[^>]*>[\s\S]*?</h2>', html)
        print(f"Found {len(h2s)} h2 elements:")
        for h in h2s[:5]:
            clean = re.sub(r'<[^>]+>', ' ', h).strip()
            print("  -", clean)
    except Exception as e:
        print(f"Query {q} failed: {e}")
