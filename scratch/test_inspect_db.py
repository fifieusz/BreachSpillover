import sqlite3
from pathlib import Path

db_paths = [
    Path("data/breach_spillover.db")
]

for p in db_paths:
    if p.exists():
        print(f"\n=== Database: {p} ===")
        conn = sqlite3.connect(p)
        c = conn.cursor()
        try:
            c.execute("SELECT id, full_name, corporate_email, department, job_title FROM employees WHERE corporate_email LIKE '%jordin%'")
            emps = c.fetchall()
            print("Employees:", emps)
            for emp in emps:
                emp_id = emp[0]
                c.execute("SELECT pivot_type, pivot_value, context_note FROM pivots WHERE employee_id = ?", (emp_id,))
                pivs = c.fetchall()
                print(f"Pivots for emp {emp_id} ({len(pivs)}):")
                for pt, pv, cn in pivs:
                    if "facebook" in (pv + " " + cn).lower() or "http" in cn.lower():
                        print(f"  [{pt}] {pv} | {cn}")
                
                c.execute("SELECT address_line, city, country FROM physical_footprints WHERE employee_id = ?", (emp_id,))
                foots = c.fetchall()
                print(f"Footprints for emp {emp_id}:", foots)
        except Exception as e:
            print("Error:", e)
        conn.close()
