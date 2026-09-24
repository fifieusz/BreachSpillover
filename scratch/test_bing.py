import urllib.request
import urllib.parse
import re

query = 'Yasir Kadhim'
url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    print('HTML length:', len(html))
    print('b_algo count:', html.count('b_algo'))
    
    # Check current regex:
    # re.findall(r'<li class="b_algo".*?<h2>.*?<a href="([^"]+)".*?>(.*?)</a>.*?<p[^>]*>(.*?)</p>', html, re.DOTALL)
    blocks = re.findall(r'<li class="b_algo".*?<h2>.*?<a href="([^"]+)".*?>(.*?)</a>.*?<p[^>]*>(.*?)</p>', html, re.DOTALL)
    print('Current regex blocks:', len(blocks))
    
    # Check looser regex:
    links = re.findall(r'<li class="b_algo"[^>]*>[\s\S]*?<h2>[\s\S]*?<a\s+href="([^"]+)"[^>]*>([\s\S]*?)</a>', html)
    print('Looser regex links:', len(links))
    for h, t in links[:5]:
        clean_t = re.sub(r'<[^>]+>', '', t).strip()
        print(' -', clean_t, '->', h)
except Exception as e:
    print('Error:', e)
