import urllib.request
import re
from bs4 import BeautifulSoup

url = "https://jordinzwaan.jouwweb.nl/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=5) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print("Status:", res.status, "Len:", len(html))
        soup = BeautifulSoup(html, 'html.parser')
        print("Title:", soup.title.string if soup.title else "")
        links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
        print("Links:", set(links))
        text = re.sub(r'\s+', ' ', soup.get_text()).strip()
        print("Text sample:", text[:400])
        fb_matches = re.findall(r'facebook\.com/[^\s"\'<>]+', html)
        print("FB matches:", set(fb_matches))
except Exception as e:
    print("Error:", e)
