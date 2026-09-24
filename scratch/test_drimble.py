import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7'
}

queries = [
    "https://drimble.nl/zoeken?q=" + urllib.parse.quote("Yasir Kadhim"),
    "https://drimble.nl/zoeken?q=" + urllib.parse.quote("Kadhim Bergschenhoek"),
    "https://drimble.nl/zoeken?q=" + urllib.parse.quote("JY Collective"),
]

for url in queries:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        print(f"URL: {url} -> Status: {resp.status}, Len: {len(html)}")
        # Look for text matches
        cards = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>', html)
        matches = [c for c in cards if any(k in c[1].lower() for k in ['kadhim', 'kadim', 'jy collective', 'yasir'])]
        print(f"Found {len(matches)} matches:")
        for m in matches[:5]:
            clean = re.sub(r'<[^>]+>', ' ', m[1]).strip()
            print("  -", m[0], ":", clean)
    except Exception as e:
        print(f"URL: {url} Failed: {e}")
