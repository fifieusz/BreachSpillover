import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.entity_resolution import (
    dissect_email_address,
    calculate_candidate_confidence,
    cluster_discovered_entities
)

class TestEntityResolutionEngine(unittest.TestCase):
    def test_email_dissection_webmail(self):
        res = dissect_email_address("j.o.r.d.i.n.zwaan+alerts2024@gmail.com")
        self.assertEqual(res["domain_type"], "FREE_WEBMAIL")
        self.assertEqual(res["canonical_user"], "jordinzwaan")
        self.assertFalse(res["can_pivot_on_domain"])
        self.assertIn("jordinzwaan", res["candidate_usernames"])

    def test_email_dissection_disposable(self):
        res = dissect_email_address("tempuser99@mailinator.com")
        self.assertEqual(res["domain_type"], "DISPOSABLE_BURNER")
        self.assertFalse(res["can_pivot_on_domain"])

    def test_email_dissection_corporate(self):
        res = dissect_email_address("ceo@acme-defense-corp.io")
        self.assertEqual(res["domain_type"], "CORPORATE_CUSTOM")
        self.assertTrue(res["can_pivot_on_domain"])

    def test_candidate_confidence_exact_email(self):
        cand = {
            "platform": "Gravatar",
            "handle": "jordinzwaan2016",
            "is_email_bound": True
        }
        target = {
            "email": "jordinzwaan2016@gmail.com",
            "full_name": "Jordin Zwaan",
            "primary_handles": ["jordinzwaan2016"]
        }
        res = calculate_candidate_confidence(cand, target)
        self.assertGreaterEqual(res["confidence"], 0.95)
        self.assertTrue(res["can_merge"])
        self.assertIn("Exact Email Authentication (Platform Confirmed)", res["matching_signals"])

    def test_candidate_confidence_given_name_collision(self):
        cand = {
            "platform": "YouTube",
            "handle": "zwaan",
            "name": "John Zwaan",
            "url": "https://www.youtube.com/@zwaan"
        }
        target = {
            "email": "jordinzwaan2016@gmail.com",
            "full_name": "Jordin Zwaan",
            "primary_handles": ["jordinzwaan2016"]
        }
        res = calculate_candidate_confidence(cand, target)
        self.assertLess(res["confidence"], 0.50)
        self.assertFalse(res["can_merge"])
        self.assertTrue(any("Conflicting Given Name" in s for s in res["conflict_signals"]))

    def test_candidate_confidence_demographic_contradiction(self):
        cand = {
            "platform": "Bluesky",
            "handle": "jordin_z",
            "context": "Cybersecurity student (she/her) living in Amsterdam.",
            "url": "https://bsky.app/profile/jordin_z.bsky.social"
        }
        target = {
            "email": "jordinzwaan2016@gmail.com",
            "full_name": "Jordin Zwaan",
            "gender": "male",
            "primary_handles": ["jordinzwaan"]
        }
        res = calculate_candidate_confidence(cand, target)
        self.assertLess(res["confidence"], 0.50)
        self.assertFalse(res["can_merge"])
        self.assertTrue(any("Demographic Contradiction" in s for s in res["conflict_signals"]))

    def test_candidate_confidence_bare_surname_collision(self):
        cand = {
            "platform": "Steam",
            "handle": "zwaan",
            "url": "https://steamcommunity.com/id/zwaan"
        }
        target = {
            "email": "jordinzwaan2016@gmail.com",
            "full_name": "Jordin Zwaan",
            "gender": "male",
            "primary_handles": ["jordinzwaan2016"]
        }
        res = calculate_candidate_confidence(cand, target)
        self.assertLess(res["confidence"], 0.50)
        self.assertFalse(res["can_merge"])
        self.assertTrue(any("Surname Namespace Collision" in s for s in res["conflict_signals"]))

    def test_cluster_discovered_entities_partitioning(self):
        target = {
            "email": "jordinzwaan2016@gmail.com",
            "full_name": "Jordin Zwaan",
            "gender": "male",
            "primary_handles": ["jordinzwaan2016", "sazeku", "sazeku123"],
            "authenticated_handles": ["sazeku", "sazeku123"]
        }
        profiles = [
            {
                "platform": "GitHub",
                "handle": "sazeku123",
                "url": "https://github.com/sazeku123",
                "is_commit_bound": True
            },
            {
                "platform": "LinkedIn",
                "handle": "jordin-zwaan",
                "name": "Jordin Zwaan",
                "url": "https://linkedin.com/in/jordin-zwaan"
            },
            {
                "platform": "YouTube",
                "handle": "zwaan",
                "name": "John Zwaan",
                "url": "https://youtube.com/@zwaan"
            }
        ]
        pivots = [
            {
                "pivot_type": "PUBLIC_PROFILE",
                "pivot_value": "GitHub: @sazeku123",
                "context_note": "Authenticated GitHub developer account [STATUS: VERIFIED]"
            },
            {
                "pivot_type": "PUBLIC_PROFILE",
                "pivot_value": "YouTube: @zwaan",
                "context_note": "Public YouTube Creator Channel: John Zwaan [URL: https://youtube.com/@zwaan] [STATUS: VERIFIED]"
            }
        ]

        clusters = cluster_discovered_entities(target, profiles, pivots)
        all_c = clusters["all_clusters"]
        cand_c = clusters["candidate_clusters"]

        # Primary cluster should contain authenticated GitHub
        self.assertEqual(clusters["primary_entity"]["cluster_id"], "persona_target")
        self.assertTrue(any(p["handle"] == "sazeku123" for p in clusters["primary_entity"]["profiles"]))

        # Candidate clusters should isolate John Zwaan
        namesake_clusters = [c for c in cand_c if c["cluster_type"] == "NAMESAKE_COLLISION"]
        self.assertGreaterEqual(len(namesake_clusters), 1)
        self.assertTrue(any("John" in c["cluster_label"] for c in namesake_clusters))

        # Check John Zwaan pivot was stripped of fake VERIFIED status
        john_pivots = namesake_clusters[0]["pivots"]
        self.assertGreaterEqual(len(john_pivots), 1)
        self.assertEqual(john_pivots[0]["pivot_type"], "SUSPECTED_ACCOUNT")
        self.assertIn("[STATUS: NAMESAKE_COLLISION]", john_pivots[0]["context_note"])
        self.assertLessEqual(john_pivots[0]["confidence_score"], 0.40)

    def test_osint_local_target_and_semantic_query_verification(self):
        from backend.email_verifier import verify_email_address
        # Verify that synthetic OSINT targets pass verification cleanly
        res = verify_email_address("alex.morgan@osint.local")
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["status"], "OSINT_TARGET")

        # Verify that complex semantic role query sanitization works
        from backend.main import search_exposure
        query = "Role: Grunnskolelærer (primary school teacher) at Norwegian primary/secondary education system"
        api_res = search_exposure(email=query, query=None)
        self.assertTrue(api_res["email_verification"]["is_valid"])
        self.assertEqual(api_res["email_verification"]["status"], "OSINT_TARGET")

    def test_alias_persona_clustering_and_media_segregation(self):
        target = {
            "email": "jordinzwaan2016@gmail.com",
            "full_name": "Jordin Zwaan",
            "gender": "male",
            "primary_handles": ["jordinzwaan2016", "jordinzwaan"],
            "authenticated_handles": ["sazeku123", "sazeku"]
        }
        pivots = [
            {
                "pivot_type": "PUBLIC_PROFILE",
                "pivot_value": "GitHub: @sazeku123",
                "context_note": "Authenticated GitHub developer account [author commit] [STATUS: VERIFIED]"
            },
            {
                "pivot_type": "SUSPECTED_ACCOUNT",
                "pivot_value": "Telegram: @sazeku",
                "context_note": "Unverified candidate lead on Telegram [STATUS: SUSPECTED]"
            },
            {
                "pivot_type": "SUSPECTED_ACCOUNT",
                "pivot_value": "Steam: @Sazeku (Persona: 'Poes')",
                "context_note": "Steam gaming profile with alternate persona [STATUS: SUSPECTED]"
            },
            {
                "pivot_type": "SUSPECTED_ACCOUNT",
                "pivot_value": "Chess.com: @poes",
                "context_note": "Speculative chess profile [STATUS: SUSPECTED]"
            },
            {
                "pivot_type": "AVATAR_CORRELATION",
                "pivot_value": "Secondary Visual Footprint (LinkedIn): https://media.licdn.com/dms/image/avatar1.jpg",
                "confidence_score": 0.75,
                "context_note": "Visual candidate asset [URL: https://media.licdn.com/dms/image/avatar1.jpg] [STATUS: SECONDARY AVATAR]"
            }
        ]

        clusters = cluster_discovered_entities(target, [], pivots)
        cand_labels = [c["cluster_label"] for c in clusters["candidate_clusters"]]

        # 1. Aliases @sazeku and @poes must form distinct candidate persona clusters
        self.assertIn("@sazeku", cand_labels)
        self.assertIn("@poes", cand_labels)

        # 2. AVATAR_CORRELATION must be in persona_target and NOT in candidate persona buckets
        for c in clusters["candidate_clusters"]:
            media_pivots = [p for p in c.get("pivots", []) if p.get("pivot_type") == "AVATAR_CORRELATION"]
            self.assertEqual(len(media_pivots), 0, f"Found leaked media pivots in candidate cluster {c['cluster_label']}")

        primary_media = [p for p in clusters["primary_entity"].get("pivots", []) if p.get("pivot_type") == "AVATAR_CORRELATION"]
        self.assertEqual(len(primary_media), 1)

if __name__ == "__main__":
    unittest.main()
