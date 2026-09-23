import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

endpoints = [
    ("Bing", "https://www.bing.com/search?q="),
    ("Yahoo", "https://search.yahoo.com/search?p="),
    ("Mojeek", "https://www.mojeek.com/search?q="),
    ("Swisscows", "https://swisscows.com/web?query=")
]

query = "Jordin Zwaan facebook"

for name, base_url in endpoints:
    url = base_url + urllib.parse.quote(query)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"[{name}] HTTP {resp.status} - length: {len(html)}")
            fb_matches = re.findall(r'https?://(?:www\.)?facebook\.com/[^\s"\'<>]+', html, re.I)
            print(f"[{name}] Facebook links ({len(fb_matches)}):", fb_matches[:3])
    except Exception as e:
        print(f"[{name}] Failed: {e}")
