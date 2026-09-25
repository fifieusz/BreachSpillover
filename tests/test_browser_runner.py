import unittest
from unittest.mock import patch, MagicMock
from backend.browser_runner import (
    get_session_dir,
    get_browser_channel,
    is_browser_authenticated,
    scrape_linkedin_profile_headless
)

class TestBrowserRunner(unittest.TestCase):
    def test_session_dir_exists(self):
        s_dir = get_session_dir()
        self.assertTrue(s_dir.exists())
        self.assertTrue(str(s_dir).endswith("browser_session"))

    def test_browser_channel_detection(self):
        ch = get_browser_channel()
        self.assertIn(ch, ["msedge", "chromium"])

    def test_is_browser_authenticated_returns_dict(self):
        status = is_browser_authenticated()
        self.assertIsInstance(status, dict)
        self.assertIn("authenticated", status)

if __name__ == "__main__":
    unittest.main()
