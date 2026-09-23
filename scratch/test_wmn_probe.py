from backend.wmn_engine import probe_whatsmyname, get_wmn_sites
import time

t0 = time.time()
sites = get_wmn_sites()
print("Active sites:", len(sites))

res = probe_whatsmyname("torvalds", max_sites=35)
print(f"Elapsed: {time.time()-t0:.2f}s | Discovered {len(res)} profiles:")
for r in res:
    print(f" - [{r['category']}] {r['platform']}: {r['profile_url']}")
