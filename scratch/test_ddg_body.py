with open("scratch/ddg_body.html", "w", encoding="utf-8") as f:
    pass

import urllib.request
import urllib.parse
import re

url = "https://lite.duckduckgo.com/lite/"
data = urllib.parse.urlencode({'q': 'Yasir Kadhim'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://lite.duckduckgo.com/'
}
req = urllib.request.Request(url, data=data, headers=headers)
with urllib.request.urlopen(req, timeout=5) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# find all <a> tags
links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html)
print("Total <a> tags:", len(links))
for href, t in links[:15]:
    clean_t = re.sub(r'<[^>]+>', '', t).strip()
    print(" ->", clean_t, "|", href)
