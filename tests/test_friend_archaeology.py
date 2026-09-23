#!/usr/bin/env python3
"""
Test Suite: Git Commit Archaeology & Authenticated Stem Prioritization
Validates that:
1. Authentic account logins (e.g. sazeku123) are prioritized over human display names (Jordin).
2. Root stems (sazeku) are probed across platforms with high confidence.
3. Common given names (Jordin) do NOT trigger false-positive registrations.
4. SSH keys are strictly fetched for verified logins, not display names.
5. Graph nodes display visible confidence scores and proper categories.
6. No duplicate platform profile nodes are created.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.main import app, search_exposure
from fastapi.testclient import TestClient

def test_friend_identity_recon():
    print("[*] Testing Friend Identity Recon (sazeku123 / Jordin)...")
    target_email = "jordinzwaan2016@gmail.com"
    client = TestClient(app)
    
    resp = client.get(f"/api/search?email={target_email}&audit_mode=true")
    assert resp.status_code == 200
    data = resp.json()

    pivots = data.get("pivots", [])
    graph_nodes = data.get("graph", {}).get("nodes", [])

    # 1. Authentic GitHub handle sazeku123 must be discovered and present in repositories
    assert any("sazeku123" in p.get("pivot_value", "") for p in pivots), "Authentic handle sazeku123 missing from pivots"
    assert any("commerceai-hub-releases" in p.get("pivot_value", "") for p in pivots), "Repository commerceai-hub-releases missing"

    # 2. Authentic stem sazeku must be discovered on external platforms (Steam, Telegram, Chess.com, Roblox)
    sazeku_platforms = [p.get("pivot_value") for p in pivots if "@sazeku" in p.get("pivot_value", "")]
    assert len(sazeku_platforms) >= 3, f"Expected sazeku external accounts, got: {sazeku_platforms}"
    assert any("Steam: @sazeku" in p for p in sazeku_platforms), "Steam account for sazeku missing"

    # 3. False-positive accounts for generic display name @Jordin MUST NOT exist
    jordin_false_positives = [
        p.get("pivot_value") for p in pivots 
        if any(bad in p.get("pivot_value", "") for bad in [
            "HackerRank: @Jordin", "Pastebin: @Jordin", "Keybase: @Jordin", 
            "Linktree: @Jordin", "Telegram: @Jordin", "Chess.com: @Jordin", "Steam: @Jordin"
        ])
    ]
    assert len(jordin_false_positives) == 0, f"Detected false-positive accounts for @Jordin: {jordin_false_positives}"

    # 4. SSH keys must NOT be pulled from unrelated user github.com/Jordin.keys
    jordin_keys = [p for p in pivots if "GitHub SSH Key: @Jordin" in p.get("pivot_value", "")]
    assert len(jordin_keys) == 0, f"Detected unrelated SSH keys for @Jordin: {jordin_keys}"

    # 5. Verified graph nodes must display confidence percentage badges
    account_nodes = [n for n in graph_nodes if n.get("category") == "accounts" and n.get("group") == "pivot_account"]
    assert len(account_nodes) >= 3, f"Expected at least 3 verified account nodes, found {len(account_nodes)}"
    for node in account_nodes:
        assert "% CONF" in node.get("label", ""), f"Node missing confidence badge: {node.get('label')}"
        assert node.get("data", {}).get("confidence") is not None, "Node data missing confidence float"

    # 5b. Uncorroborated candidate accounts must be segregated into SUSPECTED_ACCOUNT
    suspected_accounts = [p for p in pivots if p.get("pivot_type") == "SUSPECTED_ACCOUNT"]
    assert len(suspected_accounts) >= 3, f"Expected quarantined candidate accounts, got {len(suspected_accounts)}"
    for sa in suspected_accounts:
        assert sa.get("confidence_score", 1.0) <= 0.70, f"Suspected account confidence too high: {sa}"
        assert "[STATUS: SUSPECTED]" in sa.get("context_note", ""), f"Missing suspected status note: {sa}"

    # 5c. Developer account must be explicitly classified as GITHUB DEVELOPER ACCOUNT node
    dev_account_nodes = [n for n in graph_nodes if "[GITHUB DEVELOPER ACCOUNT]" in n.get("label", "")]
    assert len(dev_account_nodes) >= 1, "Expected verified GitHub developer account node on graph"

    # 6. No duplicate Roblox nodes
    roblox_nodes = [n for n in graph_nodes if "ROBLOX" in n.get("label", "").upper()]
    assert len(roblox_nodes) <= 1, f"Found duplicate Roblox nodes: {[n.get('label') for n in roblox_nodes]}"

    print("[+] Friend Identity Recon tests PASSED cleanly!")

if __name__ == "__main__":
    test_friend_identity_recon()
