import urllib.request, urllib.parse, base64, re
from bs4 import BeautifulSoup

def improved_bing_search(query: str, max_results: int = 10):
    snippets = []
    seen = set()
    try:
        url = "https://www.bing.com/search?q=" + urllib.parse.quote(query) + "&setlang=en&cc=us"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        soup = BeautifulSoup(html, 'html.parser')
        algos = soup.find_all('li', class_=lambda c: c and 'b_algo' in c)
        
        query_terms = [t.lower() for t in re.findall(r'[a-zA-Z0-9]+', query) if len(t) >= 3 and t.lower() not in ["site", "http", "https", "com", "www", "org", "net"]]

        for a in algos[:max_results]:
            h2 = a.find('h2')
            link = h2.find('a') if h2 else a.find('a')
            if not link:
                continue
            title = link.get_text().strip()
            href = link.get('href', '').strip()
            p = a.find('p')
            snip = p.get_text().strip() if p else ''

            if 'bing.com/ck/a' in href:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                u_param = qs.get('u', [''])[0]
                if u_param.startswith('a1'):
                    b64 = u_param[2:]
                    b64 += '=' * ((4 - len(b64) % 4) % 4)
                    try:
                        dec = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                        if dec.startswith('http') and 'bing.com' not in dec and 'microsoft.com' not in dec:
                            href = dec
                    except Exception:
                        pass

            if href and href not in seen and 'bing.com' not in href:
                seen.add(href)
                snippets.append({
                    "title": title or href,
                    "url": href,
                    "snippet": snip
                })
    except Exception as e:
        print("Bing error:", e)
    return snippets

for q in ['"Sjoerd Sikkema"', 'Sjoerd Sikkema Wolvega', 'Yasir Kadhim', 'Filip Niewiadomski']:
    res = improved_bing_search(q, max_results=5)
    print(f"Query: {q} -> Found {len(res)} results:")
    for r in res[:2]:
        print("  ", r['title'][:60], "->", r['url'])
