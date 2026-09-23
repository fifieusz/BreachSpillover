import urllib.request
import re

url = "https://jordinzwaan2016.wixsite.com/portfolio"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=6) as r:
    html = r.read().decode('utf-8', errors='ignore')

# Meta tags
metas = re.findall(r'<meta\s+[^>]*content="([^"]*)"[^>]*>', html)
for m in metas:
    if len(m) > 10 and not m.startswith('http') and not m.startswith('width'):
        print("Meta:", m)

# Search for city or location keywords or Dutch keywords
for kw in ['amsterdam', 'netherlands', 'nederland', 'rotterdam', 'utrecht', 'merlon', 'security', 'student', 'designer']:
    matches = re.findall(rf'(.{{0,40}}{kw}.{{0,40}})', html, re.IGNORECASE)
    if matches:
        print(f"Keyword '{kw}': {len(matches)} matches")
        for match in matches[:3]:
            print(f"   -> {match.strip()}")
