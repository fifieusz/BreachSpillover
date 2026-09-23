import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.web_dork_recon import query_search_snippets

for q in [
    'Jordin Zwaan Deltion',
    'Jordin Zwaan Wolvega',
    'Jordin Zwaan AUAS',
    'Jordin Zwaan "Wolvega"',
    'jordin zwaan facebook'
]:
    snips = query_search_snippets(q)
    print(f"Query: [{q}] -> {len(snips)} snips")
    for s in snips:
        print("  ", s['title'], "->", s['url'])
        if "facebook" in s['url'].lower():
            print("     FB FOUND:", s['url'])
