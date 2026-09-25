import urllib.request, re, base64, urllib.parse

url = 'https://www.bing.com/search?q=python+programming'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
with urllib.request.urlopen(req, timeout=5) as r:
    html = r.read().decode('utf-8', errors='ignore')

blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
print('Blocks:', len(blocks))
for idx, b in enumerate(blocks[:3]):
    a_matches = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', b)
    print(f'Block {idx} a_matches: {len(a_matches)}')
    for href, text in a_matches:
        clean_href = href.replace('&amp;', '&')
        print('  href:', clean_href[:100])
        if 'bing.com/ck/a' in clean_href:
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(clean_href).query)
            u_param = qs.get('u', [''])[0]
            print('  u_param:', u_param[:40])
            if u_param.startswith('a1'):
                b64 = u_param[2:]
                b64 += '=' * ((4 - len(b64) % 4) % 4)
                try:
                    dec = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                    print('  DECODED:', dec)
                except Exception as e:
                    print('  DECODE ERROR:', e)
