import sqlite3
import json

conn = sqlite3.connect('data/breach_spillover.db')
c = conn.cursor()
c.execute("SELECT id, full_name, corporate_email FROM employees")
emps = c.fetchall()
print(f"Total employees: {len(emps)}")
for emp_id, name, email in emps:
    c.execute("SELECT pivot_type, pivot_value, context_note FROM pivots WHERE employee_id = ?", (emp_id,))
    pivs = c.fetchall()
    fb_pivs = [p for p in pivs if 'facebook' in p[1].lower() or 'facebook' in (p[2] or '').lower()]
    if fb_pivs:
        print(f"\nEmployee #{emp_id}: {name} ({email}) has {len(fb_pivs)} Facebook pivots:")
        for pt, pv, cn in fb_pivs:
            print(f"  [{pt}] {pv} -> {cn}")
conn.close()
