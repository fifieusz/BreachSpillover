import urllib.request
import urllib.parse
import re

def query_ddg_post(q):
    data = urllib.parse.urlencode({'q': q}).encode('utf-8')
    req = urllib.request.Request('https://html.duckduckgo.com/html/', data=data, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://duckduckgo.com/'
    })
    resp = urllib.request.urlopen(req, timeout=5)
    html = resp.read().decode('utf-8', errors='ignore')
    blocks = re.findall(r'<div class="result results_links[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    print(f"Query: '{q}' -> Status: {resp.status}, Blocks: {len(blocks)}")
    for b in blocks[:3]:
        title_m = re.search(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b)
        if title_m:
            raw_href = title_m.group(1)
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
            clean_url = qs.get("uddg", [raw_href])[0]
            clean_title = re.sub(r'<[^>]+>', '', title_m.group(2)).strip()
            print(f"   * {clean_title} -> {clean_url}")

if __name__ == '__main__':
    query_ddg_post('Jordin Zwaan')
    query_ddg_post('Jordin Zwaan facebook')
    query_ddg_post('Jordin Zwaan linkedin')
    query_ddg_post('jordinzwaan2016')
