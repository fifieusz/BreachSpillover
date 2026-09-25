import urllib.request, re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Cookie': 'SOCS=CAESHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiA_LymBg'
}
req = urllib.request.Request('https://www.google.com/search?q=Jordin+Zwaan+linkedin', headers=headers)
with urllib.request.urlopen(req, timeout=5) as r:
    html = r.read().decode('utf-8', errors='ignore')

# Google results usually have <a jsname="..." href="url"><h3 ...>title</h3>
matches = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>[\s\S]*?<h3[^>]*>(.*?)</h3>', html)
print('Google matches:', len(matches))
for href, title in matches:
    clean_title = re.sub(r'<[^>]+>', '', title)
    if 'google.com' not in href:
        print(' ', href, '|', clean_title)
