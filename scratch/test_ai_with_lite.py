import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.web_dork_recon import query_search_snippets, disambiguate_with_llm
import urllib.request
import urllib.parse
import re
import json

def fetch_ddg_lite(q):
    url = "https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({'q': q}).encode('utf-8')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://lite.duckduckgo.com/'
    }
    req = urllib.request.Request(url, data=data, headers=headers)
    snippets = []
    try:
        with urllib.request.urlopen(req, timeout=6) as res:
            html = res.read().decode('utf-8', errors='ignore')
        a_tags = re.findall(r'<a[^>]+class=[\'"]result-link[\'"][^>]*>.*?</a>', html, re.DOTALL)
        snip_tags = re.findall(r'<td[^>]+class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>', html, re.DOTALL)
        for i in range(min(len(a_tags), len(snip_tags))):
            tag = a_tags[i]
            href_m = re.search(r'href=[\'"]([^\'"]+)[\'"]', tag)
            href = href_m.group(1) if href_m else ""
            title = re.sub(r'<[^>]+>', '', tag).strip()
            snip = re.sub(r'<[^>]+>', ' ', snip_tags[i])
            snip = re.sub(r'\s+', ' ', snip).strip()
            if href and "duckduckgo.com" not in href:
                snippets.append({"title": title, "url": href, "snippet": snip})
    except Exception as e:
        print("Lite error:", e)
    return snippets

# Gather snippets for Jordin Zwaan
all_snips = []
seen = set()

for q in ['"Jordin Zwaan"', 'Jordin Zwaan facebook', 'jordinzwaan']:
    for s in fetch_ddg_lite(q):
        if s['url'] not in seen:
            seen.add(s['url'])
            all_snips.append(s)

print(f"Total unique snippets from Lite: {len(all_snips)}")
for s in all_snips:
    if "wolvega" in s['snippet'].lower() or "wixsite" in s['url'].lower():
        print(f"  [FOUND] {s['title']} | {s['url']}")
        print(f"     {s['snippet']}")

# Now run AI disambiguation with Groq Llama 3.3
res = disambiguate_with_llm("Jordin Zwaan", "jordinzwaan2016@gmail.com", all_snips, ["jordinzwaan", "sazeku"])
print("\n=== AI DISAMBIGUATION RESULT ===")
print(json.dumps(res, indent=2))
