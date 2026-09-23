import httpx
import re
from bs4 import BeautifulSoup

client = httpx.Client(
    follow_redirects=True,
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    },
    timeout=10.0
)

# Fetch google search
r = client.get("https://www.google.com/search?q=Jordin+Zwaan+facebook&hl=en")
print("Status:", r.status_code, "URL:", r.url)
soup = BeautifulSoup(r.text, 'html.parser')
forms = soup.find_all('form')
print("Forms found:", len(forms))
for f in forms:
    action = f.get('action')
    print("Form action:", action)
    inputs = {inp.get('name'): inp.get('value') for inp in f.find_all('input') if inp.get('name')}
    print("Inputs:", inputs)
