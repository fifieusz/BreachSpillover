import urllib.request, urllib.parse, re
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'}

url = "https://drimble.nl/zoeken?q=" + urllib.parse.quote("Sjoerd Sikkema")
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("Drimble HTML len:", len(html))
        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all("div", class_=lambda c: c and "search-result" in c)
        print("Drimble search results count:", len(items))
        for it in items[:4]:
            print("  Drimble item:", it.get_text()[:100].replace("\n", " "))
except Exception as e:
    print("Drimble Error:", e)

# Also test Oozo
url_oozo = "https://www.oozo.nl/zoeken?q=" + urllib.parse.quote("Sjoerd Sikkema")
try:
    req = urllib.request.Request(url_oozo, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("Oozo HTML len:", len(html))
        soup = BeautifulSoup(html, "html.parser")
        res_items = soup.find_all("li", class_=lambda c: c and "search" in c)
        print("Oozo results count:", len(res_items))
        for it in res_items[:4]:
            print("  Oozo item:", it.get_text()[:100].replace("\n", " "))
except Exception as e:
    print("Oozo Error:", e)
