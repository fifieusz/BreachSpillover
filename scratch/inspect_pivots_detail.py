import sqlite3

conn = sqlite3.connect('data/breach_spillover.db')
c = conn.cursor()

def dump_emp(emp_id, email):
    print(f"\n================ EMP {emp_id}: {email} ================")
    c.execute("SELECT id, pivot_type, pivot_value, confidence_score, context_note FROM pivots WHERE employee_id = ?", (emp_id,))
    pivots = c.fetchall()
    print(f"Total pivots: {len(pivots)}")
    for p in pivots:
        ptype, pval, conf, ctx = p[1], p[2], p[3], p[4]
        print(f"  [{ptype}] {pval} (conf: {conf})")
        if ctx:
            print(f"      context: {ctx[:120]}")

dump_emp(583, 'yasir1kadhim@gmail.com')
dump_emp(47, 'filipos123.91@gmail.com')
