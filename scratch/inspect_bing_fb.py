import urllib.request
import urllib.parse
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def inspect_block(query):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=8) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    blocks = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)
    print(f"Blocks: {len(blocks)}")
    for i, b in enumerate(blocks[:6]):
        # Extract any href inside <h2>
        h2 = re.search(r'<h2[^>]*>(.*?)</h2>', b, re.DOTALL)
        if h2:
            a = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h2.group(1), re.DOTALL)
            if a:
                href = a.group(1)
                title = re.sub(r'<[^>]+>', '', a.group(2)).strip()
                # snippet
                cap = re.search(r'<div class="b_caption"[^>]*>(.*?)</div>', b, re.DOTALL)
                snip = re.sub(r'<[^>]+>', '', cap.group(1)).strip() if cap else ""
                clean_title = title.encode('ascii', 'replace').decode('ascii')
                clean_snip = snip.encode('ascii', 'replace').decode('ascii')
                print(f"[{i+1}] {clean_title}")
                print(f"    URL: {href}")
                print(f"    SNIP: {clean_snip[:140]}")

if __name__ == "__main__":
    inspect_block("Jordin Zwaan facebook")
