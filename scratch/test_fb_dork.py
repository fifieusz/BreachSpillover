import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.web_dork_recon import query_duckduckgo_lite, query_search_snippets, extract_valid_facebook_profile

print("Testing DDG queries for Facebook...")
queries = [
    'site:facebook.com "Jordin Zwaan"',
    '"Jordin Zwaan" facebook',
    'Jordin Zwaan facebook',
    'Jordin Zwaan facebook Wolvega',
    '"Jordin Zwaan" "Wolvega"',
    'Jordin Zwaan "Deltion College"'
]

for q in queries:
    print(f"\n--- Query: {q} ---")
    results = query_duckduckgo_lite(q, max_results=5)
    print(f"DDG Lite returned {len(results)} results")
    for r in results:
        print("Title:", r["title"])
        print("URL:", r["url"])
        print("Snippet:", r["snippet"][:150])
        fb_valid = extract_valid_facebook_profile(
            r["url"], title=r["title"], snippet=r["snippet"],
            target_name="Jordin Zwaan", target_email="jordinzwaan2016@gmail.com"
        )
        print("FB Valid:", fb_valid)
