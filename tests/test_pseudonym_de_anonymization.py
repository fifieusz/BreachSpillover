import unittest
import sqlite3
from unittest.mock import patch, MagicMock

from backend.identity_decomposer import decompose_target_identity, _heuristic_decomposition
from backend.live_osint import derive_candidate_handles
from backend.platform_probes import query_gravatar_handle, query_twitch_channel
from backend.database import get_test_in_memory_db
from backend.osint_scanner import ingest_breaches_to_profile

class TestPseudonymDeAnonymization(unittest.TestCase):

    def test_pseudonym_decomposition_handles_and_dorks(self):
        """Verifies that pseudonymous emails generate clean handles and community/paste dorks rather than corporate LinkedIn queries."""
        res = _heuristic_decomposition("xmister795", None, "gmail.com")
        self.assertTrue(res["is_pseudonym"])
        self.assertIn("xmister795", res["candidate_usernames"])
        self.assertIn("xmister", res["candidate_usernames"])
        self.assertIn("mister", res["candidate_usernames"])

        # Check no domain extensions in candidate usernames
        for u in res["candidate_usernames"]:
            self.assertFalse(any(u.endswith(ext) for ext in [".com", ".net", ".org"]))

        # Check search dorks focus on email, pastes, and community boards
        dork_text = " ".join(res["search_dorks"])
        self.assertIn("xmister795@gmail.com", dork_text)
        self.assertIn("pastebin.com", dork_text)
        self.assertNotIn("linkedin.com/in", dork_text)

    def test_candidate_handle_prefix_stripping(self):
        """Tests that derive_candidate_handles strips x-prefixes and trailing numbers for gamer tags."""
        cands = derive_candidate_handles("xmister795@gmail.com")
        self.assertIn("xmister795", cands)
        self.assertIn("xmister", cands)
        self.assertIn("mister", cands)

    def test_gravatar_handle_probe(self):
        """Tests query_gravatar_handle returns clean structured profile."""
        res = query_gravatar_handle("beau")
        if res:
            self.assertEqual(res["platform"], "Gravatar")
            self.assertTrue(res["is_verified"])
            self.assertIsNotNone(res["display_name"])

    def test_twitch_channel_probe_sanitization(self):
        """Tests query_twitch_channel parses and strips emojis."""
        res = query_twitch_channel("shroud")
        if res:
            self.assertEqual(res["platform"], "Twitch")
            self.assertTrue(res["is_verified"])
            self.assertIn("shroud", res["context"].lower())

    def test_password_spillover_correlation_in_scanner(self):
        """Verifies that cross-identity credential reuse links the pseudonymous target to the corporate entity."""
        conn = get_test_in_memory_db()
        cursor = conn.cursor()

        email1 = "corporate.exec@company.com"
        email2 = "pseudonym.xmister795@gmail.com"
        shared_pwd = "P@ssword2024!SharedSpillover"

        # Insert test leak to satisfy foreign key constraint
        cursor.execute("INSERT OR IGNORE INTO leaks (id, leak_name, leak_type, breach_date, severity) VALUES (9999, 'Test Spillover Leak', 'FORUM', '2023-01-01', 'HIGH')")

        # Insert corporate target who already leaked this password
        cursor.execute("""
            INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level)
            VALUES (?, ?, ?, ?, ?)
        """, ("Alex Petrov", email1, "VP of Engineering", "Engineering", "VP"))
        emp1_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, password_hash, password_pattern, is_corporate_password_match, domain_compromised, global_frequency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (9999, emp1_id, email1, shared_pwd, None, "Shared Pattern", 1, "company.com", 1))

        # Insert pseudonymous target
        cursor.execute("""
            INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level)
            VALUES (?, ?, ?, ?, ?)
        """, ("Xmister795", email2, "Individual", "External", "Individual"))
        emp2_id = cursor.lastrowid
        conn.commit()

        try:
            fake_breach = [{
                "breach_id": "test_leak",
                "breach_name": "Test Stealer Leak",
                "leak_type": "INFOSTEALER",
                "threat_actor_source": "Infostealer Malware C2",
                "exposed_data": ["passwords", "emails"],
                "domain": "testforum.com",
                "top_passwords": [shared_pwd]
            }]

            fake_osint = {
                "primary_name": "Xmister795",
                "discovered_names": ["Xmister795"],
                "discovered_profiles": [],
                "discovered_handles": ["xmister795"],
                "discovered_locations": [],
                "discovered_telecom": []
            }

            with patch("backend.live_osint.execute_deep_live_osint", return_value=fake_osint):
                with patch("backend.identity_decomposer.decompose_target_identity", return_value={"is_pseudonym": True, "full_name": "Xmister795", "primary_handle": "xmister"}):
                    with patch("backend.corporate_recon.query_corporate_registries", return_value={}):
                        with patch("backend.web_dork_recon.execute_ai_dork_recon", return_value={}):
                            with patch("backend.osint_scanner.generate_breach_credential_hash", return_value=("hash123", "pattern", 1)):
                                with patch("backend.browser_runner.auto_enrich_target_from_browser", return_value={"success": False}):
                                    ingest_breaches_to_profile(cursor, emp2_id, email2, "Xmister795", fake_breach)

            # Check that PASSWORD_SPILLOVER_IDENTITY was created for emp2 pointing to Alex Petrov
            cursor.execute("SELECT pivot_type, pivot_value, context_note FROM pivots WHERE employee_id = ? AND pivot_type = 'PASSWORD_SPILLOVER_IDENTITY'", (emp2_id,))
            spillover = cursor.fetchone()
            self.assertIsNotNone(spillover)
            self.assertIn("Alex Petrov", spillover["pivot_value"])
            self.assertIn("corporate.exec@company.com", spillover["pivot_value"])

        finally:
            cursor.execute("DELETE FROM pivots WHERE employee_id IN (?, ?)", (emp1_id, emp2_id))
            cursor.execute("DELETE FROM credentials WHERE employee_id IN (?, ?)", (emp1_id, emp2_id))
            cursor.execute("DELETE FROM employees WHERE id IN (?, ?)", (emp1_id, emp2_id))
            cursor.execute("DELETE FROM leaks WHERE id = 9999")
            conn.commit()
            conn.close()

if __name__ == "__main__":
    unittest.main()
