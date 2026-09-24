import urllib.request, urllib.parse, re
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8'
}

queries = [
    'Sjoerd Sikkema linkedin',
    'Sjoerd Sikkema facebook',
    'Sjoerd Sikkema Wolvega',
    'Sjoerd Sikkema korfbal',
    'xmister github',
    'xmister steam'
]

for q in queries:
    print(f"\n==========================================")
    print(f"QUERY: {q}")
    print(f"==========================================")
    url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        algos = soup.find_all('li', class_=lambda c: c and 'b_algo' in c)
        print(f"Found {len(algos)} results:")
        for a in algos[:3]:
            h2 = a.find('h2')
            link = h2.find('a') if h2 else None
            p = a.find('p')
            title = link.get_text() if link else ''
            href = link.get('href') if link else ''
            snip = p.get_text() if p else ''
            
            # Decode Bing redirect if present
            if 'bing.com/ck/a' in href:
                import base64
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                u_param = qs.get('u', [''])[0]
                if u_param.startswith('a1'):
                    b64 = u_param[2:] + '=' * ((4 - len(u_param[2:]) % 4) % 4)
                    try:
                        href = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                    except Exception:
                        pass
            print(f"  [{title[:60]}]\n   -> {href}\n   Snippet: {snip[:90]}\n")
    except Exception as e:
        print("Error:", e)
