import urllib.request
import re
from bs4 import BeautifulSoup

url = "https://jordinzwaan2016.wixsite.com/portfolio"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')
print("Title:", soup.title.string if soup.title else "No title")

# All links
links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
print("All links in portfolio:")
for l in set(links):
    print("  Link:", l)

# All text
text = soup.get_text(separator=' ')
clean_text = re.sub(r'\s+', ' ', text).strip()
print("\nPage text sample:")
print(clean_text[:500])

# Search for Facebook or social in page source
print("\nMentions of 'facebook' in source:", len(re.findall(r'facebook', html, re.IGNORECASE)))
for m in re.finditer(r'facebook[^\s"\'<>]*', html, re.IGNORECASE):
    print("  FB match:", m.group(0))

# Search for Wolvega
for m in re.finditer(r'[^.]{0,60}Wolvega[^.]{0,60}', clean_text, re.IGNORECASE):
    print("  Wolvega match:", m.group(0))
