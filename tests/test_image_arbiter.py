import unittest
from backend.image_recon import extract_image_perceptual_features, ai_select_most_plausible_target_image, reconcile_and_store_target_images
from backend.database import get_connection

class TestImageArbiter(unittest.TestCase):
    def test_perceptual_features_invalid_url(self):
        feat = extract_image_perceptual_features("")
        self.assertFalse(feat.get("is_accessible"))

    def test_ai_selection_generic(self):
        candidates = [
            {
                "platform": "Gravatar",
                "source": "Gravatar Universal Avatar",
                "image_url": "https://www.gravatar.com/avatar/4f456d6e9355fa86d7743688437d560a?s=256&d=404",
                "context": "Gravatar account tied to email"
            },
            {
                "platform": "GitHub",
                "source": "GitHub Profile Avatar",
                "image_url": "https://github.com/jordinzwaan.png?size=256",
                "context": "GitHub developer avatar"
            },
            {
                "platform": "LinkedIn",
                "source": "LinkedIn Professional Network",
                "image_url": "https://media.licdn.com/dms/image/v2/D4E03AQHPR7YAjKs1JA/profile-displayphoto-scale_100_100/B4EZ8evsKuIkAc-/0/1782927248326?e=1792022400&v=beta&t=IKZ7kO0NPYg8UlbBsazy8z9n1WuNL0QHMPW96y0-A8M",
                "context": "Public professional profile photograph"
            }
        ]

        winner = ai_select_most_plausible_target_image(
            candidate_images=candidates,
            target_name="Jordin Zwaan",
            target_email="jordinzwaan2016@gmail.com"
        )
        self.assertIsNotNone(winner)
        self.assertTrue(winner.get("is_real_face"))
        self.assertEqual(winner.get("classification"), "REAL_HUMAN_PORTRAIT")
        self.assertIn("licdn.com", winner.get("image_url"))
        self.assertGreaterEqual(winner.get("plausibility_score", 0), 0.80)

if __name__ == "__main__":
    unittest.main()
