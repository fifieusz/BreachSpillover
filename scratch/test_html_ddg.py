import urllib.request
import urllib.parse
import re

url = "https://html.duckduckgo.com/html/"
data = urllib.parse.urlencode({'q': 'Yasir Kadhim'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded',
}

try:
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print('Status:', res.status, 'Len:', len(html))
        # Look for result-link
        links = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"', html)
        print('Result URLs:', len(links))
        for l in links[:5]:
            print('  *', l)
        snippets = re.findall(r'<a class="result__snippet"[^>]*>([\s\S]*?)</a>', html)
        print('Snippets:', len(snippets))
        for s in snippets[:3]:
            print('  SNIP:', re.sub(r'<[^>]+>', '', s).strip()[:100])
except Exception as e:
    print('DDG HTML Error:', e)
