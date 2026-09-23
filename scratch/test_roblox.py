import urllib.request
import json

def test_roblox(usernames):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = json.dumps({"usernames": usernames, "excludeBannedUsers": False}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            print("Roblox response:", json.dumps(data, indent=2))
            return data.get("data", [])
    except Exception as e:
        print("Roblox error:", e)
        return []

if __name__ == '__main__':
    test_roblox(["fifieusz", "fifi", "filipos123"])
