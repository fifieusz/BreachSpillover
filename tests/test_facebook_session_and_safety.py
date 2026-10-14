import unittest
from unittest.mock import patch, MagicMock
from backend.session_vault import (
    parse_facebook_cookie_input,
    verify_facebook_cookie,
    get_vault_summary
)
from backend.facebook_recon import (
    get_facebook_session_cookies,
    derive_candidate_facebook_urls
)

class TestFacebookSessionAndSafety(unittest.TestCase):

    def test_parse_facebook_cookie_input_clean(self):
        # 1. Plain numeric ID and token
        u, x = parse_facebook_cookie_input("100009990541720", "2%3Aabcde1234567890")
        self.assertEqual(u, "100009990541720")
        self.assertEqual(x, "2%3Aabcde1234567890")

        # 2. Raw Cookie Header string pasted into first field
        cookie_header = "sb=AbCd; c_user=100009990541720; xs=17%3Axyz9876543210; datr=Def123"
        u, x = parse_facebook_cookie_input(cookie_header, "")
        self.assertEqual(u, "100009990541720")
        self.assertEqual(x, "17%3Axyz9876543210")

        # 3. Quoted inputs
        u, x = parse_facebook_cookie_input('"100009990541720"', "'2%3Atoken1234567890'")
        self.assertEqual(u, "100009990541720")
        self.assertEqual(x, "2%3Atoken1234567890")

    @patch("curl_cffi.requests.get")
    def test_verify_facebook_cookie_valid_session(self, mock_get):
        # Mock active session 302 redirecting to user profile
        mock_resp = MagicMock()
        mock_resp.status_code = 302
        mock_resp.headers = {"location": "https://www.facebook.com/filip.113"}
        mock_get.return_value = mock_resp

        res = verify_facebook_cookie("100009990541720", "17%3Avalid_session_token_123")
        self.assertTrue(res["valid"])
        self.assertEqual(res["status"], "good")
        self.assertEqual(res["account_name"], "filip.113")
        self.assertIn("Active & Verified", res["message"])

    @patch("curl_cffi.requests.get")
    def test_verify_facebook_cookie_expired_session(self, mock_get):
        # Mock expired session 302 redirecting to login page
        mock_resp = MagicMock()
        mock_resp.status_code = 302
        mock_resp.headers = {"location": "https://www.facebook.com/login.php"}
        mock_get.return_value = mock_resp

        res = verify_facebook_cookie("100009990541720", "17%3Aexpired_token_123")
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "expired")
        self.assertIn("login/checkpoint", res["message"])

    def test_derive_candidate_facebook_urls(self):
        urls = derive_candidate_facebook_urls("Jordin Zwaan", "jordinzwaan2016@gmail.com")
        url_strs = [item["url"] for item in urls]
        self.assertIn("https://www.facebook.com/jordinzwaan2016", url_strs)
        self.assertIn("https://www.facebook.com/jordinzwaan", url_strs)
        self.assertIn("https://www.facebook.com/jordin.zwaan", url_strs)

    def test_vault_summary_facebook_integration(self):
        with patch("backend.session_vault.reload_env"), \
             patch("backend.session_vault.os.getenv", side_effect=lambda k, d="": {"FACEBOOK_C_USER": "100009990541720", "FACEBOOK_XS": "17%3Avalid_token_1234567890"}.get(k, d)):
            summary = get_vault_summary(check_live=False)
            fb = summary.get("facebook", {})
            self.assertTrue(fb.get("configured"))
            self.assertEqual(fb.get("c_user"), "100009990541720")

if __name__ == "__main__":
    unittest.main()
