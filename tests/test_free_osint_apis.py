import unittest
from unittest.mock import patch, MagicMock

from backend.geo_recon import (
    geocode_location_nominatim,
    resolve_universal_location,
    FALLBACK_CITIES
)
from backend.live_osint import check_disposable_email, query_domain_infrastructure
from backend.platform_probes import (
    query_keybase_user,
    query_hackernews_user,
    query_wayback_snapshots
)


class TestFreeOsintApis(unittest.TestCase):

    def test_nominatim_geocoding_structure(self):
        """Verifies OpenStreetMap Nominatim universal geocoding parsing."""
        mock_response_json = """[
            {
                "lat": "52.2297",
                "lon": "21.0122",
                "display_name": "Warsaw, Masovian Voivodeship, Poland",
                "address": {
                    "city": "Warsaw",
                    "state": "Masovian Voivodeship",
                    "country": "Poland",
                    "country_code": "pl",
                    "postcode": "00-001"
                }
            }
        ]"""
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = mock_response_json.encode("utf-8")
            mock_url.return_value.__enter__.return_value = mock_resp

            res = geocode_location_nominatim("Warsaw, Poland")
            self.assertIsNotNone(res)
            self.assertEqual(res["city"], "Warsaw")
            self.assertEqual(res["country"], "Poland")
            self.assertEqual(res["country_code"], "PL")
            self.assertAlmostEqual(res["latitude"], 52.2297, places=3)
            self.assertAlmostEqual(res["longitude"], 21.0122, places=3)

    def test_resolve_universal_location_fallback_and_global(self):
        """Verifies resolve_universal_location works for both offline dictionary and arbitrary locations."""
        # 1. Offline high-frequency city
        res_sarpsborg = resolve_universal_location("Sarpsborg, Norway")
        self.assertEqual(res_sarpsborg["city"], "Sarpsborg")
        self.assertEqual(res_sarpsborg["country"], "Norway")
        self.assertIsNotNone(res_sarpsborg["latitude"])

        # 2. Arbitrary location via mocked Nominatim
        with patch("backend.geo_recon.geocode_location_nominatim") as mock_geo:
            mock_geo.return_value = {
                "city": "Katowice",
                "country": "Poland",
                "country_code": "PL",
                "postal_code": "40-001",
                "latitude": 50.2649,
                "longitude": 19.0238,
                "exposure_type": "PUBLIC_PROFILE_GEO"
            }
            res_kat = resolve_universal_location("Katowice, Poland")
            self.assertEqual(res_kat["city"], "Katowice")
            self.assertEqual(res_kat["country"], "Poland")
            self.assertAlmostEqual(res_kat["latitude"], 50.2649, places=3)

    def test_kickbox_disposable_email_detection(self):
        """Verifies Kickbox Open API live disposable email check."""
        # 1. Static fast-path match
        res_mailinator = check_disposable_email("mailinator.com")
        self.assertTrue(res_mailinator["is_disposable"])
        self.assertEqual(res_mailinator["risk_rating"], "HIGH_EVASION_RISK")

        # 2. Persistent domain non-match
        res_corp = check_disposable_email("cybercorp.io")
        self.assertFalse(res_corp["is_disposable"])

        # 3. Live unlisted domain detected via Kickbox API mock
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = b'{"disposable": true}'
            mock_url.return_value.__enter__.return_value = mock_resp

            res_live = check_disposable_email("random-burner-domain-9988.xyz")
            self.assertTrue(res_live["is_disposable"])
            self.assertIn("Kickbox", res_live["provider"])

    def test_keybase_cryptographic_proof_extraction(self):
        """Verifies Keybase user lookup parses linked social identities (Twitter, GitHub, Reddit)."""
        mock_keybase_json = """{
            "status": {"code": 0, "name": "OK"},
            "them": [
                {
                    "basics": {"username": "testuser"},
                    "profile": {"full_name": "Test User", "location": "Oslo, Norway", "bio": "Security analyst"},
                    "proofs_summary": {
                        "all": [
                            {"proof_type": "github", "nametag": "testuser_gh", "service_url": "https://github.com/testuser_gh"},
                            {"proof_type": "twitter", "nametag": "testuser_tw", "service_url": "https://twitter.com/testuser_tw"},
                            {"proof_type": "hackernews", "nametag": "testuser_hn", "service_url": "https://news.ycombinator.com/user?id=testuser_hn"}
                        ]
                    }
                }
            ]
        }"""
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = mock_keybase_json.encode("utf-8")
            mock_url.return_value.__enter__.return_value = mock_resp

            hit = query_keybase_user("testuser")
            self.assertIsNotNone(hit)
            self.assertEqual(hit["platform"], "Keybase")
            self.assertEqual(hit["real_name"], "Test User")
            self.assertEqual(hit["location"], "Oslo, Norway")
            self.assertEqual(len(hit["linked_identities"]), 3)
            platforms = [li["platform"] for li in hit["linked_identities"]]
            self.assertIn("github", platforms)
            self.assertIn("twitter", platforms)
            self.assertIn("hackernews", platforms)

    def test_hackernews_profile_lookup(self):
        """Verifies Hacker News Firebase API profile parser."""
        mock_hn_json = """{
            "id": "alexmorgan",
            "created": 1500000000,
            "karma": 342,
            "about": "Security researcher and backend engineer",
            "submitted": [101, 102, 103, 104]
        }"""
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = mock_hn_json.encode("utf-8")
            mock_url.return_value.__enter__.return_value = mock_resp

            hit = query_hackernews_user("alexmorgan")
            self.assertIsNotNone(hit)
            self.assertEqual(hit["platform"], "HackerNews")
            self.assertEqual(hit["handle"], "alexmorgan")
            self.assertEqual(hit["karma"], 342)
            self.assertIn("Security researcher", hit["bio"])
            self.assertEqual(hit["submitted_count"], 4)
            self.assertTrue(hit["is_verified"])

    def test_wayback_availability_snapshot(self):
        """Verifies Wayback Machine archive availability parser."""
        mock_wb_json = """{
            "archived_snapshots": {
                "closest": {
                    "status": "200",
                    "available": true,
                    "url": "http://web.archive.org/web/20230501120000/https://example.com/profile",
                    "timestamp": "20230501120000"
                }
            }
        }"""
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = mock_wb_json.encode("utf-8")
            mock_url.return_value.__enter__.return_value = mock_resp

            hit = query_wayback_snapshots("https://example.com/profile")
            self.assertIsNotNone(hit)
            self.assertEqual(hit["platform"], "Wayback Machine")
            self.assertTrue(hit["is_verified"])
            self.assertEqual(hit["timestamp"], "2023-05-01")
            self.assertIn("web.archive.org", hit["archive_url"])

    def test_domain_infrastructure_doh_and_ip_api(self):
        """Verifies DoH and IP-API integration in query_domain_infrastructure."""
        with patch("urllib.request.urlopen") as mock_url:
            # We will mock the DNS responses and IP-API response
            def side_effect(req, timeout=None):
                url = req.full_url if hasattr(req, "full_url") else str(req)
                resp = MagicMock()
                resp.status = 200
                if "type=MX" in url:
                    resp.read.return_value = b'{"Answer": [{"data": "10 mail.example.com."}]}'
                elif "type=TXT" in url and "_dmarc" in url:
                    resp.read.return_value = b'{"Answer": [{"data": "\\"v=DMARC1; p=reject;\\""}]}'
                elif "type=TXT" in url:
                    resp.read.return_value = b'{"Answer": [{"data": "\\"v=spf1 -all\\""}]}'
                elif "type=A" in url:
                    resp.read.return_value = b'{"Answer": [{"data": "93.184.216.34"}]}'
                elif "ip-api.com" in url:
                    resp.read.return_value = b'{"status": "success", "country": "United States", "city": "Norwell", "isp": "EDGECAST", "as": "AS15133 MCI Communications Services, Inc. d/b/a Verizon Business"}'
                else:
                    resp.read.return_value = b'{}'
                mock_context = MagicMock()
                mock_context.__enter__.return_value = resp
                return mock_context

            mock_url.side_effect = side_effect

            infra = query_domain_infrastructure("admin@example.com")
            self.assertIsNotNone(infra)
            self.assertEqual(infra["domain"], "example.com")
            self.assertEqual(infra["spf_status"], "CONFIGURED")
            self.assertEqual(infra["dmarc_policy"], "REJECT (Enforced)")
            self.assertFalse(infra["spoofable"])
            self.assertIsNotNone(infra.get("hosting_intel"))
            self.assertEqual(infra["hosting_intel"]["isp"], "EDGECAST")
            self.assertEqual(infra["hosting_intel"]["country"], "United States")


if __name__ == "__main__":
    unittest.main()
