import sqlite3

conn = sqlite3.connect("data/breach_spillover.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

for email in ["yasir1kadhim@gmail.com", "filipos123.91@gmail.com"]:
    cursor.execute("SELECT id, full_name, corporate_email FROM employees WHERE corporate_email = ?", (email,))
    emp = cursor.fetchone()
    print("=" * 60)
    if not emp:
        print(f"Employee not found for {email}")
        continue
    emp_id = emp["id"]
    print(f"Employee ID {emp_id}: {emp['full_name']} ({emp['corporate_email']})")
    
    cursor.execute("SELECT pivot_type, pivot_value, confidence_score, context_note FROM pivots WHERE employee_id = ? ORDER BY confidence_score DESC, id ASC", (emp_id,))
    rows = cursor.fetchall()
    print(f"Total Pivots in DB: {len(rows)}")
    for r in rows:
        val = str(r["pivot_value"]).encode("ascii", "replace").decode("ascii")
        note = str(r["context_note"] or "").encode("ascii", "replace").decode("ascii")
        print(f"  [{r['pivot_type']}] conf: {r['confidence_score']} | val: {val} | note: {note[:60]}")

conn.close()
