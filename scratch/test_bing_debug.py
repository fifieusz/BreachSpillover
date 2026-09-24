import urllib.request, urllib.parse, re, base64

url = "https://www.bing.com/search?q=" + urllib.parse.quote("Amir Secic")
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"})
with urllib.request.urlopen(req, timeout=5) as r:
    html = r.read().decode("utf-8", errors="ignore")

blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
print(f"Blocks found: {len(blocks)}")
for i, b in enumerate(blocks[:4]):
    a_matches = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', b)
    print(f"\nBlock {i}: a_matches={len(a_matches)}")
    for href, text in a_matches[:1]:
        clean_href = href.replace("&amp;", "&")
        print("   clean_href:", clean_href)
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(clean_href).query)
        print("   qs keys:", list(qs.keys()))
        print("   u_param:", qs.get("u"))
        u_val = qs.get("u", [""])[0]
        if u_val.startswith("a1"):
            b64 = u_val[2:]
            b64 += "=" * ((4 - len(b64) % 4) % 4)
            try:
                dec = base64.urlsafe_b64decode(b64).decode("utf-8", errors="ignore")
                print("   decoded:", dec)
            except Exception as e:
                print("   decode error:", e)
