import urllib.request, re, sys
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://drimble.nl/zoeken/?q=82224056'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print('Drimble Status:', r.status)
        title = re.search(r'<title>(.*?)</title>', html)
        print('Title:', title.group(1) if title else 'No title')
        for match in re.findall(r'<a[^>]*href="(/bedrijf/[^"]+)"[^>]*>(.*?)</a>', html):
            print('  Bedrijf link:', match[0], '|', re.sub(r'<[^>]+>', '', match[1]).strip())
except Exception as e:
    print('Error:', e)
