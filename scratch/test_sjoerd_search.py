import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.web_dork_recon import query_search_snippets

query = '"Sjoerd Sikkema"'
snips = query_search_snippets(query, max_results=8)
print(f"Found snippets for {query}: {len(snips)}")
for s in snips:
    title = str(s.get("title", "")).encode("ascii", "replace").decode("ascii")
    url = str(s.get("url", ""))
    print(f"  {title[:60]} -> {url}")
