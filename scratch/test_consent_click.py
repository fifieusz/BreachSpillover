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

r1 = client.get("https://www.google.com/search?q=Jordin+Zwaan+facebook&hl=en")
soup1 = BeautifulSoup(r1.text, 'html.parser')
click_a = soup1.find('a', string=re.compile(r'click here', re.IGNORECASE))
if click_a and click_a.get('href'):
    next_url = "https://www.google.com" + click_a['href']
    print("Following click here:", next_url)
    r2 = client.get(next_url)
    print("R2 Status:", r2.status_code, "Len:", len(r2.text))
    fb_links = re.findall(r'https?://(?:www\.)?facebook\.com/[^\s"\'&<>]+', r2.text)
    print("FB links found in R2:", set(fb_links))
    if "Wolvega" in r2.text:
        print("Found 'Wolvega' in R2!")
