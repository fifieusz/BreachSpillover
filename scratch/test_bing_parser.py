import urllib.request, urllib.parse, re

url = 'https://www.bing.com/search?q=' + urllib.parse.quote('Sjoerd Sikkema')
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml'})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

tags = re.findall(r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>', html)
print('Found b_algo tags:', tags)

# Try with BeautifulSoup4 which handles nested li tags properly
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
algos = soup.find_all('li', class_=lambda c: c and 'b_algo' in c)
print(f'BS4 found {len(algos)} b_algo elements:')
for a in algos:
    h2 = a.find('h2')
    link = h2.find('a') if h2 else None
    snippet = a.find('p')
    title = link.get_text() if link else 'No Title'
    href = link.get('href') if link else 'No Href'
    snip_text = snippet.get_text() if snippet else ''
    print(f'  Title: {title}\n  Href: {href}\n  Snip: {snip_text[:100]}\n')
