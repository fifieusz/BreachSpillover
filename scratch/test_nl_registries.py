import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7'
}

def test_url(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"URL: {url} -> Status: {resp.status}, Len: {len(html)}")
            for term in ['kadhim', 'kadim', 'jy collective', 'bergschenhoek']:
                cnt = len(re.findall(term, html, re.I))
                if cnt > 0:
                    print(f"  Keyword '{term}': {cnt} occurrences")
    except Exception as e:
        print(f"URL: {url} -> Error: {e}")

test_url("https://oozo.nl/zoeken?q=" + urllib.parse.quote("Kadhim"))
test_url("https://oozo.nl/bedrijven/bergschenhoek")
test_url("https://bedrijvenmonitor.info/zoeken?q=" + urllib.parse.quote("JY Collective"))
test_url("https://openkvk.nl/zoeken/" + urllib.parse.quote("JY Collective"))
