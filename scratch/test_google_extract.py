import urllib.request
import urllib.parse
import re

q = urllib.parse.quote('"Yasir Ashraf" Kadhim')
url = f"https://www.google.com/search?q={q}&hl=en&num=10"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': 'SOCS=CAESHAgBEhJnd3NfMjAyNDA3MjMtMF9SQzIaAmVuIAEaBgiA_L20Bg'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=5) as res:
    html = res.read().decode('utf-8', errors='ignore')

# Search for any https links that are not google
all_hrefs = re.findall(r'href="(https?://[^"&]+)"', html)
print('Total hrefs:', len(all_hrefs))
non_google = [h for h in all_hrefs if 'google.com' not in h and 'gstatic.com' not in h]
print('Non-google hrefs:', len(non_google))
for h in set(non_google)[:15]:
    print('  *', h)
