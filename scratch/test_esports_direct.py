import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

queries = ["Yasir", "Kadhim", "Jordin", "Zwaan", "Djessir"]

for name in queries:
    url = "https://www.esportsearnings.com/search?search=" + urllib.parse.quote(name)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"[{name}] Status: {resp.status}, Len: {len(html)}")
            # Find players table or links
            players = re.findall(r'<a href="(/players/[^"]+)"[^>]*>([\s\S]*?)</a>', html)
            print(f"  Players found ({len(players)}):")
            for p_url, p_name in players[:5]:
                clean_p = re.sub(r'<[^>]+>', ' ', p_name).strip()
                print(f"    * {clean_p} -> https://www.esportsearnings.com{p_url}")
    except Exception as e:
        print(f"[{name}] Error: {e}")
