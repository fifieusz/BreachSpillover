import sys
import os

def test_user_scanner_programmatic():
    try:
        from user_scanner.core.email_orchestrator import _run_email_full_batch_async
        from user_scanner.core.config import Config
        import asyncio
        
        cfg = Config()
        cfg.no_nsfw = True
        cfg.timeout = 5
        cfg.verbose = True
        
        print("Invoking _run_email_full_batch_async...")
        results = asyncio.run(_run_email_full_batch_async("3gbxdd@gmail.com", cfg))
        print("Results received:", len(results))
        for r in results:
            status_val = getattr(r.status, 'value', str(r.status))
            if status_val.lower() in ["found", "registered", "claimed"]:
                print(f"MATCH: {r.site_name} -> {status_val} (URL: {getattr(r, 'url', '')})")
    except Exception as e:
        print("Error invoking user_scanner:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_scanner_programmatic()
