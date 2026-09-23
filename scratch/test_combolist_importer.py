import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".")
from import_breach import import_combolist
from backend.database import get_connection

# Generate a mock 500-line combolist with email:pass, email:hash, and user:email:pass
sample_data = []
for i in range(1, 250):
    sample_data.append(f"audit_user_{i}@enterprise-corp.com:P@ssword2024!")
    sample_data.append(f"user_{i}:hash_target_{i}@enterprise-corp.com:5f4dcc3b5aa765d61d8327deb882cf99")

mock_file = os.path.join(tempfile.gettempdir(), "test_breach_dump.txt")
with open(mock_file, "w", encoding="utf-8") as f:
    f.write("\n".join(sample_data))

print(f"Generated test breach file at {mock_file} with {len(sample_data)} rows.")

res = import_combolist(
    file_path=mock_file,
    leak_name="Canva", # Test automatic HIBP catalog matching
    leak_type="DATABASE_LEAK"
)

assert res["total_records"] == len(sample_data), f"Expected {len(sample_data)}, got {res['total_records']}"
assert res["total_plains"] == 249, f"Expected 249 plaintexts, got {res['total_plains']}"
assert res["total_hashes"] == 249, f"Expected 249 hashes, got {res['total_hashes']}"

# Verify database query
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT leak_name, description, severity FROM leaks WHERE id = ?", (res["leak_id"],))
row = cursor.fetchone()
print(f"Database Verification: Leak #{res['leak_id']} '{row[0]}' [Severity: {row[2]}]")
assert "Canva" in row[0], "Expected Canva title from HIBP catalog"

# Clean up
if os.path.exists(mock_file):
    os.remove(mock_file)

print("ALL COMBIST IMPORTER TESTS PASSED SUCCESSFULLY!")
