import urllib.request
import urllib.parse
import re

url = "https://lite.duckduckgo.com/lite/"
data = urllib.parse.urlencode({'q': 'site:facebook.com Jordin Zwaan'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://lite.duckduckgo.com/'
}
req = urllib.request.Request(url, data=data, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print("Status:", res.status, "Len:", len(html))
        a_tags = re.findall(r'<a[^>]+class=[\'"]result-link[\'"][^>]*>.*?</a>', html, re.DOTALL)
        snip_tags = re.findall(r'<td[^>]+class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>', html, re.DOTALL)
        print("Results:", len(a_tags))
        for i in range(min(len(a_tags), len(snip_tags))):
            tag = a_tags[i]
            href = re.search(r'href=[\'"]([^\'"]+)[\'"]', tag).group(1)
            title = re.sub(r'<[^>]+>', '', tag).strip()
            print(f"  {title} | {href}")
except Exception as e:
    print("Error:", e)
