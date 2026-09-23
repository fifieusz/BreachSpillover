import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.ai_engine import (
    generate_heuristic_fallback_dossier,
    generate_ai_threat_dossier,
    ai_copilot_chat,
    test_ai_connection,
    build_target_forensic_context
)

client = TestClient(app)


class TestAIEngine(unittest.TestCase):

    def setUp(self):
        self.sample_scan_data = {
            "employee": {
                "id": 1,
                "full_name": "Jordin Zwaan",
                "corporate_email": "jordinzwaan2016@gmail.com",
                "job_title": "Threat Analyst",
                "department": "Merlon Security",
                "vip_level": "Standard"
            },
            "spillover_score": {
                "score": 65,
                "level": "HIGH",
                "color": "#f97316"
            },
            "leaks": [
                {
                    "id": 101,
                    "leak_name": "RedLine Stealer Dump 2022",
                    "leak_type": "INFOSTEALER",
                    "severity": "CRITICAL",
                    "breach_date": "2022-04-10",
                    "malware_family": "RedLine",
                    "exposed_data": ["Passwords", "Session Cookies"]
                }
            ],
            "credentials": [
                {
                    "id": 201,
                    "domain_compromised": "vpn.merlon.corp",
                    "plaintext_password": None,
                    "password_pattern": "StandardBase!2022",
                    "is_corporate_password_match": True
                }
            ],
            "pivots": [
                {
                    "id": 301,
                    "pivot_type": "PUBLIC_PROFILE",
                    "pivot_value": "GitHub: @sazeku123",
                    "context_note": "Authenticated developer commits",
                    "confidence_score": 0.95
                },
                {
                    "id": 302,
                    "pivot_type": "SUSPECTED_ACCOUNT",
                    "pivot_value": "Steam: @jordin99",
                    "context_note": "Unverified gaming alias",
                    "confidence_score": 0.55
                }
            ],
            "physical_footprints": [
                {
                    "id": 401,
                    "address_line": "Storgata 12",
                    "city": "Sarpsborg",
                    "country": "Norway",
                    "exposure_type": "Public Registry"
                }
            ],
            "relatives": []
        }

    def test_build_forensic_context(self):
        ctx = build_target_forensic_context(self.sample_scan_data)
        self.assertIn("Jordin Zwaan", ctx)
        self.assertIn("jordinzwaan2016@gmail.com", ctx)
        self.assertIn("RedLine", ctx)
        self.assertIn("Sarpsborg", ctx)

    def test_heuristic_fallback_dossier_structure(self):
        dossier = generate_heuristic_fallback_dossier(self.sample_scan_data)
        self.assertIn("executive_summary", dossier)
        self.assertIn("threat_level_verdict", dossier)
        self.assertIn("persona_disambiguation", dossier)
        self.assertIn("adversary_attack_simulation", dossier)
        self.assertIn("credential_mutation_analysis", dossier)
        self.assertIn("prioritized_remediations", dossier)

        # Check subfields in attack simulation
        sim = dossier["adversary_attack_simulation"]
        self.assertIn("spear_phishing_pretext", sim)
        self.assertIn("credential_stuffing_blast_radius", sim)
        self.assertIn("household_social_engineering_vector", sim)

        # Check subfields in credential_mutation_analysis
        mut = dossier["credential_mutation_analysis"]
        self.assertIn("base_pattern_detected", mut)
        self.assertIn("mutation_risk_score", mut)
        self.assertIn("mutation_risk_verdict", mut)
        self.assertIn("corporate_cross_reuse_assessment", mut)
        self.assertIn("defensive_hardening_guidance", mut)

        self.assertFalse(dossier.get("is_ai_generated"))
        self.assertEqual(dossier.get("provider"), "deterministic_heuristic")

    def test_dossier_caching(self):
        with patch("backend.ai_engine.resolve_api_key", return_value=""):
            dossier1 = generate_ai_threat_dossier(self.sample_scan_data, api_key="", force_refresh=True)
            dossier2 = generate_ai_threat_dossier(self.sample_scan_data, api_key="", force_refresh=False)
            self.assertEqual(dossier1.get("generated_at"), dossier2.get("generated_at"))
            self.assertIn("credential_mutation_analysis", dossier2)

    def test_offline_ai_dossier_wrapper(self):
        # Without key, should seamlessly produce heuristic dossier with notice
        with patch("backend.ai_engine.resolve_api_key", return_value=""):
            dossier = generate_ai_threat_dossier(self.sample_scan_data, api_key="")
            self.assertIn("executive_summary", dossier)
            self.assertIn("notice", dossier)
            self.assertFalse(dossier.get("is_ai_generated"))

    def test_offline_copilot_chat(self):
        with patch("backend.ai_engine.resolve_api_key", return_value=""):
            # Test password question
            res_pwd = ai_copilot_chat("Tell me about passwords", self.sample_scan_data, api_key="")
            self.assertTrue(res_pwd["success"])
            self.assertIn("password", res_pwd["reply"].lower())

            # Test 1881 question
            res_1881 = ai_copilot_chat("How to remove from 1881.no?", self.sample_scan_data, api_key="")
            self.assertTrue(res_1881["success"])
            self.assertIn("1881", res_1881["reply"])

    def test_api_dossier_endpoint(self):
        resp = client.post("/api/ai/dossier", json={
            "email": "jordinzwaan2016@gmail.com",
            "api_key": "",
            "provider": "groq",
            "scan_data": self.sample_scan_data
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("executive_summary", data)
        self.assertIn("persona_disambiguation", data)

    def test_api_copilot_endpoint(self):
        resp = client.post("/api/ai/copilot", json={
            "email": "jordinzwaan2016@gmail.com",
            "message": "What is the highest risk vector?",
            "api_key": "",
            "provider": "groq",
            "scan_data": self.sample_scan_data
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("reply", data)

    def test_api_test_key_endpoint_validation(self):
        with patch("backend.ai_engine.resolve_api_key", return_value=""):
            # When no key is provided and no key is in env, should raise 400
            resp = client.post("/api/ai/test-key", json={"api_key": "", "provider": "groq"})
            self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
