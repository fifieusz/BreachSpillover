import urllib.request
import urllib.parse
import re
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

endpoints = [
    ("Ecosia", "https://www.ecosia.org/search?q="),
    ("Qwant", "https://www.qwant.com/?q="),
    ("Startpage", "https://www.startpage.com/sp/search?query="),
    ("Brave", "https://search.brave.com/search?q="),
    ("Mojeek", "https://www.mojeek.com/search?q=")
]

query = "Jordin Zwaan facebook"

for name, base in endpoints:
    url = base + urllib.parse.quote(query)
    start = time.time()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            dur = time.time() - start
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"[{name}] {resp.status} in {dur:.2f}s, len={len(html)}")
            # Search for facebook links or snippets
            fbs = re.findall(r'href="(https?://[^"]*facebook\.com/[^"]*)"', html, re.I)
            print(f"  [{name}] FB links ({len(fbs)}):", fbs[:3])
    except Exception as e:
        print(f"[{name}] Failed in {time.time() - start:.2f}s: {e}")
