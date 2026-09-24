import urllib.request, urllib.parse, base64
from bs4 import BeautifulSoup

def search_bing(q):
    url = 'https://www.bing.com/search?q=' + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            html = r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {q}: {e}")
        return

    soup = BeautifulSoup(html, 'html.parser')
    algos = soup.find_all('li', class_='b_algo')
    print(f'=== Query: {q} (Hits: {len(algos)}) ===')
    for a in algos[:5]:
        h2 = a.find('h2')
        link = a.find('a')
        p = a.find('p')
        href = link.get('href') if link else ''
        if 'bing.com/ck/a' in href and 'u=' in href:
            try:
                u_param = href.split('u=')[1].split('&')[0]
                b64 = u_param[2:] + '=' * ((4 - len(u_param[2:]) % 4) % 4)
                dec = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                href = dec
            except Exception:
                pass
        t_str = (h2.get_text() if h2 else '').encode('ascii', 'replace').decode('ascii')
        s_str = (p.get_text()[:120] if p else '').encode('ascii', 'replace').decode('ascii')
        print('  Title:', t_str)
        print('  URL:', href)
        print('  Snippet:', s_str)

search_bing('"Sjoerd Sikkema"')
search_bing('"sjoerdsikkema"')
search_bing('site:linkedin.com "Sjoerd Sikkema"')
search_bing('"xmister"')
search_bing('"xmister795"')
