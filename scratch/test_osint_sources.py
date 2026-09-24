import urllib.request, urllib.parse, json

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}

print("=== 1. Chess.com API ===")
try:
    req = urllib.request.Request("https://api.chess.com/pub/player/sjoerdsikkema", headers=headers)
    with urllib.request.urlopen(req, timeout=4) as resp:
        print("Chess.com player:", json.loads(resp.read()))
except Exception as e:
    print("Chess.com error:", e)

print("\n=== 2. GitHub Users Search API ===")
try:
    req = urllib.request.Request("https://api.github.com/search/users?q=sjoerdsikkema", headers=headers)
    with urllib.request.urlopen(req, timeout=4) as resp:
        gh_data = json.loads(resp.read())
        print("GitHub users count:", gh_data.get("total_count"))
        for u in gh_data.get("items", [])[:3]:
            print("  Login:", u.get("login"), "URL:", u.get("html_url"))
except Exception as e:
    print("GitHub search error:", e)

print("\n=== 3. Yahoo Search ===")
try:
    req = urllib.request.Request("https://search.yahoo.com/search?p=Sjoerd+Sikkema", headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("Yahoo HTML len:", len(html))
        import re
        links = re.findall(r'<a[^>]*class="[^"]*d-ib[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', html)
        print("Yahoo links count:", len(links))
        for l, t in links[:3]:
            print("  ", re.sub(r'<[^>]+>', '', t).strip(), "->", l)
except Exception as e:
    print("Yahoo error:", e)

print("\n=== 4. Brave Search ===")
try:
    req = urllib.request.Request("https://search.brave.com/search?q=Sjoerd+Sikkema", headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("Brave HTML len:", len(html))
        import re
        titles = re.findall(r'<div class="title[^"]*"[^>]*>([\s\S]*?)</div>', html)
        print("Brave titles count:", len(titles))
        for t in titles[:3]:
            print("  ", re.sub(r'<[^>]+>', '', t).strip())
except Exception as e:
    print("Brave error:", e)

print("\n=== 5. OpenCorporates Search ===")
try:
    req = urllib.request.Request("https://api.opencorporates.com/v0.4/officers/search?q=Sjoerd+Sikkema", headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        oc_data = json.loads(resp.read())
        officers = oc_data.get("results", {}).get("officers", [])
        print("OpenCorporates officers count:", len(officers))
        for o in officers[:3]:
            off = o.get("officer", {})
            print("  Officer:", off.get("name"), "Company:", off.get("company", {}).get("name"), "Jurisdiction:", off.get("jurisdiction_code"))
except Exception as e:
    print("OpenCorporates error:", e)
