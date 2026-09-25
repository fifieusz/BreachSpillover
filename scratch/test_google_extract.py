from curl_cffi import requests
import re

r = requests.get('https://www.google.com/search?q=Alje+Woltjer+linkedin', impersonate='chrome124')
for m in re.finditer(r'linkedin', r.text, re.IGNORECASE):
    idx = m.start()
    snippet = r.text[max(0, idx - 100):min(len(r.text), idx + 200)]
    print('--- MATCH ---')
    print(snippet)
