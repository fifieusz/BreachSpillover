import sqlite3

conn = sqlite3.connect('data/breach_spillover.db')
c = conn.cursor()

# Find and delete false-positive / malformed facebook pivots
c.execute("""
    DELETE FROM pivots 
    WHERE pivot_type = 'PUBLIC_PROFILE' 
      AND (
          pivot_value LIKE 'Facebook: %'
          OR pivot_value LIKE 'Facebook: public%'
          OR pivot_value LIKE 'Facebook: login%'
          OR pivot_value LIKE 'Facebook: company_creation%'
          OR pivot_value LIKE 'Facebook: zwaan91%'
          OR pivot_value LIKE 'Facebook: jordy%'
          OR pivot_value LIKE 'Facebook: joris%'
          OR context_note LIKE '%facebook.com/public/%'
          OR context_note LIKE '%facebook.com/login%'
          OR context_note LIKE '%work.facebook.com%'
          OR context_note LIKE '%m.facebook.com%'
          OR context_note LIKE '%Zwaan91%'
          OR context_note LIKE '%jordy.zwaan%'
          OR context_note LIKE '%Jordan-Zwaard%'
          OR context_note LIKE '%Jordi-van-Zain%'
      )
""")
deleted = c.rowcount
conn.commit()
print(f"Cleaned up {deleted} invalid Facebook pivots from database.")

# Verify remaining Facebook pivots
c.execute("SELECT id, employee_id, pivot_type, pivot_value, context_note FROM pivots WHERE lower(pivot_value) LIKE '%facebook%' OR lower(context_note) LIKE '%facebook%'")
rows = c.fetchall()
print(f"Remaining Facebook pivots: {len(rows)}")
for r in rows:
    print(r)
conn.close()
