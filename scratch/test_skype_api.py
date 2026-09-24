import urllib.request, urllib.parse, json

email = "3gbxdd@gmail.com"
endpoints = [
    f"https://skype.com/api/users/{urllib.parse.quote(email)}",
    f"https://api.skype.com/users/search?q={urllib.parse.quote(email)}",
    f"https://contacts.skype.com/contacts/v2/users/{urllib.parse.quote(email)}"
]

for url in endpoints:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            print("URL:", url, "Status:", resp.status)
            print(resp.read().decode()[:200])
    except Exception as e:
        print("URL:", url, "Failed:", e)
