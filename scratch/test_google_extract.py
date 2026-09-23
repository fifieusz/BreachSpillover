import urllib.request
import urllib.parse
import re

q = urllib.parse.quote('Jordin Zwaan facebook')
url = f"https://www.google.com/search?q={q}&hl=en&num=10"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=8) as res:
    html = res.read().decode('utf-8', errors='ignore')

print(f"Google status: {res.status}, len: {len(html)}")

# Find all links
links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
print(f"Total links: {len(links)}")
for href, title in links:
    if "facebook.com" in href or "jordin" in href.lower() or "zwaan" in href.lower():
        clean_title = re.sub(r'<[^>]+>', '', title).strip()
        print(f"  * HREF: {href}")
        print(f"    Title: {clean_title}")

# Search for Wolvega
if "wolvega" in html.lower():
    print("\n[+] FOUND 'WOLVEGA' in Google HTML!")
    idx = html.lower().find("wolvega")
    print("Snippet around Wolvega:")
    print(html[max(0, idx-200):min(len(html), idx+300)])
else:
    print("\n[-] 'Wolvega' not found in HTML")
