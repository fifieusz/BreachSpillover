import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.web_dork_recon import query_search_snippets
res = query_search_snippets('site:facebook.com "Jordin Zwaan"')
print("Num results:", len(res))
for r in res:
    print(r['title'], "-->", r['url'])
