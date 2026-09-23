import urllib.request
import urllib.parse
import re

url = "https://www.google.com/search?q=" + urllib.parse.quote("Jordin Zwaan") + "&hl=en"
# Android mobile user agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': 'CONSENT=PENDING+999; SOCS=CAISHAgCEhJnd3NfMjAyNDA2MTAtMF9SQzIaAmVuIAEaBgiA_L20Bg'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print("Status:", res.status, "Len:", len(html))
        print("Title:", re.findall(r'<title>(.*?)</title>', html))
        fb = re.findall(r'facebook\.com/[^\s"\'&<>]+', html)
        print("FB in mobile Google:", set(fb))
        if "Wolvega" in html:
            print("Found Wolvega in mobile Google!")
except Exception as e:
    print("Error:", e)
