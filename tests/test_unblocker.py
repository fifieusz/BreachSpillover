import unittest
from unittest.mock import patch, MagicMock
from backend.unblocker_client import (
    resolve_unblocker_config,
    fetch_html_with_unblocker_fallback,
    parse_linkedin_html
)

class TestUnblockerClient(unittest.TestCase):
    @patch("dotenv.dotenv_values", return_value={})
    def test_unblocker_config_resolution(self, mock_env):
        with patch.dict("os.environ", {"SCRAPER_API_KEY": "test_key_123"}, clear=True):
            cfg = resolve_unblocker_config()
            self.assertEqual(cfg["provider"], "scraperapi")
            self.assertEqual(cfg["api_key"], "test_key_123")


    @patch("backend.unblocker_client.resolve_unblocker_config", return_value={"provider": None, "api_key": None})
    def test_direct_request_blocked_fallback_notice(self, mock_cfg):
        with patch("curl_cffi.requests.get") as mock_direct:
            mock_resp = MagicMock()
            mock_resp.status_code = 999
            mock_resp.text = "Request Denied"
            mock_direct.return_value = mock_resp
            res = fetch_html_with_unblocker_fallback("https://www.linkedin.com/in/testuser/")
            self.assertFalse(res["success"])
            self.assertTrue(res.get("blocked", False))
            self.assertIn("SCRAPER_API_KEY", res["message"])

    def test_parse_linkedin_html_extracts_employer_and_role(self):
        html_sample = """
        <html>
        <head><title>Alje Woltjer - Senior Security Engineer at Merlon Security | LinkedIn</title></head>
        <body>
            <h1>Alje Woltjer</h1>
            <div class="text-body-medium">Senior Security Engineer at Merlon Security</div>
            <ul>
                <li class="pvs-list__item">
                    <span>Senior Security Engineer</span>
                    <span>Merlon Security</span>
                    <span>2024 - Present</span>
                </li>
            </ul>
        </body>
        </html>
        """
        parsed = parse_linkedin_html(html_sample, "https://www.linkedin.com/in/alje/")
        self.assertEqual(parsed["full_name"], "Alje Woltjer")
        self.assertEqual(parsed["current_company"], "Merlon Security")
        self.assertTrue(len(parsed["experiences"]) >= 1)

if __name__ == "__main__":
    unittest.main()
