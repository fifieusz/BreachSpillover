import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
}

def test_engine(name, url, q_param, query):
    full_url = f"{url}?{urllib.parse.urlencode({q_param: query})}"
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"[{name}] Status: {resp.status}, Len: {len(html)}")
            matches = list(re.finditer(r'(kadhim|kadim|jy collective|bergschenhoek)', html, re.I))
            print(f"[{name}] Hits for keywords: {len(matches)}")
            for m in matches[:3]:
                s = max(0, m.start() - 40)
                e = min(len(html), m.end() + 60)
                print(f"   Hit: {html[s:e].strip()}")
    except Exception as e:
        print(f"[{name}] Failed: {e}")

test_engine("Mojeek", "https://www.mojeek.com/search", "q", "Yasir Kadhim")
test_engine("Mojeek-2", "https://www.mojeek.com/search", "q", "JY Collective")
test_engine("Mojeek-3", "https://www.mojeek.com/search", "q", "Yasir Ashraf Kadhim")
test_engine("Bing-nl", "https://www.bing.com/search", "q", "Yasir Kadhim Bergschenhoek")
test_engine("Bing-oozo", "https://www.bing.com/search", "q", "site:oozo.nl Kadhim")
test_engine("Bing-comp", "https://www.bing.com/search", "q", "site:companyinfo.nl \"JY Collective\"")
test_engine("Bing-drimble", "https://www.bing.com/search", "q", "site:drimble.nl \"JY Collective\"")
