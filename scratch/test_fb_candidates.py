import urllib.request
import urllib.parse
import re

candidates = [
    "https://www.facebook.com/jordin.zwaan",
    "https://www.facebook.com/jordinzwaan",
    "https://www.facebook.com/jordinzwaan2016",
    "https://www.facebook.com/sazeku",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

for u in candidates:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"[{u}] Status: {resp.status} - length: {len(html)}")
            # Check title
            t_m = re.search(r'<title>(.*?)</title>', html, re.I)
            if t_m:
                print(f"  Title: {t_m.group(1)}")
    except urllib.error.HTTPError as e:
        print(f"[{u}] HTTPError: {e.code}")
    except Exception as e:
        print(f"[{u}] Error: {e}")
