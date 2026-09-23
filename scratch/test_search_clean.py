import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from backend.main import search_exposure

res = search_exposure('jordinzwaan2016@gmail.com', audit_mode=True)
print(f"Total Pivots: {len(res.get('pivots', []))}")
fb_pivots = [p for p in res.get('pivots', []) if 'facebook' in p['pivot_value'].lower() or 'facebook' in (p.get('context_note') or '').lower()]
print(f"Facebook Pivots: {len(fb_pivots)}")
for p in fb_pivots:
    print(f"  [{p['pivot_type']}] {p['pivot_value']} -> {p.get('context_note')}")

print(f"\nPhysical Footprints: {len(res.get('physical_footprints', []))}")
for f in res.get('physical_footprints', []):
    print(f"  {f.get('address_line')}, City: {f.get('city')}, Country: {f.get('country')}")

emp = res.get('employee', {})
print(f"\nEmployee: Name: {emp.get('full_name')}, Dept: {emp.get('department')}, Title: {emp.get('job_title')}")
