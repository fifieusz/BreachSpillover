import urllib.request
import urllib.parse
import re

print("--- Testing html.duckduckgo.com/html/ ---")
url = "https://html.duckduckgo.com/html/"
data = urllib.parse.urlencode({'q': 'Yasir Kadhim'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://duckduckgo.com/'
}
try:
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    print("html.ddg length:", len(html))
    links = re.findall(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
    print("html.ddg result__a links:", len(links))
    for h, t in links[:5]:
        print(" ->", re.sub(r'<[^>]+>', '', t).strip(), "->", h)
except Exception as e:
    print("html.ddg error:", e)

print("\n--- Testing Google Search ---")
g_url = "https://www.google.com/search?q=" + urllib.parse.quote("Yasir Kadhim")
g_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
try:
    req = urllib.request.Request(g_url, headers=g_headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        g_html = resp.read().decode('utf-8', errors='ignore')
    print("Google length:", len(g_html))
    g_links = re.findall(r'<a href="(/url\?q=[^"&]+|https://[^"]+)"[^>]*><h3[^>]*>(.*?)</h3>', g_html)
    print("Google h3 links:", len(g_links))
    for h, t in g_links[:5]:
        print(" ->", re.sub(r'<[^>]+>', '', t).strip(), "->", h)
except Exception as e:
    print("Google error:", e)
