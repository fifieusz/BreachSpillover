from curl_cffi import requests
import urllib.parse
import re

query = 'Alje Woltjer'

# 1. Yahoo
try:
    resp = requests.get(f'https://search.yahoo.com/search?p={urllib.parse.quote(query)}', impersonate='chrome124', timeout=5)
    print('Yahoo status:', resp.status_code, 'len:', len(resp.text))
    # Look for results
    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', resp.text)
    external = [h for h, t in links if 'linkedin' in h or 'vooruit' in h or 'merlon' in h]
    print('Yahoo matches:', set(external[:5]))
except Exception as e:
    print('Yahoo error:', e)

# 2. DuckDuckGo HTML
try:
    resp = requests.post('https://html.duckduckgo.com/html/', data={'q': query}, impersonate='chrome124', timeout=5)
    print('DDG status:', resp.status_code, 'len:', len(resp.text))
    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', resp.text)
    external = [h for h, t in links if 'uddg=' in h]
    print('DDG count:', len(external))
    for h in external[:5]:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(h).query)
        print('  DDG link:', qs.get('uddg', [h])[0])
except Exception as e:
    print('DDG error:', e)

# 3. Google
try:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
    resp = requests.get(f'https://www.google.com/search?q={urllib.parse.quote(query)}', headers=headers, impersonate='chrome124', timeout=5)
    print('Google status:', resp.status_code, 'len:', len(resp.text))
    matches = re.findall(r'<a[^>]+href=["\'](/url\?q=[^"\'&]+|https://[^"\'&]+linkedin[^"\'&]+)["\']', resp.text)
    print('Google matches:', matches[:5])
except Exception as e:
    print('Google error:', e)
