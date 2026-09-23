import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

for q in ['Jordin Zwaan', 'Jordin Zwaan facebook', '"Jordin Zwaan"']:
    url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode('utf-8', errors='ignore')
            # Extract links and titles from Bing
            blocks = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)
            print(f"Bing '{q}': {len(blocks)} blocks")
            for b in blocks[:5]:
                m = re.search(r'<h2><a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', b)
                snip_m = re.search(r'<p[^>]*>(.*?)</p>', b)
                if m:
                    title = re.sub(r'<[^>]+>', '', m.group(2))
                    snip = re.sub(r'<[^>]+>', '', snip_m.group(1)) if snip_m else ""
                    print(f"   {title} -> {m.group(1)}")
                    if snip:
                        print(f"      {snip[:100]}")
    except Exception as e:
        print(f"Bing '{q}' Error: {e}")
