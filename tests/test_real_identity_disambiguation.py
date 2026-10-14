"""
Unit tests validating Real Identity Recovery and Disambiguation in BreachSpillover:
1. Compound onomastic handle splitting (e.g. 'islamzerdab' -> Islam Zerdab, 'hakimazer1974' -> Hakim Azer).
2. Birth-year / temporal age extraction (e.g. 1974 -> age 52).
3. Cryptographic Git commit author inversion (Author: Name <email>).
4. Direct Duolingo and Gravatar public email-bound profile lookups.
5. Credential lake spillover bridge across shared unique passwords.
6. Strict multi-tier segregation: Verified Real vs Most Plausible vs Namesake Collisions vs Co-Device Affiliates.
"""

import unittest
import json
from unittest.mock import patch, MagicMock

from backend.onomastic_engine import (
    deconstruct_onomastic_handle,
    extract_handle_temporal_anchor,
    estimate_namesake_collision_risk
)
from backend.profile_enricher import (
    query_github_commit_author,
    query_duolingo_by_email,
    query_gravatar_by_email,
    query_pgp_keyserver_by_email,
    query_keybase_by_email,
    query_credential_lake_reuse_bridge,
    enrich_email_identity,
    TIER_AUTHENTICATED
)
from backend.entity_resolution import (
    cluster_discovered_entities,
    assess_candidate_evidence,
    TIER_CONTRADICTED
)
from backend.database import get_test_in_memory_db
from backend.osint_scanner import ingest_breaches_to_profile


class TestRealIdentityDisambiguation(unittest.TestCase):

    def test_unpunctuated_compound_onomastics_arabic_north_african(self):
        """Verifies decomposition of unpunctuated compound handles (islamzerdab, hakimazer1974, hakima1974)."""
        # 1. Islam Zerdab
        res_islam = deconstruct_onomastic_handle("islamzerdab@gmail.com")
        self.assertFalse(res_islam["is_pseudonym"])
        self.assertEqual(res_islam["given_name"], "Islam")
        self.assertEqual(res_islam["family_name"], "Zerdab")
        self.assertEqual(res_islam["full_name"], "Islam Zerdab")
        self.assertIn("Arabic / North African", res_islam["culture_hint"])

        # 2. Hakim Azer (with 1974 birth year)
        res_hakim = deconstruct_onomastic_handle("hakimazer1974@gmail.com")
        self.assertFalse(res_hakim["is_pseudonym"])
        self.assertEqual(res_hakim["given_name"], "Hakim")
        self.assertEqual(res_hakim["family_name"], "Azer")
        self.assertEqual(res_hakim["full_name"], "Hakim Azer")
        self.assertEqual(res_hakim["birth_year"], 1974)
        self.assertEqual(res_hakim["estimated_age"], 52)
        self.assertEqual(res_hakim["perceived_gender"], "male")

        # 3. Hakima (female given name with 1974 birth year)
        res_hakima = deconstruct_onomastic_handle("hakima1974@gmail.com")
        self.assertFalse(res_hakima["is_pseudonym"])
        self.assertEqual(res_hakima["given_name"], "Hakima")
        self.assertIsNone(res_hakima["family_name"])
        self.assertEqual(res_hakima["birth_year"], 1974)
        self.assertEqual(res_hakima["perceived_gender"], "female")

    def test_dutch_particle_and_gamer_tag_distinction(self):
        """Verifies particle splits for Dutch names and pseudonym detection for gamer handles."""
        res_dutch = deconstruct_onomastic_handle("jandevries@gmail.com")
        self.assertEqual(res_dutch["full_name"], "Jan de Vries")
        self.assertEqual(res_dutch["family_name"], "de Vries")
        self.assertFalse(res_dutch["is_pseudonym"])

        res_gamer = deconstruct_onomastic_handle("xmister795@gmail.com")
        self.assertTrue(res_gamer["is_pseudonym"])
        self.assertEqual(res_gamer["primary_handle"], "xmister")

    def test_namesake_collision_risk_quantification(self):
        """Verifies collision risk scoring: common global names flagged for strict disambiguation."""
        risk_common = estimate_namesake_collision_risk("Mohamed Ali")
        self.assertTrue(risk_common["requires_strict_disambiguation"])
        self.assertIn("CRITICAL_COLLISION", risk_common["risk_tier"])

        risk_distinctive = estimate_namesake_collision_risk("Islam Zerdab")
        self.assertEqual(risk_distinctive["risk_tier"], "MODERATE_DISTINCTIVE")

    @patch("urllib.request.urlopen")
    def test_github_commit_author_inversion(self, mock_urlopen):
        """Verifies cryptographic inversion of Git commit author email to real legal name."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_json = {
            "items": [
                {
                    "commit": {
                        "author": {
                            "name": "Hakim Azer",
                            "email": "hakimazer1974@gmail.com",
                            "date": "2023-04-12T10:15:30Z"
                        }
                    },
                    "author": {
                        "login": "hakimazer"
                    },
                    "repository": {
                        "full_name": "hakimazer/infra-tooling"
                    }
                }
            ]
        }
        mock_resp.read.return_value = json.dumps(mock_json).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = query_github_commit_author("hakimazer1974@gmail.com")
        self.assertIsNotNone(res)
        self.assertEqual(res["author_name"], "Hakim Azer")
        self.assertEqual(res["github_username"], "hakimazer")
        self.assertEqual(res["evidence_tier"], TIER_AUTHENTICATED)
        self.assertTrue(res["is_email_bound"])
        self.assertTrue(res["is_commit_bound"])

    @patch("urllib.request.urlopen")
    def test_duolingo_public_email_lookup(self, mock_urlopen):
        """Verifies Duolingo public email lookup returns registered user display name and courses."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_json = {
            "users": [
                {
                    "name": "Islam Zerdab",
                    "username": "islamzerdab",
                    "picture": "https://s3.amazonaws.com/duolingo-images/avatar_123.jpg",
                    "courses": [{"title": "French"}, {"title": "English"}],
                    "streak": 45
                }
            ]
        }
        mock_resp.read.return_value = json.dumps(mock_json).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = query_duolingo_by_email("islamzerdab@gmail.com")
        self.assertIsNotNone(res)
        self.assertEqual(res["real_name"], "Islam Zerdab")
        self.assertEqual(res["username"], "islamzerdab")
        self.assertIn("French", res["courses"])
        self.assertEqual(res["evidence_tier"], TIER_AUTHENTICATED)
        self.assertTrue(res["is_email_bound"])

    @patch("urllib.request.urlopen")
    def test_gravatar_profile_email_lookup(self, mock_urlopen):
        """Verifies Gravatar lookup extracts real name and verified external accounts."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_json = {
            "entry": [
                {
                    "displayName": "Hakim Azer",
                    "name": {"givenName": "Hakim", "familyName": "Azer"},
                    "currentLocation": "Algiers, Algeria",
                    "thumbnailUrl": "https://secure.gravatar.com/avatar/hash.jpg",
                    "verifiedAccounts": [{"service_type": "github", "url": "https://github.com/hakimazer"}]
                }
            ]
        }
        mock_resp.read.return_value = json.dumps(mock_json).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = query_gravatar_by_email("hakimazer1974@gmail.com")
        self.assertIsNotNone(res)
        self.assertEqual(res["real_name"], "Hakim Azer")
        self.assertEqual(res["location"], "Algiers, Algeria")
        self.assertEqual(res["evidence_tier"], TIER_AUTHENTICATED)

    def test_credential_lake_reuse_bridge(self):
        """Verifies cross-identity credential reuse links an opaque email to a corporate profile."""
        conn = get_test_in_memory_db()
        cursor = conn.cursor()

        cursor.execute("INSERT OR IGNORE INTO leaks (id, leak_name, leak_type, breach_date, severity) VALUES (8888, 'Corporate VPN Leak', 'VPN', '2024-02-10', 'CRITICAL')")

        cursor.execute("""
            INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level)
            VALUES (?, ?, ?, ?, ?)
        """, ("Hakim Azer", "h.azer@corporate-enterprise.com", "DevOps Engineer", "IT Infrastructure", "Individual"))
        corp_emp_id = cursor.lastrowid

        shared_password = "P@ssword2024!UniqueCorporatePhrase"
        cursor.execute("""
            INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, is_corporate_password_match, domain_compromised)
            VALUES (?, ?, ?, ?, 1, 'corporate-enterprise.com')
        """, (8888, corp_emp_id, "h.azer@corporate-enterprise.com", shared_password))

        cursor.execute("""
            INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level)
            VALUES (?, ?, ?, ?, ?)
        """, ("Target User", "hakimazer1974@gmail.com", "External", "External", "Individual"))
        target_emp_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, is_corporate_password_match, domain_compromised)
            VALUES (?, ?, ?, ?, 0, 'gmail.com')
        """, (8888, target_emp_id, "hakimazer1974@gmail.com", shared_password))
        conn.commit()

        try:
            bridge = query_credential_lake_reuse_bridge("hakimazer1974@gmail.com", cursor=cursor)
            self.assertIsNotNone(bridge)
            self.assertEqual(bridge["real_name"], "Hakim Azer")
            self.assertEqual(bridge["bridged_email"], "h.azer@corporate-enterprise.com")
            self.assertEqual(bridge["evidence_tier"], TIER_AUTHENTICATED)
        finally:
            conn.close()

    def test_strict_namesake_segregation_by_geographic_divergence(self):
        """Verifies that public profiles matching target name in a conflicting location are quarantined as namesakes."""
        target_info = {
            "email": "hakimazer1974@gmail.com",
            "full_name": "Hakim Azer",
            "locations": ["Algiers", "Algeria"],
            "primary_handles": ["hakimazer1974", "hakimazer"]
        }

        # Candidate with same full name but located in Australia without email binding
        cand_namesake = {
            "platform": "LinkedIn",
            "handle": "hakim-azer-sydney",
            "name": "Hakim Azer",
            "location": "Sydney, Australia",
            "context": "Civil Engineer at Sydney Construction based in Sydney, Australia",
            "url": "https://linkedin.com/in/hakim-azer-sydney",
            "is_email_bound": False,
            "is_commit_bound": False
        }

        ev = assess_candidate_evidence(cand_namesake, target_info)
        self.assertEqual(ev["evidence_tier"], TIER_CONTRADICTED)
        self.assertFalse(ev["can_merge"])
        self.assertTrue(any("Geographic Location Divergence" in c for c in ev["conflict_signals"]))

        # Clustering should route this to NAMESAKE_COLLISION, never CONFIRMED_PRIMARY
        clusters = cluster_discovered_entities(target_info, [cand_namesake], [])
        primary = clusters["primary_entity"]
        self.assertEqual(len(primary["profiles"]), 0)

        namesake_clusters = [c for c in clusters["candidate_clusters"] if c["cluster_type"] == "NAMESAKE_COLLISION"]
        self.assertGreaterEqual(len(namesake_clusters), 1)
        self.assertTrue(any("Hakim" in c["cluster_label"] for c in namesake_clusters))

    def test_co_device_household_account_segregation(self):
        """Verifies that accounts from the same physical machine (co-device) are segregated into household cluster."""
        target_info = {
            "email": "hakimazer1974@gmail.com",
            "full_name": "Hakim Azer",
            "primary_handles": ["hakimazer1974"]
        }

        # Co-device email from infostealer session
        co_device_pivot = {
            "pivot_type": "SUSPECTED_ACCOUNT",
            "pivot_value": "Shared Device Account: hakima1974@gmail.com",
            "context_note": "Associated entity on same physical device in infostealer dump. [PLATFORM: CO_DEVICE] [STATUS: SUSPECTED] [STATUS: CO_DEVICE_AFFILIATE]"
        }

        clusters = cluster_discovered_entities(target_info, [], [co_device_pivot])
        co_clusters = [c for c in clusters["candidate_clusters"] if c["cluster_type"] == "CO_DEVICE_AFFILIATE"]
        self.assertGreaterEqual(len(co_clusters), 1)
        self.assertIn("Shared Device", co_clusters[0]["cluster_label"])

    def test_multi_numeric_temporal_suppression(self):
        """Verifies that arbitrary multi-number handles (like filipos123.91) suppress false birth years."""
        # Multi-number handle: "123" + "91" is random numbers, NOT a birth year
        res_multi = extract_handle_temporal_anchor("filipos123.91@gmail.com")
        self.assertFalse(res_multi["has_birth_year"])
        self.assertIsNone(res_multi["birth_year"])
        self.assertEqual(res_multi["clean_stem"], "filipos")
        self.assertTrue(res_multi.get("is_arbitrary_numeric"))

        # Clean 2-digit handle: "filipos91" -> speculative 1991 (confidence: SPECULATIVE)
        res_clean2 = extract_handle_temporal_anchor("filipos91@gmail.com")
        self.assertTrue(res_clean2["has_birth_year"])
        self.assertEqual(res_clean2["birth_year"], 1991)
        self.assertEqual(res_clean2["confidence"], "SPECULATIVE")
        self.assertTrue(res_clean2["is_speculative"])

        # Clean 4-digit handle: "hakimazer1974" -> high confidence 1974 (confidence: HIGH)
        res_clean4 = extract_handle_temporal_anchor("hakimazer1974@gmail.com")
        self.assertTrue(res_clean4["has_birth_year"])
        self.assertEqual(res_clean4["birth_year"], 1974)
        self.assertEqual(res_clean4["confidence"], "HIGH")
        self.assertFalse(res_clean4["is_speculative"])

    @patch("urllib.request.urlopen")
    def test_pgp_keyserver_query(self, mock_urlopen):
        """Verifies OpenPGP public keyserver lookup unmasks real legal name."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"""
        <html><body>
        <hr /><pre><strong>pub</strong> <a href="/pks/lookup?op=get&search=0x5b45863e83fa9a00">rsa2048/5b45863e83fa9a00</a>
        <strong>uid</strong> <span class="uid">Filip Niewiadomski (Developer) &lt;filipos123.91@gmail.com&gt;</span>
        </pre></body></html>
        """
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = query_pgp_keyserver_by_email("filipos123.91@gmail.com")
        self.assertIsNotNone(res)
        self.assertEqual(res["real_name"], "Filip Niewiadomski")
        self.assertEqual(res["evidence_tier"], TIER_AUTHENTICATED)
        self.assertGreaterEqual(res["confidence"], 0.98)
        self.assertTrue(res["is_email_bound"])

    @patch("urllib.request.urlopen")
    def test_keybase_user_lookup(self, mock_urlopen):
        """Verifies Keybase user lookup unmasks verified profile name and location."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "status": {"code": 0, "name": "OK"},
            "them": [{
                "basics": {"username": "filipos"},
                "profile": {"full_name": "Filip Niewiadomski", "location": "Warsaw, Poland"},
                "pictures": {"primary": {"url": "https://keybase.io/avatar.png"}},
                "proofs_summary": {
                    "all": [{"proof_type": "github", "nametag": "filip-gh", "service_url": "https://github.com/filip-gh"}]
                }
            }]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = query_keybase_by_email("filipos123.91@gmail.com")
        self.assertIsNotNone(res)
        self.assertEqual(res["real_name"], "Filip Niewiadomski")
        self.assertEqual(res["username"], "filipos")
        self.assertEqual(res["location"], "Warsaw, Poland")
        self.assertEqual(res["evidence_tier"], TIER_AUTHENTICATED)
        self.assertEqual(len(res["verified_proofs"]), 1)


if __name__ == "__main__":
    unittest.main()

