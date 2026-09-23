import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

urls = [
    "https://www.facebook.com/public/Jordin-Zwaan",
    "https://m.facebook.com/public/Jordin-Zwaan",
    "https://www.facebook.com/public/jordinzwaan",
    "https://m.facebook.com/public/jordinzwaan"
]

for u in urls:
    req = urllib.request.Request(u, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode('utf-8', errors='ignore')
            print(f"URL: {u} | Status: {res.status} | Len: {len(html)}")
            # look for profiles
            profs = re.findall(r'href="([^"]*facebook\.com/[^"]*)"', html)
            print("  Profs count:", len(profs))
            for p in profs[:5]:
                print("   ->", p)
            if "Wolvega" in html:
                print("  FOUND WOLVEGA IN FB HTML!")
    except Exception as e:
        print(f"URL: {u} | Error: {e}")
