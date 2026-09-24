import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.web_dork_recon import query_search_snippets

queries = [
    '"Amir Secic"',
    '3gbxdd',
    '"Amir Secic" 3gbxdd',
    '"Amir Secic" (site:github.com OR site:gitlab.com)',
    '"Amir Secic" site:linkedin.com',
    '"Amir Secic" (site:x.com OR site:twitter.com)',
    '"Amir Secic" site:instagram.com',
    '"Amir Secic" site:steamcommunity.com'
]

for q in queries:
    snips = query_search_snippets(q, max_results=3)
    print(f"=== Query: {q} ({len(snips)} results) ===")
    for s in snips[:2]:
        print("  Title:", s.get("title"))
        print("  URL:  ", s.get("url"))
        print("  Snip: ", (s.get("snippet") or "")[:120])
