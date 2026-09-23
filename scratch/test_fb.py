import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.web_dork_recon import query_search_snippets

def test_fb():
    target = "Jordin Zwaan"
    queries = [
        f"{target} facebook",
        f'"{target}" facebook',
        f'site:facebook.com "{target}"',
        f'site:facebook.com {target}',
        f'site:facebook.com/public "{target}"',
        f'site:facebook.com/public {target}',
        f'"{target}" "facebook.com"',
        f'jordinzwaan2016 facebook'
    ]
    for q in queries:
        print(f"\n--- QUERY: {q} ---")
        snips = query_search_snippets(q, max_results=6)
        print(f"Total results: {len(snips)}")
        for s in snips:
            print(f"  Title: {s['title']}")
            print(f"  URL: {s['url']}")
            print(f"  Snip: {s['snippet'][:150]}")

if __name__ == "__main__":
    test_fb()
