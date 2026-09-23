import urllib.request
import urllib.parse
import re

def test_query(q):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')
        
        # In Bing, search results are inside <li class="b_algo">
        items = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)
        print(f"\n==========================================")
        print(f"Query: {q} -> Items: {len(items)}")
        for i, it in enumerate(items[:5]):
            # Find the title and link
            m_link = re.search(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', it, re.DOTALL)
            m_snip = re.search(r'<p[^>]*>(.*?)</p>', it, re.DOTALL)
            if m_link:
                href = m_link.group(1)
                title = re.sub(r'<[^>]+>', '', m_link.group(2)).strip()
                snip = re.sub(r'<[^>]+>', '', m_snip.group(1)).strip() if m_snip else ""
                print(f"[{i+1}] {title}")
                print(f"    URL: {href}")
                print(f"    TXT: {snip[:160]}")
    except Exception as e:
        print(f"Error for {q}: {e}")

test_query('"filip niewiadomski"')
test_query('"jordin zwaan"')
test_query('site:facebook.com "jordin zwaan"')
test_query('site:linkedin.com "jordin zwaan"')
