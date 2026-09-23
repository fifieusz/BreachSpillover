import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

def test_search(name, url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode('utf-8', errors='ignore')
            print(f"[{name}] Status: {res.status}, Len: {len(html)}")
            fb = re.findall(r'https?://(?:www\.)?facebook\.com/[^\s"\'&<>]+', html)
            print(f"  [{name}] FB links: {set(fb)}")
            if "Wolvega" in html:
                print(f"  [{name}] FOUND WOLVEGA!")
    except Exception as e:
        print(f"[{name}] Error: {e}")

q = urllib.parse.quote('"Jordin Zwaan"')
q_fb = urllib.parse.quote('Jordin Zwaan facebook')

test_search("Mojeek", f"https://www.mojeek.com/search?q={q}")
test_search("Mojeek FB", f"https://www.mojeek.com/search?q={q_fb}")
test_search("Ecosia", f"https://www.ecosia.org/search?q={q}")
test_search("Ecosia FB", f"https://www.ecosia.org/search?q={q_fb}")
test_search("Ask", f"https://www.ask.com/web?q={q}")
test_search("Ask FB", f"https://www.ask.com/web?q={q_fb}")
