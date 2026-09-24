import sys
sys.path.insert(0, '.')
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import re
import hashlib
import json
from backend.database import get_connection
from backend.live_osint import check_email_with_holehe, execute_deep_live_osint
from backend.wmn_engine import enumerate_handle_wmn
from backend.osint_scanner import query_xposedornot, query_hudson_rock

email = "Yasir1kadhim@gmail.com"
conn = get_connection()
cursor = conn.cursor()

# Get or create employee
cursor.execute("SELECT id, full_name FROM employees WHERE corporate_email = ?", (email,))
row = cursor.fetchone()
if not row:
    cursor.execute("""
        INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level, avatar_seed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("Yasir Kadhim", email, "Target Identity", "Investigated Domain", "Standard / Individual", "yasir_kadhim"))
    emp_id = cursor.lastrowid
else:
    emp_id = row["id"]

print(f"Target Employee ID: {emp_id} ({email})")

# 1. Candidate handles
clean_user = email.split("@")[0].lower()
candidate_handles = {clean_user}
no_digits = re.sub(r'\d+', '', clean_user)
if no_digits and len(no_digits) >= 3:
    candidate_handles.add(no_digits)
delimited_parts = [p for p in re.split(r'[._\-\+\d]+', clean_user) if len(p) >= 2]
if len(delimited_parts) >= 2:
    candidate_handles.add("_".join(delimited_parts))
    candidate_handles.add(".".join(delimited_parts))

print(f"Candidate handles: {candidate_handles}")

# 2. WMN Probes
wmn_profiles = []
for h in list(candidate_handles):
    print(f"Running WMN for: {h}...")
    res = enumerate_handle_wmn(h, max_sites=60, priority_only=False)
    for m in res.get("matches", []):
        print(f"  -> Discovered: {m['platform']} at {m['url']}")
        wmn_profiles.append(m)

# 3. Holehe Probes
print("Running Holehe...")
holehe_matches = check_email_with_holehe(email)
for hm in holehe_matches:
    print(f"  -> Holehe verified: {hm.get('name')} (domain: {hm.get('domain')})")

conn.close()
