import urllib.request, urllib.parse, re
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8'
}

queries = ['Sjoerd Sikkema', 'sjoerdsikkema']

for q in queries:
    print(f"\n=== Bing Search for: {q} ===")
    url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}&setlang=en&cc=us"
    req = urllib.request.Request(url, headers=headers)
    try:
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        algos = soup.find_all('li', class_=lambda c: c and 'b_algo' in c)
        print(f"Found {len(algos)} b_algo elements:")
        for a in algos:
            h2 = a.find('h2')
            link = h2.find('a') if h2 else None
            p = a.find('p')
            title = link.get_text() if link else ''
            href = link.get('href') if link else ''
            snip = p.get_text() if p else ''
            print(f"  Title: {title}\n  Href: {href[:90]}...\n  Snip: {snip[:80]}...\n")
    except Exception as e:
        print("Error:", e)
