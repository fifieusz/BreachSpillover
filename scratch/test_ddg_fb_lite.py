import urllib.request
import urllib.parse
import re

url = 'https://lite.duckduckgo.com/lite/'
data = urllib.parse.urlencode({'q': 'Jordin Zwaan facebook'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, timeout=6) as res:
        html = res.read().decode('utf-8', errors='ignore')
        links = re.findall(r'<a[^>]+class=[\'"]result-link[\'"][^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html)
        print("Status:", res.status, "Found:", len(links))
        for href, title in links:
            print(f"  {re.sub('<[^>]+>', '', title)} --> {href}")
except Exception as e:
    print("Error:", e)
