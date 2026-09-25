import unittest
from unittest.mock import patch, MagicMock
from backend.linkedin_recon import derive_linkedin_candidate_slugs, get_linkedin_cookie
from backend.browser_bridge import find_system_browser, BROWSER_PROFILE_DIR

class TestLinkedInBrowserBridge(unittest.TestCase):

    def test_derive_candidate_slugs(self):
        slugs = derive_linkedin_candidate_slugs("Alje Woltjer", "alje.woltjer@vooruit.nl")
        self.assertIn("alje", slugs)
        self.assertIn("aljewoltjer", slugs)
        self.assertEqual(slugs[0], "alje-woltjer")  # Full name vanity prioritized for generalizability
        self.assertIn("aljewoltjer", slugs)

    def test_system_browser_detection(self):
        browser = find_system_browser()
        self.assertIsNotNone(browser)
        self.assertTrue(any(b in browser.lower() for b in ["opera", "msedge", "chrome", "brave"]))

    def test_bridge_profile_dir_configured(self):
        self.assertTrue(any(str(BROWSER_PROFILE_DIR).endswith(s) for s in ["browser_profile", "browser_session"]))

    @patch("backend.session_vault.get_linkedin_cookie_from_sources", return_value=None)
    @patch("backend.browser_bridge.get_active_bridge_cookie", return_value="test_cookie_12345")
    def test_get_linkedin_cookie_uses_bridge_fallback(self, mock_bridge, mock_sources):
        with patch.dict("os.environ", {"LINKEDIN_LI_AT": ""}, clear=True):
            cookie = get_linkedin_cookie()
            self.assertEqual(cookie, "test_cookie_12345")

    def test_google_login_and_degraded_notice(self):
        from backend.browser_bridge import login_google_account, inspect_bridge_status, logout_account
        logout_account()

        # Login with a Google account
        res = login_google_account("agent@defense.org", "Defense Agent")
        self.assertTrue(res["success"])
        self.assertTrue(res["authenticated"])
        self.assertEqual(res["user_email"], "agent@defense.org")
        # No scraper authenticator attached, so degraded notice must be present
        self.assertFalse(res["has_scraper_authenticator"])
        self.assertIsNotNone(res["notice"])
        self.assertIn("does not have a registered LinkedIn reconnaissance account", res["notice"])

        # Check status endpoint
        st = inspect_bridge_status()
        self.assertTrue(st["authenticated"])
        self.assertEqual(st["user_email"], "agent@defense.org")
        self.assertFalse(st["has_scraper_authenticator"])
        self.assertIn("does not have a registered LinkedIn reconnaissance account", st["notice"])

        # Logout
        out = logout_account()
        self.assertTrue(out["success"])
        st_after = inspect_bridge_status()
        self.assertFalse(st_after["authenticated"])

if __name__ == "__main__":
    unittest.main()

