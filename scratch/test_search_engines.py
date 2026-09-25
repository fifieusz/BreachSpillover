import urllib.request
import urllib.parse
import json
import re

query = 'Alje Woltjer linkedin'

# Test 1: Yahoo search
try:
    url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"Yahoo: length {len(html)}")
        # find linkedin urls
        li_urls = re.findall(r'https?://[a-z]{0,3}\.?linkedin\.com/in/[a-zA-Z0-9\-_%]+', html)
        print("Yahoo LinkedIn matches:", set(li_urls))
        if "alje" in html.lower() and "woltjer" in html.lower():
            print("Yahoo contains Alje Woltjer!")
            # let's see snippets
            for m in re.finditer(r'Alje Woltjer', html, re.IGNORECASE):
                start = max(0, m.start() - 50)
                end = min(len(html), m.end() + 150)
                print("  Yahoo snippet:", re.sub(r'<[^>]+>', ' ', html[start:end]))
except Exception as e:
    print("Yahoo error:", e)

# Test 2: Qwant
try:
    url = f"https://api.qwant.com/v3/search/web?q={urllib.parse.quote(query)}&count=10&locale=en_US"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Qwant count:", len(data.get('data', {}).get('result', {}).get('items', {}).get('mainline', [])))
except Exception as e:
    print("Qwant error:", e)

# Test 3: Brave search free / web
try:
    url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"Brave: length {len(html)}")
        li_urls = re.findall(r'https?://[a-z]{0,3}\.?linkedin\.com/in/[a-zA-Z0-9\-_%]+', html)
        print("Brave LinkedIn matches:", set(li_urls))
        for m in re.finditer(r'Alje Woltjer', html, re.IGNORECASE):
            start = max(0, m.start() - 50)
            end = min(len(html), m.end() + 150)
            print("  Brave snippet:", re.sub(r'<[^>]+>', ' ', html[start:end]))
            break
except Exception as e:
    print("Brave error:", e)
