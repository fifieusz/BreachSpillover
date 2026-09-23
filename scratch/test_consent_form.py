import httpx
from bs4 import BeautifulSoup
import re

client = httpx.Client(
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    },
    follow_redirects=True
)

r = client.get("https://www.google.com/search?q=Jordin+Zwaan+facebook&hl=en")
print("URL:", r.url)
print("Status:", r.status_code)
print("Len:", len(r.text))

# Search for facebook links or Wolvega
fb_links = re.findall(r'https?://(?:www\.)?facebook\.com/[^\s"\'&<>]+', r.text)
print("FB links found:", set(fb_links))

if "Wolvega" in r.text:
    print("Found 'Wolvega' in r.text!")

# Check if there are search result elements
soup = BeautifulSoup(r.text, 'html.parser')
print("Title:", soup.title.string if soup.title else "No title")
for a in soup.find_all('a'):
    href = a.get('href', '')
    if 'facebook.com' in href or 'jordin' in href.lower():
        print("  Anchor:", href, "-->", a.get_text()[:60])
