import sys
sys.path.insert(0, ".")
from backend.platform_probes import probe_all_direct_platforms

print('=== Probing xmister ===')
hits_x = probe_all_direct_platforms(['xmister'])
for h in hits_x:
    n = str(h.get('real_name') or h.get('display_name') or h.get('persona_name') or '').encode('ascii', 'replace').decode('ascii')
    loc = str(h.get('location') or '').encode('ascii', 'replace').decode('ascii')
    print(f"  [{h.get('platform')}] Handle: {h.get('handle')}, Name: {n}, Location: {loc}, URL: {h.get('url')}")

print('\n=== Probing sjoerdsikkema ===')
hits_s = probe_all_direct_platforms(['sjoerdsikkema'])
for h in hits_s:
    n = str(h.get('real_name') or h.get('display_name') or h.get('persona_name') or '').encode('ascii', 'replace').decode('ascii')
    c = str(h.get('country') or '').encode('ascii', 'replace').decode('ascii')
    print(f"  [{h.get('platform')}] Handle: {h.get('handle')}, Name: {n}, Country: {c}, URL: {h.get('url')}")
