import urllib.request
import re
import urllib.parse

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
url = 'https://www.mojeek.com/search?q=' + urllib.parse.quote('Yasir Kadhim')
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=5) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Mojeek uses <a class="title" href="...">
titles = re.findall(r'<a\s+[^>]*class="[^"]*title[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', html)
snippets = re.findall(r'<p\s+[^>]*class="[^"]*snippet[^"]*"[^>]*>([\s\S]*?)</p>', html)

print(f"Mojeek results ({len(titles)}):")
for idx, (href, title_html) in enumerate(titles[:10]):
    clean_t = re.sub(r'<[^>]+>', '', title_html).strip()
    snip = re.sub(r'<[^>]+>', '', snippets[idx]).strip() if idx < len(snippets) else ""
    print(f"[{idx+1}] {clean_t}")
    print(f"    URL : {href}")
    print(f"    SNIP: {snip[:120]}")
