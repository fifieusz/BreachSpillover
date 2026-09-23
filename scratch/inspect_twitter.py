import urllib.request
import re

url = "https://x.com/jordinzwaan"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})
try:
    with urllib.request.urlopen(req, timeout=5) as res:
        html = res.read().decode('utf-8', errors='ignore')
        title = re.search(r'<title>(.*?)</title>', html)
        print("Title:", title.group(1) if title else "None")
        meta = re.findall(r'<meta[^>]*>', html)
        for m in meta[:15]:
            print("Meta:", m)
except Exception as e:
    print("Error:", e)
