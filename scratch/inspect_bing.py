import urllib.request
import urllib.parse
import re

url = f"https://www.bing.com/search?q=jordin+zwaan+facebook"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=8) as r:
    html = r.read().decode('utf-8', errors='ignore')

items = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)
print(f"Items found: {len(items)}")
for i, it in enumerate(items[:5]):
    # find all <a> tags
    links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', it, re.DOTALL)
    clean_text = re.sub(r'<[^>]+>', ' ', it)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    print(f"\n--- ITEM {i+1} ---")
    for href, anchor in links:
        clean_anchor = re.sub(r'<[^>]+>', '', anchor).strip()
        if href.startswith("http") and "bing.com" not in href and "microsoft.com" not in href:
            print(f"  Link: {href} ({clean_anchor})")
    print(f"  Text snippet: {clean_text[:250]}...")
