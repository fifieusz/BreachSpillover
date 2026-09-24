import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.web_dork_recon import query_search_snippets

queries = ['"3gbxdd@gmail.com"', '3gbxdd@gmail.com', '"3gbxdd"']
for q in queries:
    results = query_search_snippets(q, max_results=5)
    print(f"=== Results for {q}: {len(results)} ===")
    for r in results:
        print("  Title:", r.get("title"))
        print("  URL:  ", r.get("url"))
        print("  Desc: ", r.get("description", "")[:120])
