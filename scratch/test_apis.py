import urllib.request, urllib.parse, json

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. DuckDuckGo Instant Answer API
try:
    url = "https://api.duckduckgo.com/?q=Sjoerd+Sikkema&format=json&no_html=1"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=3) as resp:
        d = json.loads(resp.read())
        print("DDG Abstract:", d.get("AbstractText"), "Heading:", d.get("Heading"), "Related:", len(d.get("RelatedTopics", [])))
except Exception as e:
    print("DDG Instant Answer error:", e)

# 2. Wikipedia Search API
try:
    url = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Sjoerd+Sikkema&format=json"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=3) as resp:
        d = json.loads(resp.read())
        print("Wikipedia hits:", d.get("query", {}).get("searchinfo", {}).get("totalhits"))
except Exception as e:
    print("Wikipedia error:", e)
