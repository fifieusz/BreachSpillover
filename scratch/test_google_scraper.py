import urllib.request, urllib.parse, re
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

url = "https://www.google.com/search?q=" + urllib.parse.quote('"Sjoerd Sikkema"') + "&hl=en&gl=us"
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=6) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("Google HTTP Status:", resp.status, "HTML len:", len(html))
        soup = BeautifulSoup(html, "html.parser")
        # Find Google search result blocks
        results = []
        for g in soup.find_all("div", class_=lambda c: c and ("g" in c.split() or "tF2Cxc" in c)):
            h3 = g.find("h3")
            a = g.find("a")
            snip = g.find("div", class_=lambda c: c and ("VwiC3b" in c or "yXK7lf" in c))
            if h3 and a:
                results.append({
                    "title": h3.get_text(),
                    "url": a.get("href"),
                    "snippet": snip.get_text() if snip else ""
                })
        print(f"Found {len(results)} Google search results:")
        for r in results[:5]:
            print(f"  Title: {r['title']}")
            print(f"  URL: {r['url']}")
            print(f"  Snippet: {r['snippet'][:120]}\n")
except Exception as e:
    print("Google error:", e)
