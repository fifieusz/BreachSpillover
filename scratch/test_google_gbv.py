import urllib.request
import urllib.parse
import re

url = "https://www.google.com/search?q=" + urllib.parse.quote("Jordin Zwaan facebook") + "&hl=en&gbv=1"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print("Status:", res.status, "Len:", len(html))
        print("Title:", re.findall(r'<title>(.*?)</title>', html))
        # Look for facebook links
        links = re.findall(r'href=["\'](/url\?q=[^"\']+|https?://[^"\']+)["\']', html)
        print("Total links:", len(links))
        for l in links:
            if "facebook" in l:
                print("  FB:", l)
            if "wolvega" in l.lower():
                print("  Wolvega in link:", l)
        if "Wolvega" in html:
            print("FOUND WOLVEGA IN HTML!")
except Exception as e:
    print("Error:", e)
