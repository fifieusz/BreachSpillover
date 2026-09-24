import sqlite3

conn = sqlite3.connect('data/breach_spillover.db')
conn.row_factory = sqlite3.Row
emp = conn.execute("SELECT id, full_name, corporate_email FROM employees WHERE corporate_email LIKE '%filipos%'").fetchone()
print("Employee:", dict(emp))

fps = conn.execute("SELECT * FROM physical_footprints WHERE employee_id = ?", (emp['id'],)).fetchall()
print(f"\nPhysical Footprints ({len(fps)}):")
for f in fps:
    print(f"  [{f['id']}] {f['address_line']} | {f['city']}, {f['postal_code']}, {f['country']} (Lat: {f['latitude']}, Lon: {f['longitude']}) - Type: {f['exposure_type']}")

pvs = conn.execute("SELECT * FROM pivots WHERE employee_id = ? ORDER BY confidence_score DESC", (emp['id'],)).fetchall()
print(f"\nPivots ({len(pvs)}):")
by_type = {}
for p in pvs:
    by_type.setdefault(p['pivot_type'], []).append(p)

for ptype, items in by_type.items():
    print(f"\n--- {ptype} ({len(items)}) ---")
    for item in items[:5]:
        print(f"  [{item['confidence_score']}] {item['pivot_value']} | {item['context_note'][:60] if item['context_note'] else ''}")
