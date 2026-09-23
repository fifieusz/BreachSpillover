import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup

url = "https://www.bing.com/search?q=" + urllib.parse.quote("Jordin Zwaan facebook")
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
req = urllib.request.Request(url, headers=headers)
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')
for li in soup.find_all('li', class_='b_algo'):
    h2 = li.find('h2')
    a = h2.find('a') if h2 else None
    p = li.find('p')
    if a:
        print("Title:", a.get_text())
        print("URL:", a.get('href'))
        if p:
            print("Snippet:", p.get_text()[:120])
        print("---")
