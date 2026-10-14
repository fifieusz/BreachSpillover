"""
Unit tests validating authentic raw credential processing in BreachSpillover.
Ensures:
1. No synthetic bcrypt/SHA hashes are fabricated when breaches only disclose metadata.
2. Authentic raw passwords (infostealers, combolists) are preserved in cleartext.
3. Database contains zero synthetic bcrypt hashes without plaintext.
"""

import unittest
from unittest.mock import patch
from backend.database import get_connection
from backend.osint_scanner import ingest_breaches_to_profile


class TestRawCredentials(unittest.TestCase):

    def setUp(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        self.cursor.execute("DELETE FROM credentials WHERE username_or_email IN ('test.metadata.target@security-example.com', 'stealer.target@security-example.com')")
        self.cursor.execute("DELETE FROM pivots WHERE employee_id IN (SELECT id FROM employees WHERE corporate_email IN ('test.metadata.target@security-example.com', 'stealer.target@security-example.com'))")
        self.cursor.execute("DELETE FROM employees WHERE corporate_email IN ('test.metadata.target@security-example.com', 'stealer.target@security-example.com')")
        self.conn.commit()

        self.fake_osint = {
            "primary_name": "Target",
            "discovered_names": ["Target"],
            "discovered_profiles": [],
            "discovered_handles": ["target"],
            "discovered_locations": [],
            "discovered_telecom": []
        }

    def tearDown(self):
        self.conn.close()

    def test_metadata_only_breach_generates_no_synthetic_credentials(self):
        """Verifies that breaches with password metadata do NOT insert fake $2a$10$ hashes."""
        test_email = "test.metadata.target@security-example.com"
        
        self.cursor.execute("""
            INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level)
            VALUES (?, ?, ?, ?, ?)
        """, ("Metadata Target", test_email, "Analyst", "Security", "Individual"))
        emp_id = self.cursor.lastrowid
        self.conn.commit()

        try:
            metadata_breach = [{
                "breach_id": "coll1_test",
                "breach_name": "Collection-1 Metadata Test",
                "leak_type": "FORUM",
                "breach_date": "2019-01-07",
                "description": "Exfiltrated metadata list",
                "threat_actor_source": "Aggregated Disclosure",
                "severity": "HIGH",
                "domain": "armorgames.com",
                "exposed_data": ["Passwords", "Email addresses", "Usernames"]
            }]

            with patch("backend.live_osint.execute_deep_live_osint", return_value=self.fake_osint):
                with patch("backend.identity_decomposer.decompose_target_identity", return_value={"is_pseudonym": False, "full_name": "Metadata Target", "primary_handle": "target"}):
                    with patch("backend.corporate_recon.query_corporate_registries", return_value={}):
                        with patch("backend.web_dork_recon.execute_ai_dork_recon", return_value={}):
                            with patch("backend.footprint_recon.execute_universal_footprint_recon", return_value={}):
                                with patch("backend.wmn_engine.enumerate_handle_wmn", return_value={"matches": []}):
                                    with patch("backend.browser_runner.auto_enrich_target_from_browser", return_value={"success": False}):
                                        with patch("backend.image_recon.reconcile_and_store_target_images", return_value=None):
                                            with patch("backend.image_recon.harvest_target_images", return_value=[]):
                                                ingest_breaches_to_profile(self.cursor, emp_id, test_email, "Metadata Target", metadata_breach)
            self.conn.commit()

            # Verify: NO credentials should be inserted
            self.cursor.execute("SELECT * FROM credentials WHERE employee_id = ?", (emp_id,))
            creds = self.cursor.fetchall()
            self.assertEqual(len(creds), 0, "No synthetic credentials should be inserted for metadata-only breaches!")

            # Verify: Honest disclosure pivot should be recorded
            self.cursor.execute("SELECT * FROM pivots WHERE employee_id = ? AND pivot_type = 'PASSWORD_COMPROMISE_DISCLOSURE'", (emp_id,))
            disclosures = self.cursor.fetchall()
            self.assertEqual(len(disclosures), 1)
            self.assertIn("Collection-1 Metadata Test", disclosures[0]["pivot_value"])

        finally:
            self.cursor.execute("DELETE FROM credentials WHERE employee_id = ?", (emp_id,))
            self.cursor.execute("DELETE FROM pivots WHERE employee_id = ?", (emp_id,))
            self.cursor.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
            self.conn.commit()

    def test_genuine_raw_passwords_stored_verbatim(self):
        """Verifies that authentic raw passwords from stealer dumps or combolists are stored as cleartext."""
        test_email = "stealer.target@security-example.com"
        raw_secret = "AuthenticCleartextP@ssw0rd!2026"

        self.cursor.execute("""
            INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level)
            VALUES (?, ?, ?, ?, ?)
        """, ("Stealer Target", test_email, "Developer", "IT", "Individual"))
        emp_id = self.cursor.lastrowid
        self.conn.commit()

        try:
            stealer_breach = [{
                "breach_id": "redline_c2_test",
                "breach_name": "Redline Infostealer C2 Dump",
                "leak_type": "INFOSTEALER",
                "breach_date": "2026-02-14",
                "description": "Endpoint infection memory dump",
                "threat_actor_source": "Hudson Rock Cybercrime Intelligence",
                "severity": "CRITICAL",
                "domain": "victim-workstation.local",
                "exposed_data": ["Passwords", "Browser Cookies"],
                "top_passwords": [raw_secret]
            }]

            with patch("backend.live_osint.execute_deep_live_osint", return_value=self.fake_osint):
                with patch("backend.identity_decomposer.decompose_target_identity", return_value={"is_pseudonym": False, "full_name": "Stealer Target", "primary_handle": "target"}):
                    with patch("backend.corporate_recon.query_corporate_registries", return_value={}):
                        with patch("backend.web_dork_recon.execute_ai_dork_recon", return_value={}):
                            with patch("backend.footprint_recon.execute_universal_footprint_recon", return_value={}):
                                with patch("backend.wmn_engine.enumerate_handle_wmn", return_value={"matches": []}):
                                    with patch("backend.browser_runner.auto_enrich_target_from_browser", return_value={"success": False}):
                                        with patch("backend.image_recon.reconcile_and_store_target_images", return_value=None):
                                            with patch("backend.image_recon.harvest_target_images", return_value=[]):
                                                ingest_breaches_to_profile(self.cursor, emp_id, test_email, "Stealer Target", stealer_breach)
            self.conn.commit()

            # Verify: Credential row exists with authentic plaintext password
            self.cursor.execute("SELECT plaintext_password, password_hash, password_pattern FROM credentials WHERE employee_id = ?", (emp_id,))
            creds = self.cursor.fetchall()
            self.assertEqual(len(creds), 1)
            self.assertEqual(creds[0]["plaintext_password"], raw_secret)
            self.assertIsNone(creds[0]["password_hash"])
            self.assertIn("Infostealer Exfiltrated Plaintext", creds[0]["password_pattern"])

        finally:
            self.cursor.execute("DELETE FROM credentials WHERE employee_id = ?", (emp_id,))
            self.cursor.execute("DELETE FROM pivots WHERE employee_id = ?", (emp_id,))
            self.cursor.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
            self.conn.commit()

    def test_database_contains_zero_synthetic_bcrypt_hashes(self):
        """Verifies database contains zero synthetic bcrypt hashes across all credentials."""
        # 1. Direct SQLite verification of zero synthetic bcrypt hashes without plaintext
        self.cursor.execute("SELECT COUNT(1) FROM credentials WHERE password_hash LIKE '$2a$10$%' AND plaintext_password IS NULL")
        synthetic_count = self.cursor.fetchone()[0]
        self.assertEqual(synthetic_count, 0, "No synthetic bcrypt hashes should exist in the credentials table!")

        # 2. Check phizo22 profile if present in employees table
        self.cursor.execute("SELECT id FROM employees WHERE corporate_email LIKE '%phizo22%'")
        row = self.cursor.fetchone()
        if row:
            emp_id = row[0]
            self.cursor.execute("SELECT password_hash, plaintext_password FROM credentials WHERE employee_id = ?", (emp_id,))
            phizo_creds = self.cursor.fetchall()
            for c in phizo_creds:
                p_hash = c["password_hash"] or ""
                self.assertFalse(p_hash.startswith("$2a$10$"), f"Found synthetic bcrypt hash for phizo22: {p_hash}")

        # 3. Global verification of synthetic pattern records
        self.cursor.execute("""
            SELECT COUNT(1) FROM credentials 
            WHERE password_pattern IN ('Cryptographic Hashed Secret Record', 'Salted Bcrypt Hash ($2a$10$)')
        """)
        self.assertEqual(self.cursor.fetchone()[0], 0, "No synthetic pattern credentials should remain!")

    def test_search_exposure_distinguishes_raw_and_disclosures(self):
        """Verifies that search_exposure separates raw plaintext credentials from breach password disclosures."""
        from backend.main import search_exposure

        # Test A: Target with confirmed password breach disclosures (metadata only, no raw payload in DB)
        res_phizo = search_exposure("phizo22@gmail.com")
        disclosures = res_phizo.get("password_disclosures", [])
        self.assertGreater(len(disclosures), 0, "Expected password disclosures for phizo22@gmail.com!")
        for d in disclosures:
            self.assertTrue(bool(d.get("leak_name")))
            self.assertTrue(bool(d.get("threat_actor_source")))
            self.assertIn("reason_undelivered", d)
            self.assertIn("public breach verification APIs legally only publish compromise notices", d["reason_undelivered"])

        # Test B: Target with genuine raw plaintext credentials
        res_alex = search_exposure("alex.morgan@cybercorp.io")
        creds_alex = res_alex.get("credentials", [])
        self.assertGreater(len(creds_alex), 0, "Expected raw credentials for alex.morgan@cybercorp.io!")
        for c in creds_alex:
            self.assertEqual(c.get("secret_type"), "RAW_PLAINTEXT")
            self.assertTrue(bool(c.get("plaintext_password")))
            self.assertIn("Direct cleartext", c.get("origin_description", ""))
            self.assertIn("No cryptographic hashing was applied", c.get("why_status", ""))


if __name__ == "__main__":
    unittest.main()

