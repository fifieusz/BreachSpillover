import urllib.request
import urllib.parse
import re

url = "https://search.yahoo.com/search?p=" + urllib.parse.quote('"jordin zwaan"')
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
})
try:
    with urllib.request.urlopen(req, timeout=8) as r:
        html = r.read().decode('utf-8', errors='ignore')
    print("Yahoo status:", r.status, "Len:", len(html))
    links = re.findall(r'<a class=" d-ib[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
    print("Links found:", len(links))
    for href, title in links[:5]:
        print(" ", href, "->", re.sub(r'<[^>]+>', '', title))
except Exception as e:
    print("Yahoo error:", e)
