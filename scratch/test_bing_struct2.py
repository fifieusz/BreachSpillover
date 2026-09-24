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

p = html.find('class="b_algo"')
snippet = html[p:p+12000]
links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', snippet)
for href, text in links:
    clean = re.sub(r'<[^>]+>', '', text).strip()
    print('LINK:', repr(clean[:60]), '->', href[:100])
