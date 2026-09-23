import urllib.request
import urllib.parse
import re

url = "https://www.google.com/search?q=" + urllib.parse.quote("Jordin Zwaan facebook") + "&hl=en"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Cookie': 'SOCS=CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjQwNjA5LjA2X3AwGgJlbhACGgYIgP-vswY'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print("Status:", res.status, "Len:", len(html))
        print("Title:", re.findall(r'<title>(.*?)</title>', html))
        # Look for search result links
        links = re.findall(r'<a[^>]+href="(/url\?q=[^"]+|https?://[^"]+)"[^>]*>(.*?)</a>', html)
        print("Links count:", len(links))
        for href, text in links[:15]:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            if "google" not in href or "/url?q=" in href:
                print(f"  {clean_text[:40]} --> {href[:80]}")
        fb = re.findall(r'https?://(?:www\.)?facebook\.com/[^\s"\'&<>]+', html)
        print("FB links found:", set(fb))
        if "Wolvega" in html:
            print("Found Wolvega in Google HTML!")
except Exception as e:
    print("Error:", e)
