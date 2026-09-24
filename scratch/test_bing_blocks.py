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

# find all <li class="b_algo"
blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
print("Total b_algo blocks found:", len(blocks))
for i, b in enumerate(blocks[:5]):
    print(f"\n--- Block {i} ---")
    # find all <a> in this block
    a_tags = re.findall(r'<a\s+([^>]+)>([\s\S]*?)</a>', b)
    for attrs, inner in a_tags[:3]:
        clean_inner = re.sub(r'<[^>]+>', '', inner).strip()
        print("  attrs:", attrs[:120])
        print("  text:", clean_inner[:80])
