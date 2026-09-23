import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

# Test if we can find the exact URL by testing common variants
urls = [
    "https://www.facebook.com/people/Jordin-Zwaan/100009907727146/",
    "https://www.facebook.com/Jordin-Zwaan-100009907727146",
    "https://www.facebook.com/jordin.zwaan"
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as res:
            print(f"URL {u} -> Status {res.status}")
            html = res.read().decode('utf-8', errors='ignore')
            print("  Title:", re.findall(r'<title>(.*?)</title>', html))
            if "Wolvega" in html:
                print("  Wolvega in FB page!")
    except urllib.error.HTTPError as e:
        print(f"URL {u} -> HTTP {e.code}")
    except Exception as e:
        print(f"URL {u} -> Error {e}")
