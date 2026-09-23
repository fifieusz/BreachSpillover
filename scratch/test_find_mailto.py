import urllib.request
import re

url = "https://jordinzwaan2016.wixsite.com/portfolio"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("Total len:", len(html))
        m = re.findall(r"mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", html, re.I)
        print("Mailto found:", m)
        all_emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)
        print("All emails:", set(all_emails))
except Exception as e:
    print("Error:", e)
