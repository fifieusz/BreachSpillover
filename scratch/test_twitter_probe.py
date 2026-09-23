import urllib.request
import re

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def probe_twitter(clean_handle: str):
    try:
        req = urllib.request.Request(
            f"https://x.com/{clean_handle}",
            headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(req, timeout=3.0) as res:
            if res.status == 200:
                html = res.read().decode("utf-8", errors="ignore")
                title_m = re.search(r'<title>(.*?)</title>', html)
                disp_name = clean_handle
                if title_m:
                    raw_title = title_m.group(1).strip()
                    m = re.match(r'^(.*?)\s*\(@[^\)]+\)\s*/\s*X', raw_title)
                    if m:
                        disp_name = m.group(1).strip()
                return {
                    "platform": "Twitter",
                    "handle": clean_handle,
                    "name": disp_name,
                    "profile_url": f"https://x.com/{clean_handle}",
                    "confidence": 0.90,
                    "category": "Social & Microblogging",
                    "context": f"Public profile on X (Twitter) under @{clean_handle}" + (f" (Name: '{disp_name}')" if disp_name and disp_name != clean_handle else "")
                }
    except Exception as e:
        pass
    return None

print("Testing probe_twitter('fifieusz'):", probe_twitter("fifieusz"))
print("Testing probe_twitter('jordinzwaan'):", probe_twitter("jordinzwaan"))
print("Testing probe_twitter('nonexistentrandomuser999888'):", probe_twitter("nonexistentrandomuser999888"))
