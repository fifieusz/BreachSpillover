import sys
import os

sys.path.insert(0, ".")

from backend.hibp_engine import is_hibp_configured, query_hibp_breaches, query_hibp_pastes
from backend.hibp_catalog import sync_hibp_catalog, lookup_breach_metadata

def test_hibp_unconfigured():
    print("[1/3] Testing HIBP Engine in Keyless Mode...")
    # Ensure without key it returns cleanly
    orig_key = os.environ.get("HIBP_API_KEY")
    if "HIBP_API_KEY" in os.environ:
        del os.environ["HIBP_API_KEY"]
        
    assert not is_hibp_configured(), "Expected is_hibp_configured to be False"
    breaches = query_hibp_breaches("test@example.com")
    pastes = query_hibp_pastes("test@example.com")
    assert breaches == [], f"Expected empty list, got {breaches}"
    assert pastes == [], f"Expected empty list, got {pastes}"
    print(" [OK] Keyless fallback works cleanly.\n")
    
    if orig_key:
        os.environ["HIBP_API_KEY"] = orig_key

def test_catalog_enrichment():
    print("[2/3] Testing HIBP 1,038-Breach Catalog Metadata...")
    cat = sync_hibp_catalog()
    assert len(cat) >= 1000, f"Expected >= 1000 breaches in catalog, got {len(cat)}"
    
    sample = lookup_breach_metadata("LinkedIn")
    assert sample is not None, "Expected LinkedIn in catalog"
    print(f" -> Found: {sample['title']} ({sample['breach_date']})")
    print(f"    Data Classes: {sample['data_classes']}")
    print(f"    Severity: {sample['severity']}")
    assert "Passwords" in sample["data_classes"], "Expected Passwords in LinkedIn data classes"
    assert sample["severity"] == "CRITICAL", f"Expected CRITICAL severity, got {sample['severity']}"
    print(" [OK] Catalog enrichment verified.\n")

def test_mock_key_handling():
    print("[3/3] Testing HIBP Engine Authenticated Request Handling...")
    os.environ["HIBP_API_KEY"] = "mock_test_key_12345"
    assert is_hibp_configured() is True
    # With a mock key, it should attempt request and handle 401 unauthorized gracefully without crashing
    res = query_hibp_breaches("test@gmail.com")
    assert res == [], f"Expected empty list on 401, got {res}"
    del os.environ["HIBP_API_KEY"]
    print(" [OK] Authenticated request error handling verified.\n")

if __name__ == "__main__":
    test_hibp_unconfigured()
    test_catalog_enrichment()
    test_mock_key_handling()
    print("==================================================")
    print("ALL HIBP ENGINE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
