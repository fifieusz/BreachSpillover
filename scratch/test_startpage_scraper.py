import urllib.request, urllib.parse
from bs4 import BeautifulSoup

url = "https://www.startpage.com/sp/search"
data = urllib.parse.urlencode({
    "query": '"Sjoerd Sikkema"',
    "cat": "web",
    "language": "english"
}).encode("utf-8")

req = urllib.request.Request(url, data=data, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
})

try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        results = soup.find_all("div", class_=lambda c: c and "result" in c)
        print("Startpage results count:", len(results))
        for r in results[:5]:
            title = r.find("h2")
            link = r.find("a", class_=lambda c: c and "result-link" in c or "title" in c)
            snip = r.find("p")
            print("  Title:", title.get_text() if title else "None")
            print("  Link:", link.get("href") if link else "None")
            print("  Snippet:", snip.get_text() if snip else "None")
            print()
except Exception as e:
    print("Startpage error:", e)
