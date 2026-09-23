import urllib.request, json, os

with open('backend/data/wmn-data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
sites = d.get('sites', [])

test_sites = [s for s in sites if s.get('name') in ['GitLab', 'Pastebin', 'Keybase', 'Medium', 'Chess.com', 'Docker Hub']]

def check_site(site, handle):
    url = site['uri_check'].replace('{account}', handle)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            code = resp.status
            body = resp.read().decode('utf-8', errors='ignore')
            
            m_str = site.get('m_string')
            e_str = site.get('e_string')
            m_c = site.get('m_code')
            e_c = site.get('e_code')
            
            if m_str and m_str in body:
                return False, 'm_string found'
            if e_str and e_str not in body:
                return False, 'e_string missing'
            if m_c and code == m_c and not m_str:
                return False, 'm_code match'
            if e_c and code == e_c:
                return True, 'FOUND'
            return False, 'code mismatch'
    except urllib.error.HTTPError as e:
        if site.get('m_code') and e.code == site.get('m_code'):
            return False, 'm_code HTTPError'
        return False, f'HTTPError {e.code}'
    except Exception as ex:
        return False, str(ex)

for s in test_sites:
    found, reason = check_site(s, 'torvalds')
    print(f"{s['name']}: {found} ({reason})")
