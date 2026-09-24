import urllib.request, hashlib, json

headers = {"User-Agent": "Mozilla/5.0"}

for email in ["sjoerdsikkema79@gmail.com", "xmister795@gmail.com"]:
    clean = email.strip().lower()
    md5 = hashlib.md5(clean.encode("utf-8")).hexdigest()
    print(f"\n=== Testing {email} (md5: {md5}) ===")
    
    # Gravatar JSON
    try:
        req = urllib.request.Request(f"https://en.gravatar.com/{md5}.json", headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            print("Gravatar found:", data.get("entry", [{}])[0].get("displayName"))
    except Exception as e:
        print("Gravatar:", e)

    # Duolingo
    try:
        req = urllib.request.Request(f"https://www.duolingo.com/2017-06-30/users?email={clean}", headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            users = data.get("users", [])
            print("Duolingo users found:", len(users))
            for u in users:
                print("  Duolingo:", u.get("username"), u.get("name"), u.get("bio"))
    except Exception as e:
        print("Duolingo:", e)
