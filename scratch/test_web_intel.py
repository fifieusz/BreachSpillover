import urllib.request
import urllib.parse
import re
import json

def test_ddg_snippets(query):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    })
    try:
        with urllib.request.urlopen(req, timeout=6) as res:
            html = res.read().decode('utf-8', errors='ignore')
            
            # Find all results
            results = []
            blocks = re.findall(r'<div class="result results_links[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
            print(f"Blocks found: {len(blocks)}")
            for b in blocks:
                title_m = re.search(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', b, re.DOTALL)
                snippet_m = re.search(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', b, re.DOTALL)
                url_m = re.search(r'href="([^"]*uddg=[^"]*)"', b)
                
                real_url = ""
                if url_m:
                    raw_href = url_m.group(1)
                    parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                    if 'uddg' in parsed_qs:
                        real_url = parsed_qs['uddg'][0]
                
                snippet = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip() if snippet_m else ""
                if real_url:
                    results.append({"url": real_url, "snippet": snippet})
            
            print(f"Parsed {len(results)} search results for '{query}':")
            for r in results[:5]:
                print(f"  * URL: {r['url']}")
                print(f"    Snippet: {r['snippet'][:100]}...")
            return results
    except Exception as e:
        print("Error:", e)
        return []

if __name__ == '__main__':
    test_ddg_snippets('filipos123.91@gmail.com')
    test_ddg_snippets('site:github.com "filipos123.91"')
