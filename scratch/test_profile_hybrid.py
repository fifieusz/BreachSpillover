import sys
sys.path.insert(0, '.')
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.database import get_or_create_identity_profile, get_connection

email = "Yasir1kadhim@gmail.com"
print(f"=== Testing get_or_create_identity_profile for {email} ===")
emp = get_or_create_identity_profile(email, anchors={})

print("\n--- Profile Returned ---")
print("ID:", emp.get("id"))
print("Full Name:", emp.get("full_name"))
print("Job Title:", emp.get("job_title"))
print("Department:", emp.get("department"))
print("Email:", emp.get("corporate_email"))

conn = get_connection()
c = conn.cursor()
c.execute("SELECT * FROM physical_footprints WHERE employee_id = ?", (emp["id"],))
footprints = [dict(r) for r in c.fetchall()]
print(f"\n--- Footprints ({len(footprints)}) ---")
for f in footprints:
    print(f"  * {f['address_line']} ({f['city']}, {f['country']}) [Lat: {f['latitude']}, Lon: {f['longitude']}]")

c.execute("SELECT * FROM pivots WHERE employee_id = ?", (emp["id"],))
pivots = [dict(r) for r in c.fetchall()]
print(f"\n--- Pivots ({len(pivots)}) ---")
for p in pivots:
    print(f"  * [{p['pivot_type']}] {p['pivot_value']} ({p['context_note'][:80]}...)")
conn.close()
