import urllib.request
import urllib.parse
import re

url = "https://www.google.com/search?q=" + urllib.parse.quote("Jordin Zwaan") + "&hl=en"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': 'SOCS=CAESHAgBEhJnd3NfMjAyNDA2MTAtMF9SQzIaAmVuIAEaBgiA_L20Bg; CONSENT=YES+cb.20230531-04-p0.en+FX+999'
}

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as res:
    html = res.read().decode('utf-8', errors='ignore')
    # Look for hrefs that look like search results
    print("Title:", re.findall(r'<title>(.*?)</title>', html))
    # google search results typically have /url?q= or href="https://
    all_links = re.findall(r'href="(/url\?q=[^"]+|https?://[^"]+)"', html)
    print("Total links:", len(all_links))
    for l in all_links[:20]:
        if "google" not in l or "/url?q=" in l:
            print("  Result link:", l[:100])
    # check text for Zwaan
    print("Mentions of 'Zwaan':", len(re.findall(r'Zwaan', html, re.IGNORECASE)))
    # print snippet of any mention
    for m in re.finditer(r'Zwaan', html, re.IGNORECASE):
        start = max(0, m.start() - 50)
        end = min(len(html), m.end() + 100)
        print("  Snippet:", html[start:end].replace("\n", " "))
        break
