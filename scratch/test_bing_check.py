import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import urllib.request
import urllib.parse
import re
import base64

def check_query(q):
    url = 'https://www.bing.com/search?q=' + urllib.parse.quote(q)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
    print(f"\n=== Query: {q} (Blocks: {len(blocks)}) ===")
    for i, b in enumerate(blocks[:6]):
        h2 = re.search(r'<h2[^>]*>([\s\S]*?)</h2>', b)
        h2_text = re.sub(r'<[^>]+>', '', h2.group(1)) if h2 else 'NO H2'
        p = re.search(r'<p[^>]*>([\s\S]*?)</p>', b)
        p_text = re.sub(r'<[^>]+>', '', p.group(1)) if p else ''
        a_href = re.search(r'href="([^"]+)"', b)
        url_dest = ""
        if a_href:
            clean_href = a_href.group(1).replace('&amp;', '&')
            if 'bing.com/ck/a' in clean_href:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(clean_href).query)
                u = qs.get('u', [''])[0]
                if u.startswith('a1'):
                    b64 = u[2:] + '=' * ((4 - len(u[2:]) % 4) % 4)
                    try:
                        url_dest = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                    except:
                        url_dest = clean_href
            else:
                url_dest = clean_href
        print(f"[{i+1}] {h2_text}")
        print(f"    URL: {url_dest}")
        print(f"    Snip: {p_text[:120]}")

check_query('"Yasir Kadhim"')
check_query('Yasir Ashraf Kadhim')
check_query('Yasir Kadhim Rotterdam')
check_query('Yasir Kadhim Netherlands')
check_query('Yasir Kadhim Bergschenhoek')
check_query('Yasir Kadhim "JY Collective"')
check_query('Yasir1kadhim')
