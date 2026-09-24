import urllib.request
import urllib.parse
import re

url = 'https://www.bing.com/search?q=' + urllib.parse.quote('"Yasir1kadhim"')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}
with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
    html = r.read().decode('utf-8', errors='ignore')

print('ingen resultater:', 'ingen resultater' in html.lower())
print('no results:', 'no results' in html.lower())
matches = list(re.finditer(r'(ingen resultater|no results|finner ikke|fant ingen|zero results|b_no)', html, re.I))
print('Count of matches:', len(matches))
for m in matches[:5]:
    start = max(0, m.start() - 60)
    end = min(len(html), m.end() + 60)
    print('CONTEXT:', html[start:end])
