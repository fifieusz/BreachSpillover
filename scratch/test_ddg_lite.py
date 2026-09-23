import urllib.request
import urllib.parse
import re

url = "https://lite.duckduckgo.com/lite/"
data = urllib.parse.urlencode({'q': 'Jordin Zwaan facebook'}).encode('utf-8')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://lite.duckduckgo.com/'
}
req = urllib.request.Request(url, data=data, headers=headers)
with urllib.request.urlopen(req, timeout=8) as res:
    html = res.read().decode('utf-8', errors='ignore')

idx = html.lower().find("wolvega")
# find the preceding <tr> or <table>
prev_tr = html.rfind("<tr", 0, idx)
next_tr = html.find("</tr>", idx)
print("=== TABLE ROW FOR WOLVEGA ===")
print(html[prev_tr:next_tr+5])

# Also check the link before this snippet
prev_link_idx = html.rfind("<a", 0, idx)
next_link_idx = html.find("</a>", prev_link_idx)
print("\n=== PRECEDING LINK ===")
print(html[prev_link_idx:next_link_idx+4])
