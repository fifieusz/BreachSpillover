import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': 'CONSENT=YES+shp.gws-20210601-0-RC2.en+FX+424;'
}

url = "https://www.google.com/search?q=" + urllib.parse.quote("Jordin Zwaan facebook")
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=5.0) as resp:
    html = resp.read().decode('utf-8', errors='ignore')
    # Find all /url?q= or direct links
    urls = re.findall(r'/url\?q=([^&"]+)', html)
    print("Found /url?q= count:", len(urls))
    for u in urls[:15]:
        decoded = urllib.parse.unquote(u)
        print("  ->", decoded)
    
    # Also find any hrefs
    all_hrefs = re.findall(r'href="([^"]+)"', html)
    print("\nTotal hrefs:", len(all_hrefs))
    for h in all_hrefs:
        if any(w in h.lower() for w in ["facebook", "linkedin", "jordin", "zwaan"]):
            print("  Special href:", h)
