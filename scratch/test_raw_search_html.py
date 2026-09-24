import urllib.request, urllib.parse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

# 1. DuckDuckGo Lite
url_ddg = "https://lite.duckduckgo.com/lite/"
data = urllib.parse.urlencode({"q": "Sjoerd Sikkema"}).encode("utf-8")
try:
    req = urllib.request.Request(url_ddg, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("DDG Lite HTTP Status:", resp.status, "HTML len:", len(html))
        print("DDG Snippet:", html[:500].replace("\n", " "))
except Exception as e:
    print("DDG error:", e)

# 2. Bing Search
url_bing = "https://www.bing.com/search?q=" + urllib.parse.quote("Sjoerd Sikkema")
try:
    req = urllib.request.Request(url_bing, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("\nBing HTTP Status:", resp.status, "HTML len:", len(html))
        print("Bing Snippet:", html[:500].replace("\n", " "))
except Exception as e:
    print("Bing error:", e)

# 3. DuckDuckGo HTML
url_ddg_html = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote("Sjoerd Sikkema")
try:
    req = urllib.request.Request(url_ddg_html, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("\nDDG HTML Status:", resp.status, "HTML len:", len(html))
        print("DDG HTML Snippet:", html[:500].replace("\n", " "))
except Exception as e:
    print("DDG HTML error:", e)
