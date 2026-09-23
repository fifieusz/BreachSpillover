import urllib.request
import urllib.parse
import re

url = "https://www.startpage.com/sp/search?query=" + urllib.parse.quote('site:facebook.com "Jordin Zwaan"')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"Status: {resp.status}, Length: {len(html)}")
        # Check for results
        results = re.findall(r'<a class="result-link"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', html)
        print(f"Result links: {len(results)}")
        for href, text in results:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            print(" ->", href, "|", clean_text)
        
        # Also look for any result titles
        titles = re.findall(r'<h2[^>]*>[\s\S]*?<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>', html)
        print(f"H2 links: {len(titles)}")
        for href, text in titles:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            print(" ->", href, "|", clean_text)

        # Print all external links in html
        ext = set(re.findall(r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[^\s"\'<>]*', html))
        relevant = [l for l in ext if any(k in l.lower() for k in ["facebook", "zwaan", "jordin"])]
        print(f"Relevant links in page ({len(relevant)}):", relevant)
except Exception as e:
    print("Error:", e)
