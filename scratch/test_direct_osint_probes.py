import urllib.request, urllib.parse, re
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}

print("=== 1. Telegram Web Profile Probe ===")
for h in ["sjoerdsikkema", "xmister"]:
    try:
        url = f"https://t.me/{h}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            title_m = re.search(r'<div class="tgme_page_title"[^>]*>([\s\S]*?)</div>', html)
            bio_m = re.search(r'<div class="tgme_page_description"[^>]*>([\s\S]*?)</div>', html)
            photo_m = re.search(r'<img class="tgme_page_photo_image"[^>]*src="([^"]+)"', html)
            if title_m:
                title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
                bio = re.sub(r'<[^>]+>', '', bio_m.group(1)).strip() if bio_m else ""
                photo = photo_m.group(1) if photo_m else None
                print(f"  Telegram @{h}: Name='{title}' | Bio='{bio[:60]}' | Photo={bool(photo)}")
            else:
                print(f"  Telegram @{h}: Not found / channel")
    except Exception as e:
        print(f"  Telegram @{h} Error:", e)

print("\n=== 2. Roblox Users API ===")
import json
try:
    url = "https://users.roblox.com/v1/usernames/users"
    payload = json.dumps({"usernames": ["sjoerdsikkema", "xmister", "xmister795"]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={**headers, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=4) as resp:
        data = json.loads(resp.read())
        for u in data.get("data", []):
            print(f"  Roblox user: @{u.get('name')} (DisplayName: '{u.get('displayName')}', ID: {u.get('id')})")
except Exception as e:
    print("Roblox Error:", e)

print("\n=== 3. Steam XML Profile Probe ===")
for h in ["sjoerdsikkema", "xmister"]:
    try:
        url = f"https://steamcommunity.com/id/{h}/?xml=1"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            xml = resp.read().decode("utf-8", errors="ignore")
            steam_id = re.search(r'<steamID><!\[CDATA\[(.*?)\]\]></steamID>', xml)
            real_name = re.search(r'<realname><!\[CDATA\[(.*?)\]\]></realname>', xml)
            loc = re.search(r'<location><!\[CDATA\[(.*?)\]\]></location>', xml)
            if steam_id:
                print(f"  Steam @{h}: Persona='{steam_id.group(1)}' | RealName='{real_name.group(1) if real_name else ''}' | Loc='{loc.group(1) if loc else ''}'")
            else:
                print(f"  Steam @{h}: Not found")
    except Exception as e:
        print(f"  Steam @{h} Error:", e)
