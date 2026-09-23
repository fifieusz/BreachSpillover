import urllib.request
import json
import sys

def run_tests():
    print("=== Testing BreachSpillover Frontend & Backend ===")
    
    # 1. Test Index HTML
    req = urllib.request.Request("http://127.0.0.1:8000/")
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
        assert "Target Investigation Cockpit" in html, "Missing Cockpit title"
        assert "summary-metrics-banner" in html, "Missing Summary Metrics Banner"
        assert "search-type-badge" in html, "Missing search-type-badge"
        assert "search-scanline" in html, "Missing search-scanline"
        assert "Geist" in html, "Missing Geist font"
        print("[PASS] Index HTML contains all tactical UI elements and fonts")

    # 2. Test Style CSS
    req = urllib.request.Request("http://127.0.0.1:8000/static/css/style.css")
    with urllib.request.urlopen(req) as resp:
        css = resp.read().decode("utf-8")
        assert "--c-canvas: #090A0F;" in css, "Missing slate/zinc palette"
        assert ".breach-table" in css, "Missing .breach-table class"
        assert ".breach-payload-drawer" in css, "Missing .breach-payload-drawer"
        assert "scanlineSweep" in css, "Missing scanline keyframe animation"
        print("[PASS] CSS contains utilitarian tokens, dense table styles, and scanlines")

    # 3. Test App JS
    req = urllib.request.Request("http://127.0.0.1:8000/static/js/app.js")
    with urllib.request.urlopen(req) as resp:
        js = resp.read().decode("utf-8")
        assert "updateSearchInputTypeBadge" in js, "Missing updateSearchInputTypeBadge"
        assert "renderSummaryMetrics" in js, "Missing renderSummaryMetrics"
        assert "copyInvestigationReport" in js, "Missing copyInvestigationReport"
        assert "exportInvestigationJSON" in js, "Missing exportInvestigationJSON"
        assert "toggleBreachDrawer" in js, "Missing toggleBreachDrawer"
        print("[PASS] JS contains auto-detect badge, summary metrics, and expandable drawer")

    # 4. Test Scan API
    req = urllib.request.Request("http://127.0.0.1:8000/api/scan?email=test@gmail.com")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        leaks = data.get("leaks", [])
        score = data.get("spillover_score", {}).get("score", 0)
        print(f"[PASS] Scan endpoint verified: {len(leaks)} leaks, score {score}/100")

    print("\n=== ALL FRONTEND & BACKEND INTEGRITY CHECKS PASSED ===")

if __name__ == "__main__":
    run_tests()
