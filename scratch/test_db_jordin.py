import sys
sys.path.insert(0, '.')
from backend.database import get_connection, get_or_create_identity_profile, get_employee_by_id

emp = get_or_create_identity_profile('jordinzwaan2016@gmail.com')
emp_id = emp['id']
conn = get_connection()
footprints = conn.execute('SELECT address_line, city, country, exposure_type FROM physical_footprints WHERE employee_id=?', (emp_id,)).fetchall()
pivots = conn.execute('SELECT pivot_type, pivot_value FROM pivots WHERE employee_id=? AND pivot_type IN (?, ?)', (emp_id, 'WORKPLACE', 'PUBLIC_PROFILE')).fetchall()
conn.close()

print('Employee Name:', emp.get('full_name'))
print('Job Title:', emp.get('job_title'))
print('Department:', emp.get('department'))
print('Footprints Count:', len(footprints))
for f in footprints:
    print('  Footprint:', dict(f))
print('Pivots Count:', len(pivots))
for p in pivots:
    print('  Pivot:', p['pivot_type'], '->', p['pivot_value'])
