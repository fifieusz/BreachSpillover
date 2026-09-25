import urllib.request, re, base64, urllib.parse

url = 'https://www.bing.com/search?q=Alje+Woltjer+Vooruit'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
with urllib.request.urlopen(req, timeout=5) as r:
    html = r.read().decode('utf-8', errors='ignore')

blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
print('Blocks found:', len(blocks))
for idx, b in enumerate(blocks[:5]):
    print(f'=== BLOCK {idx} ===')
    h2 = re.search(r'<h2[^>]*>([\s\S]*?)</h2>', b)
    if h2:
        print('H2 content:', h2.group(1)[:200])
        a_m = re.search(r'<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', h2.group(1))
        if a_m:
            href = a_m.group(1)
            raw_title = re.sub(r'<[^>]+>', '', a_m.group(2)).strip()
            print('  Title:', raw_title)
            print('  Href:', href[:100])
            if 'bing.com/ck/a' in href:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                u_param = qs.get('u', [''])[0]
                if u_param.startswith('a1'):
                    b64 = u_param[2:]
                    b64 += '=' * ((4 - len(b64) % 4) % 4)
                    try:
                        dec = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                        print('  Decoded URL:', dec)
                    except Exception as e:
                        print('  Decode error:', e)
    p = re.search(r'<p[^>]*>([\s\S]*?)</p>', b)
    if p:
        print('  Snippet:', re.sub(r'<[^>]+>', '', p.group(1))[:200])
