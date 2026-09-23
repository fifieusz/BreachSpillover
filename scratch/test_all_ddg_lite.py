import urllib.request
import urllib.parse
import re

url = "https://lite.duckduckgo.com/lite/"
data = urllib.parse.urlencode({'q': 'Jordin Zwaan facebook'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://lite.duckduckgo.com/'
}
req = urllib.request.Request(url, data=data, headers=headers)
with urllib.request.urlopen(req, timeout=8) as res:
    html = res.read().decode('utf-8', errors='ignore')

# Match <a> tags with class 'result-link'
a_tags = re.findall(r'<a[^>]+class=[\'"]result-link[\'"][^>]*>.*?</a>', html, re.DOTALL)
snippets = re.findall(r'<td[^>]+class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>', html, re.DOTALL)

print(f"a_tags: {len(a_tags)}, Snippets: {len(snippets)}")
for i in range(min(len(a_tags), len(snippets))):
    tag = a_tags[i]
    href_m = re.search(r'href=[\'"]([^\'"]+)[\'"]', tag)
    href = href_m.group(1) if href_m else ""
    title = re.sub(r'<[^>]+>', '', tag).strip()
    snip = re.sub(r'<[^>]+>', ' ', snippets[i])
    snip = re.sub(r'\s+', ' ', snip).strip()
    print(f"\n[{i+1}] {title}")
    print(f"    URL: {href}")
    print(f"    Snippet: {snip[:200]}")
