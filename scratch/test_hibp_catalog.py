import sys
sys.path.insert(0, '.')
from backend.hibp_catalog import sync_hibp_catalog, lookup_breach_metadata

catalog = sync_hibp_catalog()
print(f"Synchronized {len(catalog)} official HIBP breaches.")
for target in ['Canva', 'Adobe', 'LinkedIn', 'Dropbox', 'Roll20']:
    meta = lookup_breach_metadata(target)
    if meta:
        print(f" - [{meta['severity']}] {meta['title']} ({meta['breach_date']}) | Pwn Count: {meta['pwn_count']:,}")
        print(f"   Data Classes ({len(meta['data_classes'])}): {meta['data_classes'][:4]}...")
