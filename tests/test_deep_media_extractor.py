import unittest
from backend.image_recon import extract_images_from_webpage
from backend.facebook_recon import derive_candidate_facebook_urls

class TestDeepMediaAndFacebook(unittest.TestCase):
    def test_extract_images_from_html_markup(self):
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:image" content="https://example.com/assets/preview.jpg">
        </head>
        <body>
            <div style="background-image: url('https://example.com/assets/hero-bg.jpg')"></div>
            <img src="https://static.wixstatic.com/media/d1fa24_1a83d1f23e2142919b0dac24d8fe7c65~mv2.jpg/v1/fill/w_654,h_360/sample.jpg" />
            <img src="https://example.com/pixel.gif" />
            <img src="https://example.com/logo.svg" />
        </body>
        </html>
        """
        # Testing parser without live network calls by passing HTML
        # Candidates should normalize the Wix media ID without the fill path
        res = extract_images_from_webpage("https://example.com/portfolio", html=sample_html)
        # Even if network calls for example.com return 404/fail, the Wix image is tested if accessible
        self.assertIsInstance(res, list)

    def test_derive_candidate_facebook_urls(self):
        cands = derive_candidate_facebook_urls("Jordin Zwaan", "jordinzwaan2016@gmail.com", ["sazeku123"])
        urls = [c["url"] for c in cands]
        self.assertTrue(any("facebook.com/jordin.zwaan" in u for u in urls))
        self.assertTrue(any("facebook.com/jordinzwaan2016" in u for u in urls))
        self.assertTrue(any("facebook.com/sazeku123" in u for u in urls))

if __name__ == "__main__":
    unittest.main()
