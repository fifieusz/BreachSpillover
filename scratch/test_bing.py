from curl_cffi import requests
import re

resp = requests.get('https://www.bing.com/search?q=Alje+Woltjer', impersonate='chrome124', timeout=5)
links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', resp.text)
for href, text in links[:15]:
    clean_text = re.sub(r'<[^>]+>', '', text).strip()
    print(href[:60], '->', clean_text[:40])
