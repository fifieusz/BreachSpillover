import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7'
}

def inspect_matches(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    print(f"=== {url} ===")
    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>', html)
    for href, text in links:
        clean = re.sub(r'<[^>]+>', ' ', text).strip()
        if any(k in clean.lower() or k in href.lower() for k in ['kadhim', 'kadim', 'jy collective', 'bergschenhoek']):
            print("  Link:", href, "->", clean)

inspect_matches("https://oozo.nl/zoeken?q=" + urllib.parse.quote("Kadhim"))
inspect_matches("https://oozo.nl/zoeken?q=" + urllib.parse.quote("JY Collective"))
inspect_matches("https://bedrijvenmonitor.info/zoeken?q=" + urllib.parse.quote("JY Collective"))
