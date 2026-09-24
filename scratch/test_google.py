import urllib.request
import urllib.parse
import re

g_url = "https://www.google.com/search?q=" + urllib.parse.quote("Yasir Kadhim")
g_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
req = urllib.request.Request(g_url, headers=g_headers)
with urllib.request.urlopen(req, timeout=5) as resp:
    g_html = resp.read().decode('utf-8', errors='ignore')

# Google search results usually have <div class="yuRUbf"><a href="..."> or <h3>
h3s = re.findall(r'<h3[^>]*>([\s\S]*?)</h3>', g_html)
print("Google h3 count:", len(h3s))
for h in h3s[:10]:
    print("H3:", re.sub(r'<[^>]+>', '', h).strip())

# Also check for links
links = re.findall(r'<a\s+[^>]*href="(https://[^"]+)"[^>]*>([\s\S]*?)</a>', g_html)
print("Google https links:", len(links))
for h, t in links[:15]:
    clean = re.sub(r'<[^>]+>', '', t).strip()
    if clean and 'google.com' not in h:
        print(" ->", clean[:50], "->", h[:80])
