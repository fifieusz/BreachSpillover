import urllib.request, re, urllib.parse, base64

def search_bing(query):
    url = "https://www.bing.com/search?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    with urllib.request.urlopen(req, timeout=5) as r:
        html = r.read().decode('utf-8', errors='ignore')
    blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
    results = []
    for b in blocks:
        h2 = re.search(r'<h2[^>]*>([\s\S]*?)</h2>', b)
        if not h2: continue
        a_m = re.search(r'<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', h2.group(1))
        if not a_m: continue
        raw_href = a_m.group(1).replace('&amp;', '&')
        title = re.sub(r'<[^>]+>', '', a_m.group(2)).strip()
        target_url = None
        if raw_href.startswith('http') and 'bing.com' not in raw_href:
            target_url = raw_href
        elif 'bing.com/ck/a' in raw_href:
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
            u_param = qs.get('u', [''])[0]
            if u_param.startswith('a1'):
                b64 = u_param[2:]
                b64 += '=' * ((4 - len(b64) % 4) % 4)
                try:
                    dec = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                    if dec.startswith('http') and 'bing.com' not in dec:
                        target_url = dec
                except: pass
        if target_url:
            snip_m = re.search(r'<p[^>]*>([\s\S]*?)</p>', b) or re.search(r'<div class="b_caption"[^>]*>([\s\S]*?)</div>', b)
            snip = re.sub(r'<[^>]+>', ' ', snip_m.group(1)).strip() if snip_m else ""
            results.append({'url': target_url, 'title': title, 'snippet': snip})
    return results

for q in ['"Jordin Zwaan"', 'Jordin Zwaan linkedin', 'jordinzwaan2016', 'jordinzwaan']:
    res = search_bing(q)
    print(f"=== Query: {q} ({len(res)} results) ===")
    for r in res[:4]:
        print("  URL:", r['url'])
        print("  Title:", r['title'])
        print("  Snippet:", r['snippet'][:120])
    print()
