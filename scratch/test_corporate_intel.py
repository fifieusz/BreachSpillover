import sys
sys.path.insert(0, '.')
from backend.database import get_connection

conn = get_connection()
c = conn.cursor()
c.execute("SELECT * FROM employees WHERE corporate_email LIKE '%yasir%'")
rows = [dict(r) for r in c.fetchall()]
print('Employees:', rows)
if rows:
    emp_id = rows[0]['id']
    c.execute("SELECT * FROM pivots WHERE employee_id = ?", (emp_id,))
    pivots = [dict(r) for r in c.fetchall()]
    print(f'Pivots ({len(pivots)}):')
    for p in pivots:
        print(f"  [{p['pivot_type']}] {p['pivot_value']} ({p['context_note']})")
    c.execute("SELECT * FROM physical_footprints WHERE employee_id = ?", (emp_id,))
    footprints = [dict(r) for r in c.fetchall()]
    print(f'Footprints ({len(footprints)}):', footprints)
conn.close()
