import requests
import re
import json

def inspect_pinterest():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    r = requests.get('https://www.pinterest.com/3gbxdd/', headers=headers, timeout=10)
    print("Status code:", r.status_code)
    print("HTML length:", len(r.text))
    
    # Check for initial data script
    scripts = re.findall(r'<script id="__PWS_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
    if scripts:
        try:
            data = json.loads(scripts[0])
            user_data = data.get("props", {}).get("initialReduxState", {}).get("users", {})
            for uid, uinfo in user_data.items():
                print(f"UID: {uid}")
                print(f"  Username: {uinfo.get('username')}")
                print(f"  Full Name: {uinfo.get('full_name')}")
                print(f"  First Name: {uinfo.get('first_name')}")
                print(f"  Last Name: {uinfo.get('last_name')}")
                print(f"  Image: {uinfo.get('image_xlarge_url') or uinfo.get('image_large_url')}")
                print(f"  About: {uinfo.get('about')}")
                print(f"  Location: {uinfo.get('location')}")
        except Exception as e:
            print("Error parsing PWS_DATA:", e)
    else:
        print("No __PWS_DATA__ found.")

if __name__ == "__main__":
    inspect_pinterest()
