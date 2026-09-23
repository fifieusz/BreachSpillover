import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

def test_bing(q):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode('utf-8', errors='ignore')
            print(f"Bing '{q}': Status {res.status}, Len {len(html)}")
            links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html)
            fb_links = [l[0] for l in links if "facebook.com" in l[0]]
            print(f"  Bing FB links: {fb_links[:5]}")
            if "Wolvega" in html:
                print("  Bing: 'Wolvega' found!")
    except Exception as e:
        print(f"Bing error: {e}")

def test_yahoo(q):
    url = f"https://search.yahoo.com/search?p={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode('utf-8', errors='ignore')
            print(f"Yahoo '{q}': Status {res.status}, Len {len(html)}")
            links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html)
            fb_links = [l[0] for l in links if "facebook.com" in l[0]]
            print(f"  Yahoo FB links: {fb_links[:5]}")
            if "Wolvega" in html:
                print("  Yahoo: 'Wolvega' found!")
    except Exception as e:
        print(f"Yahoo error: {e}")

test_bing('"Jordin Zwaan"')
test_bing('"Jordin Zwaan" facebook')
test_yahoo('"Jordin Zwaan"')
test_yahoo('"Jordin Zwaan" facebook')
