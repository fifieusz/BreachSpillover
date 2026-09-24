import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

def check(name, url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"{name}: status {resp.status}, len {len(html)}")
            links = re.findall(r'href=[\'"](https?://[^\'"]+)[\'"]', html)
            ext = [l for l in links if not any(x in l for x in ['ecosia', 'brave', 'bing', 'microsoft', 'google', 'facebook.com/policies'])]
            print(f"  {name} ext links: {len(ext)} -> {ext[:3]}")
    except Exception as e:
        print(f"{name} err: {e}")

q = urllib.parse.quote('"Yasir Ashraf"')
check('Ecosia', f'https://www.ecosia.org/search?q={q}')
check('Brave', f'https://search.brave.com/search?q={q}')
check('Qwant', f'https://www.qwant.com/?q={q}')
check('Startpage', f'https://www.startpage.com/sp/search?query={q}')
