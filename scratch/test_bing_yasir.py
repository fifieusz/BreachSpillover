import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import urllib.request
import urllib.parse
import re
import base64

def search_bing(query, max_res=10):
    url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', html)
    results = []

    for b in blocks[:max_res]:
        a_matches = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', b)
        target_url = None
        title = None
        snippet = ""
        
        for href, text_content in a_matches:
            clean_text = re.sub(r'<[^>]+>', '', text_content).strip()
            clean_href = href.replace('&amp;', '&')
            
            if clean_href.startswith('http') and 'bing.com' not in clean_href and 'microsoft.com' not in clean_href:
                target_url = clean_href
                title = clean_text
                break
                
            if 'bing.com/ck/a' in clean_href:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(clean_href).query)
                u_param = qs.get('u', [''])[0]
                if u_param.startswith('a1'):
                    b64 = u_param[2:]
                    b64 += '=' * ((4 - len(b64) % 4) % 4)
                    try:
                        dec = base64.urlsafe_b64decode(b64).decode('utf-8', errors='ignore')
                        if dec.startswith('http') and 'bing.com' not in dec and 'microsoft.com' not in dec:
                            target_url = dec
                            if clean_text and len(clean_text) > 3 and not clean_text.startswith('http'):
                                title = clean_text
                    except Exception:
                        pass
        
        p_match = re.search(r'<p[^>]*>([\s\S]*?)</p>', b)
        if p_match:
            snippet = re.sub(r'<[^>]+>', '', p_match.group(1)).strip()
            
        if target_url:
            results.append({"title": title or target_url, "url": target_url, "snippet": snippet})
    return results

print("=== Search: Yasir Kadhim ===")
for r in search_bing("Yasir Kadhim", 5):
    print(r["title"], "->", r["url"])
    if r["snippet"]:
        print(" ", r["snippet"][:100])

print("\n=== Search: Yasir Ashraf Kadim ===")
for r in search_bing("Yasir Ashraf Kadim", 5):
    print(r["title"], "->", r["url"])
    if r["snippet"]:
        print(" ", r["snippet"][:100])

print("\n=== Search: yasir1kadhim ===")
for r in search_bing("yasir1kadhim", 5):
    print(r["title"], "->", r["url"])
    if r["snippet"]:
        print(" ", r["snippet"][:100])
