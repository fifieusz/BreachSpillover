import unittest
import os
import sys

# Ensure root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.telecom_recon import (
    parse_and_detect_phone,
    get_country_directories,
    query_live_international_telecom
)

client = TestClient(app)


class TestTelecomRecon(unittest.TestCase):

    def test_phone_parsing_norway(self):
        p = parse_and_detect_phone("+47 982 12 345")
        self.assertTrue(p["is_valid"])
        self.assertEqual(p["iso"], "NO")
        self.assertEqual(p["country_name"], "Norway")
        self.assertIn("Mobile", p["line_type"])

    def test_phone_parsing_poland(self):
        p = parse_and_detect_phone("+48 501 234 567")
        self.assertTrue(p["is_valid"])
        self.assertEqual(p["iso"], "PL")
        self.assertEqual(p["country_name"], "Poland")

    def test_phone_parsing_sweden(self):
        p = parse_and_detect_phone("+46 70 123 45 67")
        self.assertTrue(p["is_valid"])
        self.assertEqual(p["iso"], "SE")
        self.assertEqual(p["country_name"], "Sweden")

    def test_phone_parsing_usa(self):
        p = parse_and_detect_phone("+1 (555) 234-5678")
        self.assertTrue(p["is_valid"])
        self.assertEqual(p["iso"], "US")
        self.assertIn("United States", p["country_name"])

    def test_phone_parsing_uk(self):
        p = parse_and_detect_phone("+44 7911 123456")
        self.assertTrue(p["is_valid"])
        self.assertEqual(p["iso"], "GB")
        self.assertEqual(p["country_name"], "United Kingdom")

    def test_phone_parsing_germany(self):
        p = parse_and_detect_phone("+49 151 12345678")
        self.assertTrue(p["is_valid"])
        self.assertEqual(p["iso"], "DE")
        self.assertEqual(p["country_name"], "Germany")

    def test_country_directories_routing(self):
        dirs_pl = get_country_directories("+48 501 234 567", country_iso="PL")
        self.assertTrue(len(dirs_pl) >= 5)
        names = [d["name"] for d in dirs_pl]
        self.assertIn("Infonumer.pl", names)

        dirs_se = get_country_directories("Jordin Zwaan", country_iso="SE")
        self.assertTrue(len(dirs_se) >= 5)
        names_se = [d["name"] for d in dirs_se]
        self.assertIn("Hitta.se", names_se)

    def test_telecom_api_endpoints(self):
        resp_get = client.get("/api/recon/telecom?query=%2B4798212345&country=NO")
        self.assertEqual(resp_get.status_code, 200)
        data = resp_get.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["detected_iso"], "NO")
        self.assertTrue(len(data["directories"]) > 0)

        resp_post = client.post("/api/recon/telecom", json={"query": "+48 501 234 567"})
        self.assertEqual(resp_post.status_code, 200)
        data_post = resp_post.json()
        self.assertEqual(data_post["detected_iso"], "PL")


if __name__ == "__main__":
    unittest.main()
