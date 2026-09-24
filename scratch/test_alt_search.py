import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import json

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def test_engine(name, url, method="GET", data=None, headers=None):
    h = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode("utf-8", errors="ignore")
            print(f"[{name}] HTTP {r.status} - length {len(body)}")
            return body
    except Exception as e:
        print(f"[{name}] ERROR: {e}")
        return None

# 1. Mojeek
b_mojeek = test_engine("Mojeek", "https://www.mojeek.com/search?q=" + urllib.parse.quote("Sjoerd Sikkema"))
if b_mojeek:
    soup = BeautifulSoup(b_mojeek, "html.parser")
    res = soup.find_all("a", class_="ob")
    print("  Mojeek results:", len(res))
    for a in res[:3]:
        print("   ", a.get_text()[:60], "->", a.get("href"))

# 2. Swisscows
b_swiss = test_engine("Swisscows", "https://swisscows.com/en/web?query=" + urllib.parse.quote("Sjoerd Sikkema"))
if b_swiss:
    print("  Swisscows length:", len(b_swiss))

# 3. Yahoo Search with clean headers
b_yahoo = test_engine("Yahoo", "https://search.yahoo.com/search?p=" + urllib.parse.quote("Sjoerd Sikkema") + "&ei=UTF-8")
if b_yahoo:
    soup = BeautifulSoup(b_yahoo, "html.parser")
    res = soup.find_all("div", class_="algo")
    print("  Yahoo results:", len(res))
    for div in res[:3]:
        h3 = div.find("h3")
        a = h3.find("a") if h3 else None
        print("   ", a.get_text() if a else "", "->", a.get("href") if a else "")

# 4. Yandex
b_yandex = test_engine("Yandex", "https://yandex.com/search/?text=" + urllib.parse.quote("Sjoerd Sikkema"))
if b_yandex:
    print("  Yandex length:", len(b_yandex))
