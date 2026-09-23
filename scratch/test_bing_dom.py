import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

url = "https://www.bing.com/search?q=" + urllib.parse.quote("Jordin Zwaan facebook")
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=5.0) as resp:
    html = resp.read().decode('utf-8', errors='ignore')
    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>', html)
    print(f"Total links found: {len(links)}")
    for href, text in links:
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if any(k in href.lower() or k in clean_text.lower() for k in ["jordin", "zwaan", "facebook", "deltion", "wolvega"]):
            print(f"Match: href={href} | text={clean_text[:60]}")
