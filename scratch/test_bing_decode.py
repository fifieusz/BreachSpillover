import urllib.request
import urllib.parse
import re
import base64

query = 'Yasir Kadhim'
url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=5) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# decode Bing ck url:
# format: https://www.bing.com/ck/a?!&&p=...&u=a1<base64>&ntb=1
ck_urls = re.findall(r'href="(https://www\.bing\.com/ck/a\?[^"]+)"', html)
print("Total ck_urls:", len(ck_urls))
for u in ck_urls[:5]:
    clean_u = u.replace('&amp;', '&')
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(clean_u).query)
    u_param = qs.get('u', [''])[0]
    if u_param.startswith('a1'):
        b64 = u_param[2:]
        # pad base64
        b64 += '=' * ((4 - len(b64) % 4) % 4)
        try:
            decoded = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
            print("DECODED URL:", decoded)
        except Exception as e:
            print("Error decoding:", e)
