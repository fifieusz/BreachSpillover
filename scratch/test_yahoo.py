import sys
sys.path.insert(0, '.')
from backend.web_dork_recon import query_yahoo_search

snips = query_yahoo_search('Yasir Kadhim', 5)
print('Yahoo snips count:', len(snips))
for s in snips:
    print('Yahoo:', s['title'], '->', s['url'])
