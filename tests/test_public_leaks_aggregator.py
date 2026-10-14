import unittest
from backend.public_leaks_aggregator import (
    get_active_engines_summary,
    query_leakcheck_public,
    query_breachdirectory_public,
    harvest_public_pastes_and_combolists
)

class TestPublicLeaksAggregator(unittest.TestCase):

    def test_engine_catalog_and_status(self):
        summary = get_active_engines_summary()
        self.assertIsInstance(summary, list)
        self.assertGreaterEqual(len(summary), 6)
        
        engine_ids = [e["id"] for e in summary]
        self.assertIn("xposedornot", engine_ids)
        self.assertIn("hudson_rock", engine_ids)
        self.assertIn("hibp_passwords", engine_ids)
        self.assertIn("paste_harvester", engine_ids)
        self.assertIn("leakcheck", engine_ids)
        self.assertIn("breachdirectory", engine_ids)

    def test_leakcheck_endpoint_structure(self):
        res = query_leakcheck_public("nonexistent_test_probe_user_999@gmail.com")
        self.assertIsInstance(res, list)

    def test_paste_harvester_structure(self):
        res = harvest_public_pastes_and_combolists("nonexistent_test_probe_user_999@gmail.com")
        self.assertIsInstance(res, list)

if __name__ == "__main__":
    unittest.main()
