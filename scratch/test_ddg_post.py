import urllib.request, urllib.parse, re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = urllib.parse.urlencode({"q": "Amir Secic"}).encode("utf-8")
req = urllib.request.Request("https://html.duckduckgo.com/html/", data=data, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        html = r.read().decode("utf-8", errors="ignore")
        print("HTML len:", len(html))
        # Look for result__title and result__snippet
        titles = re.findall(r'<a[^>]+class="result__url"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', html)
        snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>([\s\S]*?)</a>', html)
        print(f"Titles found: {len(titles)}, Snippets: {len(snippets)}")
        for i in range(min(len(titles), len(snippets), 5)):
            url, raw_title = titles[i]
            # DDG url decoding: uddg=
            if "uddg=" in url:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                url = qs.get("uddg", [url])[0]
            print(f"[{i+1}] {re.sub(r'<[^>]+>', '', raw_title).strip()} -> {url}")
            print(f"    {re.sub(r'<[^>]+>', '', snippets[i]).strip()[:120]}")
except Exception as e:
    print("Error:", e)
