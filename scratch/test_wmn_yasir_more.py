import sys
sys.path.insert(0, '.')
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.wmn_engine import enumerate_handle_wmn

variations = ['yasir1kadhim', 'yasirkadhim', 'yasir_kadhim', 'yasir.kadhim']
for h in variations:
    res = enumerate_handle_wmn(h, max_sites=100)
    print(f"\nHandle: {h} -> Scanned {res['total_scanned']}, Matches: {res['matches_count']}")
    for m in res['matches']:
        print(f"   * {m['platform']}: {m['url']}")
