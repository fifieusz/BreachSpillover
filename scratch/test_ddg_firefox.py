import urllib.request
import urllib.parse
import time

url = "https://html.duckduckgo.com/html/"
data = urllib.parse.urlencode({'q': 'Jordin Zwaan'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://html.duckduckgo.com',
    'Referer': 'https://html.duckduckgo.com/'
}
start = time.time()
try:
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=12.0) as resp:
        elapsed = time.time() - start
        print(f"Success in {elapsed:.2f}s! Status: {resp.status}")
        content = resp.read().decode('utf-8', errors='ignore')
        print(f"Content length: {len(content)}")
        import re
        titles = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', content)
        print("Found titles:", len(titles))
        for t in titles[:5]:
            print(" -", re.sub(r'<[^>]+>', '', t))
except Exception as e:
    print(f"Failed in {time.time() - start:.2f}s: {e}")
