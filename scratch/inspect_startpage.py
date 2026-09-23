import urllib.request
import urllib.parse
import re

url = "https://www.startpage.com/sp/search"
data = urllib.parse.urlencode({'query': 'Jordin Zwaan facebook'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://www.startpage.com/'
}
req = urllib.request.Request(url, data=data, headers=headers)
with urllib.request.urlopen(req, timeout=8) as res:
    html = res.read().decode('utf-8', errors='ignore')

print(f"Startpage len: {len(html)}")
# print all result links
links = re.findall(r'<a[^>]+class="[^"]*result[^"]*"[^>]+href="([^"]+)"', html)
print(f"Links count: {len(links)}")
for l in links[:8]:
    print(" ", l)

if "wolvega" in html.lower():
    print("FOUND WOLVEGA IN STARTPAGE!")
else:
    print("Wolvega not in startpage")
