import urllib.request
import urllib.parse

url = "https://lite.duckduckgo.com/lite/"
data = urllib.parse.urlencode({'q': 'Jordin Zwaan facebook'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://lite.duckduckgo.com/'
}
req = urllib.request.Request(url, data=data, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        print("Status:", resp.status)
        html = resp.read().decode('utf-8', errors='ignore')
        print("HTML length:", len(html))
        print("First 500 chars:\n", html[:500])
except Exception as e:
    print("Error:", e)
