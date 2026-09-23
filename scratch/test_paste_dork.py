import urllib.request
import urllib.parse
import re

def search_kw(q):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    })
    try:
        with urllib.request.urlopen(req, timeout=6) as res:
            html = res.read().decode('utf-8', errors='ignore')
            urls = re.findall(r'href="([^"]*uddg=[^"]*)"', html)
            real_urls = []
            for u in urls:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
                if 'uddg' in qs:
                    real_urls.append(qs['uddg'][0])
            print(f"Results for '{q}': {len(real_urls)}")
            for r in real_urls[:5]:
                print("  -", r)
            return real_urls
    except Exception as e:
        print("Error:", e)
        return []

if __name__ == '__main__':
    search_kw('test@gmail.com combolist')
    search_kw('filipos123.91@gmail.com')
