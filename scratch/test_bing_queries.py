import urllib.request, re, base64, urllib.parse

for q in ['"Alje Woltjer"', '"Alje Woltjer" Vooruit', 'site:linkedin.com/in "Alje Woltjer"', 'site:linkedin.com "Alje Woltjer"']:
    url = 'https://www.bing.com/search?q=' + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            html = r.read().decode('utf-8', errors='ignore')
        blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
        print(f'=== Query: {q} | Blocks: {len(blocks)} ===')
        for b in blocks[:2]:
            h2 = re.search(r'<h2[^>]*>([\s\S]*?)</h2>', b)
            if h2:
                print('  H2:', re.sub(r'<[^>]+>', '', h2.group(1)).strip())
            p = re.search(r'<p[^>]*>([\s\S]*?)</p>', b)
            if p:
                print('  Snippet:', re.sub(r'<[^>]+>', '', p.group(1))[:150])
    except Exception as e:
        print(f'Error for {q}: {e}')
