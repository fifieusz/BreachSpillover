import urllib.request
import urllib.parse
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

req = urllib.request.Request('https://www.bing.com/search?q=' + urllib.parse.quote('site:facebook.com "Jordin Zwaan"'), headers=headers)
with urllib.request.urlopen(req) as res:
    html = res.read().decode('utf-8', errors='ignore')
    all_links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html)
    print(f"Total links in Bing: {len(all_links)}")
    for href, text in all_links:
        if "facebook" in href.lower() or "zwaan" in href.lower() or "zwaan" in text.lower():
            print("Link:", href, "-->", re.sub(r'<[^>]+>', '', text)[:80])
