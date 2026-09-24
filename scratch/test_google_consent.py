import urllib.request, re
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Cookie': 'SOCS=CAESHAgBEhJnd3NfMjAyNDA2MTAtMF9SQzIaAmVuIAEaBgiA_L20Bg; CONSENT=YES+'
}
req = urllib.request.Request('https://www.google.com/search?q=%22Sjoerd+Sikkema%22&hl=en', headers=headers)
h = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
soup = BeautifulSoup(h, 'html.parser')
print('Title with consent cookie:', soup.title.string if soup.title else None)

# Find search results via h3 tags
h3_tags = soup.find_all('h3')
print('Found h3 tags count:', len(h3_tags))
results = []
for h3 in h3_tags:
    parent_a = h3.find_parent('a')
    if parent_a and parent_a.get('href'):
        href = parent_a['href']
        if href.startswith('http') and 'google.com' not in href:
            results.append((h3.get_text(), href))

print('Clean Google search results count:', len(results))
for t, u in results[:8]:
    print(f'  {t} -> {u}')
