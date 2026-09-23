import urllib.request
import urllib.parse
import re

url = "https://html.duckduckgo.com/html/"
data = urllib.parse.urlencode({'q': 'Jordin Zwaan facebook'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://duckduckgo.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}
req = urllib.request.Request(url, data=data, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        print("Status:", resp.status)
        html = resp.read().decode('utf-8', errors='ignore')
        print("HTML length:", len(html))
        # Look for facebook links
        links = re.findall(r'href="([^"]*facebook[^"]*)"', html, re.I)
        print("Found FB links:", links)
        if "If this error persists, please let us know" in html or "anomaly-modal" in html:
            print("DDG challenged with anomaly/bot block!")
        else:
            print("First 300 chars:", html[:300])
except Exception as e:
    print("Error:", e)
