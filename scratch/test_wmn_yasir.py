import sys
sys.path.insert(0, '.')
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.wmn_engine import enumerate_handle_wmn

handles = ['yasir1kadhim', 'yasirkadhim']
for h in handles:
    res = enumerate_handle_wmn(h, max_sites=60)
    print(f"\nHandle: {h} -> Scanned {res['total_scanned']}, Matches: {res['matches_count']}")
    for m in res['matches']:
        print(f"   * {m['platform']}: {m['url']}")
