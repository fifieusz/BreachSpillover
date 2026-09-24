import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from user_scanner.core.helpers import ScanConfig
from user_scanner.core.email_orchestrator import run_email_full_batch

def run_test():
    cfg = ScanConfig(no_nsfw=True, timeout=5)
    results = run_email_full_batch("3gbxdd@gmail.com", cfg)
    print(f"Total results: {len(results)}")
    for r in results:
        s = str(r.status).lower()
        if any(k in s for k in ["found", "registered", "claimed", "true"]):
            print(f"HIT: {r.site_name} | Status: {r.status} | URL: {getattr(r, 'url', None)}")

if __name__ == "__main__":
    run_test()
