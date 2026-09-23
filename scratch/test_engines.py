import urllib.request
import urllib.parse
import re
import json

def test_engine(name, url, headers=None, method="GET", data=None):
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=7) as res:
            text = res.read().decode('utf-8', errors='ignore')
            print(f"[{name}] Status: {res.status}, Len: {len(text)}")
            matches = [m.start() for m in re.finditer(r'facebook\.com', text, re.IGNORECASE)]
            print(f"  -> Facebook mentions: {len(matches)}")
            if len(matches) > 0:
                print(f"  -> Snippet near first match: {text[max(0, matches[0]-100):min(len(text), matches[0]+200)]}")
            return text
    except Exception as e:
        print(f"[{name}] Error: {e}")
        return ""

q = urllib.parse.quote('"Jordin Zwaan" facebook')
test_engine("Qwant", f"https://api.qwant.com/v3/search/web?q={q}&count=10&locale=en_US")
test_engine("Brave", f"https://search.brave.com/search?q={q}")
test_engine("Swisscows", f"https://swisscows.com/api/web/search?query={q}")
test_engine("Google Direct", f"https://www.google.com/search?q={q}&hl=en")
test_engine("DuckDuckGo API", f"https://api.duckduckgo.com/?q={q}&format=json")
