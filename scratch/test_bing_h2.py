import urllib.request
import urllib.parse
import re

query = 'Yasir Kadhim'
url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=5) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Search for any <h2> tags
h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
print('Total H2 tags:', len(h2s))
for h in h2s[:8]:
    print('H2:', re.sub(r'<[^>]+>', '', h).strip())
    # find href inside
    m = re.search(r'href="([^"]+)"', h)
    if m:
        print(' -> URL:', m.group(1))
