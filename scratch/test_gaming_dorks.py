import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

queries = [
    '"Yasir Kadhim" esports OR brawlhalla OR gaming OR tournament',
    '"Yasir" "Kadhim" brawlhalla',
    'site:esportsearnings.com "Yasir"',
    'site:liquipedia.net "Yasir Kadhim"',
    'site:liquipedia.net "Yasir"',
    'site:dashfight.com "Yasir"',
    'site:start.gg "Yasir Kadhim"',
    '"Yasir Kadhim" player OR gamertag OR alias',
]

for q in queries:
    url = 'https://www.bing.com/search?q=' + urllib.parse.quote(q)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        matches = list(re.finditer(r'(djessir|brawlhalla|esports|tournament|earnings)', html, re.I))
        print(f"[{q}] -> Matches: {len(matches)}")
        for m in matches[:3]:
            s = max(0, m.start() - 40)
            e = min(len(html), m.end() + 60)
            print(f"   Context: {html[s:e].strip()}")
    except Exception as e:
        print(f"[{q}] -> Error: {e}")
