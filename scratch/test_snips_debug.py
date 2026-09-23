import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.web_dork_recon import query_search_snippets

for q in ["Jordin Zwaan", '"Jordin Zwaan"', "jordinzwaan", "Jordin Zwaan facebook"]:
    snips = query_search_snippets(q)
    print(f"Query '{q}': {len(snips)} snips")
    for s in snips:
        if "wixsite" in s['url'].lower() or "wolvega" in s['snippet'].lower():
            print("  FOUND:", s['title'], "-->", s['url'])
            print("    ", s['snippet'][:100])
