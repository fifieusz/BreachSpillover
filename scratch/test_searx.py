import urllib.request
import urllib.parse
import json

searx_instances = [
    "https://searx.be/search?q={}&format=json",
    "https://search.ononoki.org/search?q={}&format=json",
    "https://searx.tiekoetter.com/search?q={}&format=json",
    "https://search.sapti.me/search?q={}&format=json",
    "https://priv.au/search?q={}&format=json",
    "https://search.mdosch.de/search?q={}&format=json"
]

q = urllib.parse.quote('Jordin Zwaan facebook')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for inst in searx_instances:
    url = inst.format(q)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as res:
            if res.status == 200:
                data = json.loads(res.read().decode('utf-8'))
                results = data.get('results', [])
                print(f"Success with {inst}: {len(results)} results")
                for r in results:
                    if 'facebook' in r.get('url', ''):
                        print("  FB URL:", r.get('url'))
                        print("  Title:", r.get('title'))
                        print("  Snippet:", r.get('content', '')[:100])
                break
    except Exception as e:
        print(f"Failed {inst}: {e}")
