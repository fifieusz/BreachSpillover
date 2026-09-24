import sqlite3

conn = sqlite3.connect('data/breach_spillover.db')
conn.execute("UPDATE employees SET job_title = '', department = '', full_name = 'Filip Niewiadomski' WHERE corporate_email LIKE '%filipos%'")
conn.execute("DELETE FROM pivots WHERE pivot_value LIKE '%Customs Support%'")
conn.commit()
r = conn.execute("SELECT id, full_name, corporate_email, job_title, department FROM employees WHERE corporate_email LIKE '%filipos%'").fetchone()
print("Updated row:", r)
conn.close()
