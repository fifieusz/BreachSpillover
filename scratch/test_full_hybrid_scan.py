import sys
sys.path.insert(0, '.')
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.database import get_connection, init_db
from backend.osint_scanner import run_full_osint_scan

init_db()

email = "Yasir1kadhim@gmail.com"
print(f"=== Executing Super Hybrid Scan for: {email} ===")

result = run_full_osint_scan(email, anchors={})
print(f"Scan finished. Target ID: {result.get('target_id')}")

conn = get_connection()
c = conn.cursor()
c.execute("SELECT * FROM employees WHERE corporate_email = ?", (email,))
emp = dict(c.fetchone())
print("\n--- Profile Attributes ---")
print("Full Name:", emp.get("full_name"))
print("Job Title:", emp.get("job_title"))
print("Department:", emp.get("department"))
print("Email:", emp.get("corporate_email"))

c.execute("SELECT * FROM physical_footprints WHERE employee_id = ?", (emp["id"],))
footprints = [dict(r) for r in c.fetchall()]
print(f"\n--- Physical Footprints ({len(footprints)}) ---")
for f in footprints:
    print(f"  * Address: {f['address_line']} | City: {f['city']} | Postal: {f['postal_code']} | Country: {f['country']} (Lat: {f['latitude']}, Lon: {f['longitude']})")

c.execute("SELECT * FROM pivots WHERE employee_id = ?", (emp["id"],))
pivots = [dict(r) for r in c.fetchall()]
print(f"\n--- Verified Pivots & External Accounts ({len(pivots)}) ---")
for p in pivots:
    print(f"  [{p['pivot_type']}] {p['pivot_value']} ({p['context_note'][:90]}...)")

conn.close()
