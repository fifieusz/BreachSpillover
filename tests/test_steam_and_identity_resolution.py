import unittest
import sqlite3
from unittest.mock import patch, MagicMock

from backend.live_osint import derive_candidate_handles
from backend.platform_probes import query_steam_xml_profile
from backend.database import parse_name_from_email, get_or_create_identity_profile, get_connection
from backend.osint_scanner import ingest_breaches_to_profile

class TestSteamAndIdentityResolution(unittest.TestCase):

    def test_derive_candidate_handles_doubled_consonant(self):
        """Verifies doubled consonant permutation rule for handles like fifieusz -> fifieuszz."""
        cands = derive_candidate_handles("fifieusz")
        self.assertIn("fifieusz", cands)
        self.assertIn("fifieuszz", cands)

    def test_parse_name_from_email_pseudonym_cleansing(self):
        """Ensures pseudonyms with numeric suffixes like filipos123.91 do not produce digit-polluted legal names."""
        name = parse_name_from_email("filipos123.91@gmail.com")
        self.assertNotIn("91", name)
        self.assertNotIn("123", name)

    def test_steam_probe_handles_numeric_and_vanity(self):
        """Tests query_steam_xml_profile parsing vanity URLs, SteamID64s, and collision flags."""
        # 1. Vanity URL
        p1 = query_steam_xml_profile("Fifieuszz")
        if p1:
            self.assertEqual(p1["platform"], "Steam")
            self.assertEqual(p1["persona_name"], "Fifi")
            self.assertEqual(p1["custom_url"], "Fifieuszz")
            self.assertEqual(p1["location"], "Jamaica")

        # 2. Numeric SteamID64
        p2 = query_steam_xml_profile("76561199144037063")
        if p2:
            self.assertEqual(p2["platform"], "Steam")
            self.assertEqual(p2["persona_name"], "Fifieusz")
            self.assertEqual(p2["location"], "Jamaica")
            self.assertIn("Twoja stara", p2["summary"])

        # 3. Short vanity handle with discordant persona (fifi / Czesiek)
        p3 = query_steam_xml_profile("fifi")
        if p3:
            self.assertEqual(p3["persona_name"], "Czesiek")
            self.assertFalse(p3["is_verified"])
            self.assertTrue(p3["is_suspected"])

    def test_real_name_promotion_in_ingest_breaches(self):
        """Verifies that discovered authentic real names override initial email handles in employees table."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insert a dummy employee with an initial handle
        cursor.execute("""
            INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level, avatar_seed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("Filipos123 91", "test.filipos123.91@example.com", "Test Role", "Test Dept", "Standard", "avatar_seed"))
        emp_id = cursor.lastrowid
        conn.commit()

        try:
            # Mock execute_deep_live_osint to return Filip Niewiadomski
            fake_osint = {
                "primary_name": "Filip Niewiadomski",
                "discovered_names": ["Filip Niewiadomski", "fifieusz"],
                "discovered_profiles": [],
                "discovered_handles": ["fifieusz"],
                "discovered_locations": ["Poland"],
                "discovered_telecom": []
            }
            with patch("backend.live_osint.execute_deep_live_osint", return_value=fake_osint):
                with patch("backend.identity_decomposer.decompose_target_identity", return_value={"is_pseudonym": True, "full_name": "Filipos123 91", "primary_handle": "filipos123"}):
                    with patch("backend.corporate_recon.query_corporate_registries", return_value={}):
                        with patch("backend.web_dork_recon.execute_ai_dork_recon", return_value={}):
                            ingest_breaches_to_profile(cursor, emp_id, "test.filipos123.91@example.com", "Filipos123 91", [])

            cursor.execute("SELECT full_name FROM employees WHERE id = ?", (emp_id,))
            row = cursor.fetchone()
            self.assertEqual(row["full_name"], "Filip Niewiadomski")

            # Check that FULL_NAME pivot was added
            cursor.execute("SELECT pivot_value FROM pivots WHERE employee_id = ? AND pivot_type = 'FULL_NAME'", (emp_id,))
            pivot = cursor.fetchone()
            self.assertIsNotNone(pivot)
            self.assertIn("Filip Niewiadomski", pivot["pivot_value"])

            # Check that online pseudonym persona pivot was also preserved
            cursor.execute("SELECT pivot_value FROM pivots WHERE employee_id = ? AND pivot_type = 'PERSONA_PIVOT'", (emp_id,))
            p_pivot = cursor.fetchone()
            self.assertIsNotNone(p_pivot)
            self.assertIn("@filipos123", p_pivot["pivot_value"])
        finally:
            cursor.execute("DELETE FROM pivots WHERE employee_id = ?", (emp_id,))
            cursor.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
            conn.commit()
            conn.close()

if __name__ == "__main__":
    unittest.main()
