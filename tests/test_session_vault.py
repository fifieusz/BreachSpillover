import unittest
from unittest.mock import patch, MagicMock
from backend.session_vault import get_vault_summary, verify_linkedin_cookie, get_cached_linkedin_status

class TestSessionVault(unittest.TestCase):

    def test_vault_summary_unconfigured(self):
        with patch("backend.session_vault.get_linkedin_cookie_from_sources", return_value=None), \
             patch("backend.session_vault.get_linkedin_jsessionid_from_sources", return_value=None), \
             patch.dict("os.environ", {"LINKEDIN_LI_AT": "", "LINKEDIN_JSESSIONID": ""}, clear=True):
            summary = get_vault_summary()
            self.assertEqual(summary["overall_status"], "problem")
            self.assertFalse(summary["is_good"])
            self.assertTrue(summary["has_problem"])
            self.assertFalse(summary["linkedin"]["configured"])
            self.assertFalse(summary["linkedin"]["valid"])

    def test_verify_linkedin_empty(self):
        with patch("backend.session_vault.get_linkedin_cookie_from_sources", return_value=None):
            res = verify_linkedin_cookie(None)
            self.assertFalse(res["valid"])
            self.assertFalse(res["configured"])

    @patch("curl_cffi.requests.get")
    def test_verify_linkedin_valid(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "plainId": "test_investigator",
            "miniProfile": {
                "firstName": "Alje",
                "lastName": "Woltjer",
                "occupation": "Security Specialist at Merlon Security"
            }
        }
        mock_get.return_value = mock_resp

        res = verify_linkedin_cookie("AQEDATestCookieValue1234567890")
        self.assertTrue(res["valid"])
        self.assertTrue(res["configured"])
        self.assertEqual(res["account_name"], "Alje Woltjer")
        self.assertEqual(res["headline"], "Security Specialist at Merlon Security")

        # Vault summary should reflect the valid cached status when cookie is present in sources
        with patch("backend.session_vault.get_linkedin_cookie_from_sources", return_value="AQEDATestCookieValue1234567890"):
            summary = get_vault_summary()
            self.assertEqual(summary["overall_status"], "good")
            self.assertTrue(summary["is_good"])
            self.assertFalse(summary["has_problem"])
            self.assertTrue(summary["linkedin"]["valid"])
            self.assertEqual(summary["linkedin"]["account_name"], "Alje Woltjer")

if __name__ == "__main__":
    unittest.main()
