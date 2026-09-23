import urllib.request
import urllib.parse
import re

url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote("Jordin Zwaan")
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=6) as r:
    html = r.read().decode('utf-8', errors='ignore')

blocks = re.findall(r'<div class="result results_links[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
print(f"Blocks: {len(blocks)}")
for i, b in enumerate(blocks[:6]):
    clean = re.sub(r'<[^>]+>', ' ', b)
    clean = re.sub(r'\s+', ' ', clean).strip()
    print(f"\n[{i+1}] {clean}")
