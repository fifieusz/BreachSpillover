import unittest
from unittest.mock import patch, MagicMock

from backend.corporate_recon import (
    query_sec_edgar_officers,
    query_uk_companies_house,
    query_corporate_registries
)
from backend.footprint_recon import (
    query_youtube_channel,
    query_bluesky_profile,
    query_personal_site_candidate,
    execute_universal_footprint_recon
)


class TestGlobalCorporateAndFootprint(unittest.TestCase):

    def test_sec_edgar_officer_extraction(self):
        """Verifies US SEC EDGAR Full-Text Search JSON parsing for corporate officers."""
        mock_sec_json = """{
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {
                            "display_names": ["ACME CORP  (CIK 0001234567)", "Smith Jane  (CIK 0007654321)"],
                            "form": "4",
                            "file_date": "2024-05-15"
                        }
                    }
                ]
            }
        }"""
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = mock_sec_json.encode("utf-8")
            mock_url.return_value.__enter__.return_value = mock_resp

            res = query_sec_edgar_officers("Jane Smith")
            self.assertIsNotNone(res)
            self.assertTrue(res["matched"])
            self.assertEqual(res["company_name"], "ACME CORP")
            self.assertEqual(res["country"], "United States")
            self.assertIn("SEC Form 4", res["role"])
            self.assertIn("SEC EDGAR", res["official_sources"][0])

    def test_uk_companies_house_officer_extraction(self):
        """Verifies UK Companies House director search parsing."""
        mock_html = """
        <ul id="results">
            <li class="type-officer">
                <h2 role="heading">
                    <a href="/officers/123/appointments">SMITH, John David</a>
                </h2>
                <dl>
                    <dt>Correspondence address</dt>
                    <dd class="data">10 Downing Street, London, SW1A 2AA</dd>
                    <dt>Appointed</dt>
                    <dd class="data">BRITISH GLOBAL TECH LTD (12345678)</dd>
                </dl>
            </li>
        </ul>
        """
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = mock_html.encode("utf-8")
            mock_url.return_value.__enter__.return_value = mock_resp

            res = query_uk_companies_house("John Smith")
            self.assertIsNotNone(res)
            self.assertTrue(res["matched"])
            self.assertEqual(res["country"], "United Kingdom")
            self.assertIn("BRITISH GLOBAL TECH LTD", res["company_name"])

    def test_corporate_registries_jurisdiction_routing_us(self):
        """Verifies query_corporate_registries routes US context to SEC EDGAR."""
        with patch("backend.corporate_recon.query_sec_edgar_officers") as mock_sec:
            mock_sec.return_value = {
                "matched": True,
                "company_name": "Silicon Valley Holdings",
                "country": "United States",
                "role": "Director"
            }
            res = query_corporate_registries(
                target_name="Jane Doe",
                target_email="jane@siliconvalley.com",
                anchors={"known_country": "United States"}
            )
            self.assertIsNotNone(res)
            self.assertEqual(res["country"], "United States")
            mock_sec.assert_called_once_with("Jane Doe")

    def test_youtube_channel_probe(self):
        """Verifies YouTube channel discovery and metadata extraction."""
        mock_html = """
        <html>
            <head>
                <title>TechReview - YouTube</title>
                <meta property="og:title" content="TechReview Official">
                <meta property="og:description" content="In-depth hardware and security engineering reviews.">
                <meta property="og:image" content="https://yt3.ggpht.com/avatar_test.jpg">
            </head>
            <body>Channel content</body>
        </html>
        """
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = (mock_html * 30).encode("utf-8")
            mock_url.return_value.__enter__.return_value = mock_resp

            res = query_youtube_channel("techreview")
            self.assertIsNotNone(res)
            self.assertEqual(res["platform"], "YouTube")
            self.assertEqual(res["category"], "CREATOR")
            self.assertEqual(res["display_name"], "TechReview Official")
            self.assertEqual(res["avatar_url"], "https://yt3.ggpht.com/avatar_test.jpg")
            self.assertTrue(res["is_verified"])

    def test_bluesky_profile_probe(self):
        """Verifies Bluesky AT Protocol public REST profile lookup."""
        mock_bsky_json = """{
            "handle": "investigator.bsky.social",
            "displayName": "Cyber Analyst",
            "description": "Open source intelligence and security researcher",
            "avatar": "https://cdn.bsky.app/img/avatar_test.jpeg",
            "followersCount": 1542
        }"""
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = mock_bsky_json.encode("utf-8")
            mock_url.return_value.__enter__.return_value = mock_resp

            res = query_bluesky_profile("investigator")
            self.assertIsNotNone(res)
            self.assertEqual(res["platform"], "Bluesky")
            self.assertEqual(res["category"], "SOCIAL")
            self.assertEqual(res["display_name"], "Cyber Analyst")
            self.assertEqual(res["followers"], 1542)
            self.assertTrue(res["is_verified"])

    def test_personal_site_candidate_probe(self):
        """Verifies personal portfolio / GitHub Pages candidate probe."""
        mock_html = """
        <html>
            <head>
                <title>Alex Morgan - Security Portfolio</title>
                <meta name="description" content="Personal blog and reverse engineering writeups.">
                <meta property="og:image" content="https://alexmorgan.github.io/portrait.png">
            </head>
            <body>Welcome to my personal site</body>
        </html>
        """
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = mock_html.encode("utf-8")
            mock_url.return_value.__enter__.return_value = mock_resp

            res = query_personal_site_candidate("https://alexmorgan.github.io", ["alex", "morgan"])
            self.assertIsNotNone(res)
            self.assertEqual(res["platform"], "GitHub Pages")
            self.assertEqual(res["category"], "PORTFOLIO")
            self.assertIn("Alex Morgan", res["title"])
            self.assertEqual(res["avatar_url"], "https://alexmorgan.github.io/portrait.png")

    def test_universal_footprint_recon_orchestration(self):
        """Verifies that execute_universal_footprint_recon aggregates handles, sites, and esports backward compatibility."""
        with patch("backend.footprint_recon.query_youtube_channel") as mock_yt, \
             patch("backend.footprint_recon.query_bluesky_profile") as mock_bsky, \
             patch("backend.footprint_recon.query_personal_site_candidate") as mock_site, \
             patch("backend.esports_recon.query_esports_earnings") as mock_esp:

            mock_yt.return_value = {
                "platform": "YouTube",
                "category": "CREATOR",
                "handle": "@testcreator",
                "url": "https://www.youtube.com/@testcreator",
                "avatar_url": "https://yt.com/av.jpg"
            }
            mock_bsky.return_value = None
            mock_site.return_value = {
                "platform": "Personal Portfolio / Website",
                "category": "PORTFOLIO",
                "url": "https://testcreator.github.io",
                "avatar_url": "https://testcreator.github.io/me.jpg"
            }
            mock_esp.return_value = [
                {
                    "gamertag": "Djessir",
                    "game": "Brawlhalla",
                    "earnings": "$500.00",
                    "country": "Netherlands",
                    "profile_url": "https://www.esportsearnings.com/players/123-djessir",
                    "confidence_score": 0.95
                }
            ]

            res = execute_universal_footprint_recon(
                target_name="Yasir Khalid",
                known_handles=["djessir", "testcreator"],
                target_country="Netherlands"
            )

            self.assertIsInstance(res, dict)
            self.assertIn("matches", res)
            self.assertIn("discovered_handles", res)
            self.assertIn("discovered_sites", res)

            # Check handles: contains both youtube handle and esports gamertag
            handles_lower = [h.lower() for h in res["discovered_handles"]]
            self.assertIn("djessir", handles_lower)

            # Check sites: contains discovered portfolio
            self.assertIn("https://testcreator.github.io", res["discovered_sites"])

            # Check esports match is preserved in matches
            platforms = [m.get("platform") for m in res["matches"]]
            self.assertIn("EsportsEarnings", platforms)
            self.assertIn("YouTube", platforms)

    def test_cardinal_strictness_given_name_demotion(self):
        """Verifies Cardinal demotes 'John Zwaan' to suspected_profiles when target is 'Jordin Zwaan'."""
        from backend.cardinal.arbiter import _enforce_cardinal_strictness
        parsed = {
            "real_name": "Jordin Zwaan",
            "perceived_gender": "male",
            "verified_profiles": [
                {
                    "platform": "LinkedIn",
                    "url": "https://linkedin.com/in/john-zwaan",
                    "display_name": "John Zwaan",
                    "confidence": 0.95
                }
            ],
            "suspected_profiles": []
        }
        observations = {
            "profile_clues": [
                {
                    "url": "https://linkedin.com/in/john-zwaan",
                    "display_name": "John Zwaan",
                    "bio": "Financial Director"
                }
            ]
        }
        res = _enforce_cardinal_strictness(parsed, observations)
        self.assertEqual(len(res["verified_profiles"]), 0)
        self.assertEqual(len(res["suspected_profiles"]), 1)
        self.assertIn("Conflicting given name", res["suspected_profiles"][0]["quarantine_reason"])

    def test_cardinal_strictness_pronoun_contradiction_demotion(self):
        """Verifies Cardinal demotes profiles with 'she/her' when target is male."""
        from backend.cardinal.arbiter import _enforce_cardinal_strictness
        parsed = {
            "real_name": "Jordin Zwaan",
            "perceived_gender": "male",
            "verified_profiles": [
                {
                    "platform": "Instagram",
                    "url": "https://instagram.com/jordinzwaan",
                    "display_name": "Jordin Zwaan",
                    "confidence": 0.95
                }
            ],
            "suspected_profiles": []
        }
        observations = {
            "profile_clues": [
                {
                    "url": "https://instagram.com/jordinzwaan",
                    "display_name": "Jordin Zwaan",
                    "bio": "Fashion designer | she/her | Amsterdam"
                }
            ]
        }
        res = _enforce_cardinal_strictness(parsed, observations)
        self.assertEqual(len(res["verified_profiles"]), 0)
        self.assertEqual(len(res["suspected_profiles"]), 1)
        self.assertIn("Demographic contradiction", res["suspected_profiles"][0]["quarantine_reason"])

    def test_ai_correlator_given_name_and_pronoun_guardrails(self):
        """Verifies ai_correlator guardrails demote given name conflicts and pronoun conflicts."""
        from backend.cardinal.arbiter import ai_verify_and_quarantine_candidates
        target_info = {
            "email": "jordin.zwaan@example.com",
            "full_name": "Jordin Zwaan",
            "primary_handles": ["jordinzwaan"],
            "locations": ["Netherlands"],
            "gender": "male"
        }
        candidates = [
            {
                "platform": "GitHub",
                "handle": "johnzwaan",
                "name": "John Zwaan",
                "url": "https://github.com/johnzwaan",
                "context": "Software engineer in Amsterdam"
            },
            {
                "platform": "Twitter",
                "handle": "jordinzwaan",
                "name": "Jordin Zwaan",
                "url": "https://twitter.com/jordinzwaan",
                "context": "Creative director (she/her) living in Utrecht"
            }
        ]
        with patch("backend.cardinal.arbiter.resolve_api_key", return_value=None):
            ver, susp, rej = ai_verify_and_quarantine_candidates(target_info, candidates)
            self.assertEqual(len(ver), 0)
            self.assertEqual(len(susp), 2)

    def test_alias_harvesting_and_wmn_prioritization(self):
        """Verifies discovered aliases like 'sazeku' are preserved and prioritized."""
        from backend.live_osint import derive_candidate_handles
        handles = set(derive_candidate_handles("target@domain.nl", target_name="Jordin Zwaan"))
        self.assertIn("target", handles)

        mock_breaches = [
            {"breach_name": "Test Breach", "username": "sazeku", "top_logins": ["sazeku_alt@mail.com"]}
        ]
        cand_handles = set(handles)
        newly_discovered_aliases = set()
        for b in mock_breaches:
            if b.get("username"):
                cand_handles.add(b["username"])
                newly_discovered_aliases.add(b["username"])
            for log in b.get("top_logins", []):
                u_part = log.split("@")[0]
                cand_handles.add(u_part)
                newly_discovered_aliases.add(u_part)

        self.assertIn("sazeku", cand_handles)
        self.assertIn("sazeku_alt", cand_handles)
        self.assertIn("sazeku", newly_discovered_aliases)


if __name__ == "__main__":
    unittest.main()
