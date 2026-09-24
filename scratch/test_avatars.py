import urllib.request
import urllib.parse
import json

# Test GitHub avatar endpoint
handle = "fifieusz"
url = f"https://github.com/{handle}.png"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=4) as resp:
        print("GitHub handle.png status:", resp.status, "content-type:", resp.headers.get('Content-Type'))
except Exception as e:
    print("GitHub handle.png error:", e)

# Test Duolingo avatar endpoint
email = "test@example.com"
d_url = f"https://www.duolingo.com/2017-06-30/users?email={urllib.parse.quote(email)}"
d_req = urllib.request.Request(d_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(d_req, timeout=4) as resp:
        data = json.loads(resp.read().decode())
        print("Duolingo data:", data)
except Exception as e:
    print("Duolingo error:", e)
