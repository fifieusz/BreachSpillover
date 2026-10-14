"""
Tests for the Forensic Investigation Execution Trace & Provenance Engine.
Verifies that searches return transparent, structured execution steps,
terminal logs, and discovery provenance maps.
"""

import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.provenance_tracker import (
    InvestigationTrace,
    ProvenanceStep,
    reconstruct_identity_provenance,
    record_active_trace,
    get_cached_trace
)

class TestProvenanceEngine(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_investigation_trace_collection(self):
        """Verifies InvestigationTrace accumulates steps and logs properly."""
        trace = InvestigationTrace("analyst.test@example.com")
        trace.add_log("INFO", "RECON_INIT", "Starting OSINT reconnaissance")
        trace.add_step(
            step_id="step_1_test",
            phase_number=1,
            phase_name="Seed Decomposition",
            title="Target Decomposition",
            summary="Extracted handle and domain",
            details=["Input: analyst.test@example.com", "Handle: @analyst.test"],
            discovered_items=[{"type": "HANDLE", "value": "@analyst.test", "status": "VERIFIED"}]
        )
        data = trace.to_dict()
        self.assertEqual(data["target"], "analyst.test@example.com")
        self.assertEqual(len(data["steps"]), 1)
        self.assertEqual(data["total_steps"], 1)
        self.assertEqual(len(data["log_lines"]), 2)  # initial log + phase log
        self.assertEqual(len(data["discoveries_ledger"]), 1)

    def test_trace_caching(self):
        """Verifies active trace caching and retrieval."""
        trace = InvestigationTrace("cache.test@domain.com")
        trace.add_step(
            step_id="step_cache",
            phase_number=1,
            phase_name="Cache Test",
            title="Cache Verification",
            summary="Cached trace",
        )
        record_active_trace("cache.test@domain.com", trace)
        cached = get_cached_trace("cache.test@domain.com")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["target"], "cache.test@domain.com")
        self.assertEqual(len(cached["steps"]), 1)

    def test_provenance_reconstruction(self):
        """Verifies deterministic reconstruction of provenance for existing database identities."""
        mock_emp = {
            "full_name": "Marcus Vance",
            "corporate_email": "marcus.vance@cybercorp.io",
            "job_title": "Security Architect",
            "department": "Infrastructure",
            "avatar_seed": "https://images.unsplash.com/photo-test"
        }
        mock_leaks = [{"leak_name": "Canva", "breach_date": "2019-05-24", "leak_type": "Database Breach"}]
        mock_creds = [{"username_or_email": "marcus.vance", "plaintext_password": "Password123"}]
        mock_pivots = [
            {"pivot_type": "WORKPLACE", "pivot_value": "Employer: CyberCorp", "context_note": "Verified by AI Cardinal"},
            {"pivot_type": "PUBLIC_PROFILE", "pivot_value": "LinkedIn: @marcus-vance", "context_note": "Verified via Waterfall"}
        ]
        mock_images = [{"image_url": "https://images.unsplash.com/photo-test", "platform": "LinkedIn", "is_primary": True}]

        recon = reconstruct_identity_provenance(
            email="marcus.vance@cybercorp.io",
            employee=mock_emp,
            leaks=mock_leaks,
            credentials=mock_creds,
            pivots=mock_pivots,
            footprints=[],
            relatives=[],
            images=mock_images
        )

        self.assertEqual(recon["target"], "marcus.vance@cybercorp.io")
        self.assertGreaterEqual(recon["total_steps"], 5)
        step_ids = [s["step_id"] for s in recon["steps"]]
        self.assertIn("step_1_seed", step_ids)
        self.assertIn("step_2_breaches", step_ids)
        self.assertIn("step_4_synthesis", step_ids)
        self.assertIn("step_6_visual", step_ids)

    def test_api_search_includes_execution_trace(self):
        """Verifies /api/search response contains the full execution_trace payload."""
        resp = self.client.get("/api/search?email=alex.morgan@cybercorp.io")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("execution_trace", data)
        trace = data["execution_trace"]
        self.assertIsNotNone(trace)
        self.assertIn("steps", trace)
        self.assertIn("log_lines", trace)
        self.assertIn("discoveries_ledger", trace)
        self.assertGreater(len(trace["steps"]), 0)

if __name__ == "__main__":
    unittest.main()
