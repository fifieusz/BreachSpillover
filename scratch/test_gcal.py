import urllib.request, urllib.parse, re

email = "3gbxdd@gmail.com"
url = f"https://calendar.google.com/calendar/htmlembed?src={urllib.parse.quote(email)}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=4) as resp:
        print("Google Calendar status:", resp.status)
        content = resp.read().decode("utf-8", errors="ignore")
        title = re.search(r"<title>(.*?)</title>", content)
        if title:
            print("Calendar title:", title.group(1))
        # Look for any display names or email in the payload
        names = set(re.findall(r'"([a-zA-Z\s]{4,30})"', content))
        clean_names = [n for n in names if any(p in n.lower() for p in ["amir", "secic", "3gbx"])]
        print("Matches in GCal:", clean_names)
except Exception as e:
    print("GCal error:", e)
