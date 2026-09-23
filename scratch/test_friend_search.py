import urllib.request
import urllib.parse
import re
import json

def search_ddg(q):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            html = res.read().decode('utf-8', errors='ignore')
            
            results = []
            blocks = re.findall(r'<div class="result results_links[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
            for b in blocks:
                title_m = re.search(r'<a class="result__url"[^>]*href="([^"]*uddg=[^"]*)"[^>]*>(.*?)</a>', b)
                snippet_m = re.search(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', b, re.DOTALL)
                
                real_url = ""
                if title_m:
                    raw_href = title_m.group(1)
                    parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                    if 'uddg' in parsed_qs:
                        real_url = parsed_qs['uddg'][0]
                elif snippet_m:
                    url_m = re.search(r'href="([^"]*uddg=[^"]*)"', b)
                    if url_m:
                        raw_href = url_m.group(1)
                        parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                        if 'uddg' in parsed_qs:
                            real_url = parsed_qs['uddg'][0]
                
                snippet = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip() if snippet_m else ""
                if real_url:
                    results.append({"url": real_url, "snippet": snippet})
            
            print(f"Query: '{q}' -> Found {len(results)} results:")
            for r in results[:6]:
                print(f"  * {r['url']}")
                print(f"    Snippet: {r['snippet']}")
            return results
    except Exception as e:
        print(f"Error for '{q}': {e}")
        return []

if __name__ == '__main__':
    search_ddg('"jordin zwaan"')
    search_ddg('jordin zwaan facebook')
    search_ddg('site:facebook.com "jordin zwaan"')
