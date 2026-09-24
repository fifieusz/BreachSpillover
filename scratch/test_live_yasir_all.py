import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import json

import sys
sys.path.insert(0, '.')
from backend.live_osint import check_email_with_holehe, execute_deep_live_osint
from backend.osint_scanner import query_xposedornot, query_hudson_rock

email = "Yasir1kadhim@gmail.com"

print("--- 1. Testing Holehe ---")
holehe_res = check_email_with_holehe(email)
print(f"Holehe found {len(holehe_res)} registered accounts:")
for h in holehe_res:
    print(f"  * {h.get('name')} (exists: {h.get('exists')})")

print("\n--- 2. Testing XposedOrNot ---")
xon = query_xposedornot(email)
print(f"XposedOrNot breaches ({len(xon)}):")
for b in xon:
    print(f"  * {b.get('source_title')} ({b.get('breach_date')})")

print("\n--- 3. Testing Hudson Rock Cavalier ---")
hr = query_hudson_rock(email)
print(f"Hudson Rock compromised stealer breaches: {len(hr)}")

print("\n--- 4. Testing Deep Live OSINT ---")
live = execute_deep_live_osint(email)
print(f"Primary name: {live.get('primary_name')}")
print(f"Discovered names: {live.get('discovered_names')}")
print(f"Discovered handles: {live.get('discovered_handles')}")
print(f"Accounts ({len(live.get('discovered_accounts', []))}):")
for acc in live.get('discovered_accounts', []):
    print(f"  * {acc.get('platform')}: {acc.get('url')} ({acc.get('username')})")
print(f"Avatars ({len(live.get('discovered_avatars', []))}):")
for av in live.get('discovered_avatars', []):
    print(f"  * {av.get('platform')}: {av.get('url')}")
