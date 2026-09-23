import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.web_dork_recon import execute_ai_dork_recon
import json

res = execute_ai_dork_recon(
    target_name="Jordin Zwaan",
    target_email="jordinzwaan2016@gmail.com",
    known_handles=["jordinzwaan", "sazeku"],
    force_refresh=True
)

print("\n=== FINAL OSINT DORK RECON RESULT ===")
print(json.dumps(res, indent=2))
