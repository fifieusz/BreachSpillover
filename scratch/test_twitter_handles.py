import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

handles = ['yasirkadhim', 'yasir_kadhim', 'yasir1kadhim', 'djessir', 'dj_essir']
for h in handles:
    url = f"https://x.com/{h}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode('utf-8', errors='ignore')
            title = re.search(r'<title>(.*?)</title>', html, re.I)
            og_title = re.search(r'<meta property="og:title" content="(.*?)"', html, re.I)
            og_desc = re.search(r'<meta property="og:description" content="(.*?)"', html, re.I)
            print(f"@{h}: status={res.status}")
            if title:
                print(f"  title: {title.group(1)}")
            if og_desc:
                print(f"  desc: {og_desc.group(1)}")
    except Exception as e:
        print(f"@{h}: err={e}")
