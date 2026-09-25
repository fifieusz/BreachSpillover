import urllib.request, re, urllib.parse, sys
sys.stdout.reconfigure(encoding='utf-8')

def test_ddg(q):
    url = 'https://html.duckduckgo.com/html/'
    data = urllib.parse.urlencode({'q': q}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            html = r.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'<a class="result__snippet"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
        print(f"DDG '{q}' matches: {len(matches)}")
        for href, snip in matches[:3]:
            print("  URL:", href[:80])
            print("  Snip:", re.sub(r'<[^>]+>', '', snip)[:120])
    except Exception as e:
        print(f"DDG error for {q}: {e}")

test_ddg('Alje Woltjer')
test_ddg('"Alje Woltjer"')
test_ddg('site:linkedin.com "Alje Woltjer"')
test_ddg('alje.woltjer@vooruit.nl')
