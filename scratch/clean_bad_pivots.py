import sys
sys.path.insert(0, ".")
from backend.database import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("DELETE FROM pivots WHERE pivot_value LIKE '%wordpress.com%' OR context_note LIKE '%facebook.com/search%' OR pivot_value LIKE '%jordinzwaan2020%'")
print('Deleted bad cached pivots:', cur.rowcount)
conn.commit()
conn.close()
