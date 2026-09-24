import urllib.request
import urllib.parse
import traceback
import base64
import re
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

print("--- Testing DDG Lite ---")
try:
    data = urllib.parse.urlencode({"q": "Sjoerd Sikkema"}).encode("utf-8")
    req = urllib.request.Request(
        "https://lite.duckduckgo.com/lite/",
        data=data,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        html = r.read().decode("utf-8", errors="ignore")
        print("DDG Lite status:", r.status, "len:", len(html))
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", class_="result-link")
        print("DDG Lite result-links found:", len(links))
        if len(links) == 0:
            print("Snippet of DDG Lite html:", html[:400])
except Exception as e:
    print("DDG Lite error:", e)

print("\n--- Testing Bing ---")
try:
    url = "https://www.bing.com/search?q=" + urllib.parse.quote("Sjoerd Sikkema")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=5) as r:
        html = r.read().decode("utf-8", errors="ignore")
        print("Bing status:", r.status, "len:", len(html))
        soup = BeautifulSoup(html, "html.parser")
        results = soup.find_all("li", class_="b_algo")
        print("Bing b_algo found:", len(results))
        for res in results[:3]:
            h2 = res.find("h2")
            a = h2.find("a") if h2 else None
            p = res.find("p")
            print("  Title:", a.get_text() if a else "No title")
            print("  Href:", a["href"] if a else "No href")
            print("  Snippet:", p.get_text()[:80] if p else "No snippet")
except Exception as e:
    print("Bing error:", e)

print("\n--- Testing DuckDuckGo Search Package (ddgs) ---")
try:
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.text("Sjoerd Sikkema", max_results=5))
        print("ddgs library results:", len(results))
        for r in results:
            print("  ", r.get("title"), "->", r.get("href"))
except Exception as e:
    print("ddgs library error:", e)

print("\n--- Testing googlesearch-python ---")
try:
    from googlesearch import search
    g_res = list(search("Sjoerd Sikkema", num_results=5, advanced=True))
    print("googlesearch results:", len(g_res))
    for r in g_res:
        print("  ", r.title, "->", r.url)
except Exception as e:
    print("googlesearch error:", e)
