import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from backend.web_dork_recon import query_search_snippets

test_queries = [
    'facebook.com "Jordin Zwaan"',
    '"Jordin Zwaan" "facebook"',
    'intitle:"Jordin Zwaan"',
    'jordin zwaan facebook amsterdam',
    'jordin zwaan netherlands facebook',
    'jordin zwaan social facebook',
    '"Jordin" "Zwaan" facebook'
]

for q in test_queries:
    snips = query_search_snippets(q, max_results=5)
    print(f"\nQuery: {q} -> {len(snips)} results")
    for s in snips:
        print(f"  * {s['title']} | {s['url']}")
        print(f"    {s['snippet'][:120]}")
