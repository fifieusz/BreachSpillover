import urllib.request
import urllib.parse
import re

def search_ddg(q):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            html = res.read().decode('utf-8', errors='ignore')
            print(f"[{q}] DDG status: {res.status}, len: {len(html)}")
            if "anomaly-modal" in html or "challenge" in html:
                print(f"[{q}] Blocked by bot detection")
                return
            blocks = re.findall(r'<div class="result results_links[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
            print(f"[{q}] Results found: {len(blocks)}")
            for b in blocks[:5]:
                title_m = re.search(r'<a class="result__url"[^>]*href="([^"]*uddg=[^"]*)"[^>]*>(.*?)</a>', b)
                snip_m = re.search(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', b, re.DOTALL)
                raw_href = title_m.group(1) if title_m else ""
                snip = re.sub(r'<[^>]+>', '', snip_m.group(1)).strip() if snip_m else ""
                if 'uddg=' in raw_href:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                    real_url = qs['uddg'][0]
                    print(f"  * {real_url}")
                    print(f"    {snip[:100]}")
    except Exception as e:
        print(f"[{q}] DDG error: {e}")

search_ddg('Yasir Ashraf Kadhim')
search_ddg('JY Collective Bergschenhoek')
search_ddg('Yasir Kadhim')
