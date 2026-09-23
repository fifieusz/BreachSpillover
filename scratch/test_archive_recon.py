import sys
sys.path.insert(0, ".")
from backend.archive_recon import query_historical_archives
import time

t0 = time.time()
data = query_historical_archives("kernel.org")
print(f"Elapsed: {time.time()-t0:.2f}s")
print(f"Total URLs indexed: {data['total_urls_indexed']}")
print(f"Sensitive exposures count: {data['sensitive_exposures_count']}")
print(f"Discovered subdomains: {len(data['discovered_subdomains'])} ({data['discovered_subdomains'][:5]})")
print("Top 5 items:")
for it in data['items'][:5]:
    print(f" - [{it['risk_level']}] [{it['category']}] {it['url']} ({it['source']})")
