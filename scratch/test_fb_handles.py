import urllib.request
import urllib.error

handles = ["jordin.zwaan", "jordinzwaan", "jordin.zwaan.1", "jordinzwaan2016", "sazeku", "sazeku123"]
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

for h in handles:
    url = f"https://www.facebook.com/{h}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            title = "Unknown"
            if "<title>" in body:
                title = body.split("<title>")[1].split("</title>")[0]
            print(f"Handle '{h}' -> Status: {resp.status}, Title: {title[:60]}")
    except urllib.error.HTTPError as e:
        print(f"Handle '{h}' -> HTTPError: {e.code}")
    except Exception as e:
        print(f"Handle '{h}' -> Err: {e}")
