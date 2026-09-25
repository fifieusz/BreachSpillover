import unittest
from backend.linkedin_recon import derive_linkedin_candidate_slugs, is_linkedin_identity_match

class TestLinkedInSafety(unittest.TestCase):

    def test_candidate_slugs_alje_woltjer(self):
        slugs = derive_linkedin_candidate_slugs("Alje Woltjer", "alje.woltjer@vooruit.nl")
        # Ensure high-entropy full name vanity is primary
        self.assertEqual(slugs[0], "alje-woltjer")
        self.assertIn("aljewoltjer", slugs)
        self.assertIn("alje", slugs)
        self.assertIn("awoltjer", slugs)

    def test_candidate_slugs_single_word_email(self):
        slugs = derive_linkedin_candidate_slugs("Alje", "alje@vooruit.nl")
        self.assertEqual(slugs[0], "alje")

    def test_identity_matching_prevents_false_positives(self):
        # Target is Jordin Zwaan, profile is a stranger with given name Jordin
        collision_scraped = {"full_name": "Jordin Sasha Danaram", "headline": "Student at Caltech"}
        self.assertFalse(is_linkedin_identity_match(collision_scraped, "Jordin Zwaan"))

        # Target is Jordin Zwaan, profile is authentic
        authentic_scraped = {"full_name": "Jordin Zwaan", "headline": "Student Media Vormgever"}
        self.assertTrue(is_linkedin_identity_match(authentic_scraped, "Jordin Zwaan"))

if __name__ == "__main__":
    unittest.main()
