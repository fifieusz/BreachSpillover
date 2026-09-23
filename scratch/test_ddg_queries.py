import urllib.request
import urllib.parse
import re

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
        print(f"Error for '{q}': {e}")
    return snippets

queries = [
    'Jordin Zwaan',
    '"Jordin Zwaan"',
    'Jordin Zwaan facebook',
    'site:facebook.com Jordin Zwaan',
    'site:facebook.com "Jordin Zwaan"',
    'facebook.com Jordin Zwaan',
    'Jordin Zwaan Wolvega',
    'Jordin Zwaan Deltion'
]

for q in queries:
    snips = fetch_ddg_lite(q)
    print(f"Query: [{q}] -> {len(snips)} results")
    for s in snips:
        if "facebook" in s['url'].lower() or "facebook" in s['title'].lower():
            print(f"   [FB] {s['title']} | {s['url']}")
            print(f"        {s['snippet']}")
        elif "wolvega" in s['snippet'].lower() or "wolvega" in s['title'].lower():
            print(f"   [WOLVEGA] {s['title']} | {s['url']}")
            print(f"        {s['snippet']}")
