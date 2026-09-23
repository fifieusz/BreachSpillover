import urllib.request
import json
import urllib.parse
import re

def test_handles(handles):
    for handle in handles:
        url = f"https://steamcommunity.com/id/{handle}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                html = res.read().decode('utf-8', errors='ignore')
                if "The specified profile could not be found" not in html and "persona_name" in html:
                    m = re.search(r'actual_persona_name">([^<]+)<', html)
                    name = m.group(1) if m else handle
                    print(f"Steam found for {handle}: Persona Name = {name}")
                else:
                    print(f"Steam profile {handle} not found (custom URL)")
        except Exception as e:
            print(f"Steam error for {handle}:", e)

if __name__ == '__main__':
    test_handles(['fifieusz', 'Fifi987'])
