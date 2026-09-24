import urllib.request
import urllib.parse
import re

# Test Yahoo
url = "https://search.yahoo.com/search?p=" + urllib.parse.quote("Yasir Kadhim")
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})
with urllib.request.urlopen(req, timeout=5) as resp:
    y_html = resp.read().decode('utf-8', errors='ignore')

print("Yahoo HTML length:", len(y_html))
links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', y_html)
print("Yahoo total links:", len(links))
for href, t in links:
    if "r.search.yahoo.com" in href:
        clean_t = re.sub(r'<[^>]+>', '', t).strip()
        print("Yahoo r.search link:", clean_t[:50], "->", href[:90])
        # decode actual destination URL from r.search.yahoo.com
        # Format usually: https://r.search.yahoo.com/.../RU=https%3a%2f%2f.../RK=...
        m = re.search(r'/RU=([^/]+)/', href)
        if m:
            dest = urllib.parse.unquote(m.group(1))
            print(" -> EXTRACTED DEST:", dest)
