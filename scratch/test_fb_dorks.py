import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.web_dork_recon import query_search_snippets

queries = [
    'jordin zwaan facebook',
    '"jordin zwaan" facebook',
    'site:facebook.com "jordin zwaan"',
    'site:facebook.com/public "jordin zwaan"',
    'jordinzwaan facebook',
    'jordin zwaan facebook amsterdam',
    'jordin zwaan facebook netherlands'
]

for q in queries:
    print(f"\n====================\nQuery: {q}")
    snips = query_search_snippets(q, max_results=5)
    print(f"Count: {len(snips)}")
    for s in snips:
        print(f"Title: {s['title']}")
        print(f"URL: {s['url']}")
        print(f"Snippet: {s['snippet'][:150]}")
