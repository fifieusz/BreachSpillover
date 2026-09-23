import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.web_dork_recon import query_search_snippets

def test_city_dorks():
    name = "Jordin Zwaan"
    queries = [
        f'{name} facebook',
        f'{name} "lives in"',
        f'{name} "woont in"',
        f'{name} stad OR woonplaats OR city',
        f'{name} Merlon',
        f'{name} "Copyboss"',
        f'{name} LinkedIn',
        f'"{name}"'
    ]
    for q in queries:
        snips = query_search_snippets(q, max_results=5)
        print(f"\n======================================")
        print(f"QUERY: {q} (Found: {len(snips)})")
        for s in snips:
            try:
                print(f"  * {s['title']}")
                print(f"    URL: {s['url']}")
                print(f"    Snip: {s['snippet']}")
            except Exception as e:
                print(f"    [print error: {e}]")

if __name__ == "__main__":
    test_city_dorks()
