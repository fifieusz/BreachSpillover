import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

url = "https://www.bing.com/search?q=" + urllib.parse.quote("Jordin Zwaan")
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=5.0) as resp:
    html = resp.read().decode('utf-8', errors='ignore')
    # Print any external links starting with http
    external = [l for l in re.findall(r'href="(https?://[^"]+)"', html) if 'bing.com' not in l and 'microsoft.com' not in l]
    print(f"External links count: {len(external)}")
    for e in external[:10]:
        print(" ->", e)
