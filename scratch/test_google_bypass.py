import urllib.request
import urllib.parse
import re

queries = ['"Jordin Zwaan"', 'Jordin Zwaan facebook', 'site:facebook.com "Jordin Zwaan"']

# Test 1: Google with gbv=1 (Google Basic Version / no-JS lightweight)
def test_google_gbv(q):
    url = f"https://www.google.com/search?q={urllib.parse.quote(q)}&gbv=1&hl=en"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=7) as res:
            html = res.read().decode('utf-8', errors='ignore')
            print(f"[Google gbv=1] Status: {res.status}, Len: {len(html)}")
            if "wolvega" in html.lower():
                print("  [+] FOUND WOLVEGA IN GOOGLE GBV=1!")
            # Extract links
            links = re.findall(r'/url\?q=(https?://[^&]+)&', html)
            print(f"  Links found: {len(links)}")
            for l in links[:5]:
                print(f"    -> {urllib.parse.unquote(l)}")
    except Exception as e:
        print(f"[Google gbv=1] Error: {e}")

# Test 2: Startpage (Google results proxy)
def test_startpage(q):
    url = f"https://www.startpage.com/sp/search"
    data = urllib.parse.urlencode({'query': q}).encode('utf-8')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://www.startpage.com/'
    }
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=7) as res:
            html = res.read().decode('utf-8', errors='ignore')
            print(f"[Startpage] Status: {res.status}, Len: {len(html)}")
            if "wolvega" in html.lower():
                print("  [+] FOUND WOLVEGA IN STARTPAGE!")
            for m in re.finditer(r'href="(https?://[^"]*facebook\.com[^"]*)"', html):
                print(f"    -> FB link: {m.group(1)}")
    except Exception as e:
        print(f"[Startpage] Error: {e}")

# Test 3: Google with Mobile User Agent
def test_google_mobile(q):
    url = f"https://www.google.com/search?q={urllib.parse.quote(q)}&hl=en"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=7) as res:
            html = res.read().decode('utf-8', errors='ignore')
            print(f"[Google Mobile] Status: {res.status}, Len: {len(html)}")
            if "wolvega" in html.lower():
                print("  [+] FOUND WOLVEGA IN GOOGLE MOBILE!")
            links = re.findall(r'href="(https?://[^"&]*facebook\.com[^"&]*)"', html)
            print(f"  FB Links: {links}")
    except Exception as e:
        print(f"[Google Mobile] Error: {e}")

print("Testing query: 'Jordin Zwaan facebook'")
test_google_gbv("Jordin Zwaan facebook")
test_startpage("Jordin Zwaan facebook")
test_google_mobile("Jordin Zwaan facebook")
