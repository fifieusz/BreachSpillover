import sys
import os
import re
import urllib.request
import json
import time

sys.path.insert(0, ".")

def test_wmn():
    print("[1/5] Testing WhatsMyName Multi-Platform Enumeration...")
    from backend.wmn_engine import probe_whatsmyname, get_wmn_sites
    sites = get_wmn_sites()
    assert len(sites) >= 500, f"Expected >= 500 WMN sites, got {len(sites)}"
    
    t0 = time.time()
    results = probe_whatsmyname("torvalds", max_sites=30)
    elapsed = time.time() - t0
    print(f" -> WMN probed 30 sites in {elapsed:.2f}s, found {len(results)} profiles:")
    for r in results[:3]:
        print(f"    * [{r['category']}] {r['platform']}: {r['profile_url']}")
    assert len(results) > 0, "Expected at least 1 profile discovered for torvalds"
    print(" [OK] WhatsMyName Engine verified.\n")

def test_archive_recon():
    print("[2/5] Testing Historical Archive Reconnaissance...")
    from backend.archive_recon import query_historical_archives
    t0 = time.time()
    data = query_historical_archives("kernel.org")
    elapsed = time.time() - t0
    print(f" -> Archive recon completed in {elapsed:.2f}s:")
    print(f"    * Total URLs: {data['total_urls_indexed']}")
    print(f"    * Sensitive Exposures: {data['sensitive_exposures_count']}")
    print(f"    * Subdomains Mapped: {len(data['discovered_subdomains'])}")
    assert data["total_urls_indexed"] > 0, "Expected indexed URLs from archive recon"
    print(" [OK] Historical Archive Engine verified.\n")

def test_pgp_expansion():
    print("[3/5] Testing Multi-Keyserver OpenPGP Expansion...")
    from backend.live_osint import query_openpgp_keys
    t0 = time.time()
    keys = query_openpgp_keys("torvalds@kernel.org")
    elapsed = time.time() - t0
    print(f" -> PGP query completed in {elapsed:.2f}s, found {len(keys)} keys:")
    for k in keys:
        print(f"    * Key 0x{k['key_id']} [{k['algorithm']}-{k['key_len']}] Created: {k.get('creation_date')}")
        print(f"      Names: {k.get('names')} | Source: {k.get('source')}")
    assert len(keys) > 0, "Expected at least 1 key for torvalds@kernel.org"
    has_name = any("Linus" in str(k.get("names", [])) for k in keys)
    assert has_name, "Expected Linus Torvalds extracted from PGP UID"
    print(" [OK] Multi-Keyserver PGP verified.\n")

def test_domain_recon_api():
    print("[4/5] Testing Domain Recon API (/api/domain/recon)...")
    url = "http://127.0.0.1:8000/api/domain/recon?domain=tesla.com"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode("utf-8"))
        print(f" -> Domain: {data.get('domain')}")
        print(f"    Risk: {data.get('organization_risk', {}).get('level')}")
        arch = data.get("historical_archives", {})
        print(f"    Historical URLs: {arch.get('total_urls_indexed')}")
        print(f"    Sensitive Endpoints: {arch.get('sensitive_exposures_count')}")
        assert "historical_archives" in data, "historical_archives missing from response"
    print(" [OK] Domain Recon API endpoint verified.\n")

def test_frontend_cleanliness():
    print("[5/5] Testing UI Cleanliness & 0 Unicode Emojis...")
    with urllib.request.urlopen("http://127.0.0.1:8000/", timeout=5) as r:
        html = r.read().decode("utf-8")
    with urllib.request.urlopen("http://127.0.0.1:8000/static/js/app.js?v=10.0", timeout=5) as r:
        js = r.read().decode("utf-8")
    
    emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF]|[\U0001FA00-\U0001FAFF]|[\u2600-\u26FF]|[\u2700-\u27BF]')
    html_emojis = emoji_pattern.findall(html)
    js_emojis = emoji_pattern.findall(js)
    
    # Filter out harmless currency or math symbols if any
    print(f" -> HTML emoji matches: {len(html_emojis)}")
    print(f" -> JS emoji matches: {len(js_emojis)}")
    assert len(html_emojis) == 0, f"Found emojis in HTML: {html_emojis}"
    assert len(js_emojis) == 0, f"Found emojis in JS: {js_emojis}"
    print(" [OK] 100% Monochrome Utilitarian UI verified.\n")

if __name__ == "__main__":
    test_wmn()
    test_archive_recon()
    test_pgp_expansion()
    test_domain_recon_api()
    test_frontend_cleanliness()
    print("==================================================")
    print("ALL 5 EXPANSION VALIDATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
