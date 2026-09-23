import urllib.request
import json

def test_roblox_profile(user_id):
    url = f"https://users.roblox.com/v1/users/{user_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            print("Roblox Profile Details:", json.dumps(data, indent=2))
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test_roblox_profile(3104499294)
