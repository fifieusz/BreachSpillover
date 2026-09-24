import urllib.request, urllib.parse, re

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}

print("--- Testing Startpage ---")
try:
    url = "https://www.startpage.com/sp/search?query=" + urllib.parse.quote("Amir Secic")
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as r:
        html = r.read().decode("utf-8", errors="ignore")
        print("Startpage len:", len(html))
        # Look for result titles / links
        links = re.findall(r'href="([^"]+)"[^>]*class="[^"]*result-link', html)
        print("Startpage links found:", len(links), links[:3])
except Exception as e:
    print("Startpage error:", e)

print("--- Testing Bing with explicit query ---")
try:
    url = "https://www.bing.com/search?q=" + urllib.parse.quote('"Amir Secic"') + "&setlang=en"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as r:
        html = r.read().decode("utf-8", errors="ignore")
        blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
        print("Bing blocks for '\"Amir Secic\"':", len(blocks))
        for b in blocks[:3]:
            h2 = re.search(r'<h2[^>]*>([\s\S]*?)</h2>', b)
            if h2:
                print("  Bing title:", re.sub(r'<[^>]+>', '', h2.group(1)).strip()[:80])
except Exception as e:
    print("Bing error:", e)
