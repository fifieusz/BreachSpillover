import urllib.request
import urllib.parse
import re

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

# find the closing of first <li class="b_algo" or next <li class="b_algo"
pos = html.find('class="b_algo"')
next_pos = html.find('class="b_algo"', pos + 20)
chunk = html[pos:next_pos if next_pos != -1 else pos+3000]

# remove huge base64 or inline styles
clean_chunk = re.sub(r'<style[\s\S]*?</style>', '', chunk)
clean_chunk = re.sub(r'<script[\s\S]*?</script>', '', clean_chunk)
print("Clean chunk:")
print(clean_chunk[:1500])
