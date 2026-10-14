import unittest
from backend.password_auditor import (
    calculate_entropy,
    classify_password_pattern,
    audit_password_phrase,
    get_target_connected_strings
)

class TestPasswordAuditor(unittest.TestCase):
    def test_calculate_entropy(self):
        # Empty
        res_empty = calculate_entropy("")
        self.assertEqual(res_empty["shannon_entropy"], 0.0)
        self.assertEqual(res_empty["keyspace_entropy_bits"], 0.0)

        # Simple password
        res_simple = calculate_entropy("password")
        self.assertGreater(res_simple["keyspace_entropy_bits"], 20.0)

        # High entropy complex password
        res_complex = calculate_entropy("Tr0ub4dor&3!2026")
        self.assertGreater(res_complex["keyspace_entropy_bits"], 60.0)
        self.assertTrue(res_complex["character_classes"]["has_symbols"])
        self.assertTrue(res_complex["character_classes"]["has_digits"])
        self.assertTrue(res_complex["character_classes"]["has_uppercase"])
        self.assertTrue(res_complex["character_classes"]["has_lowercase"])

    def test_classify_password_pattern(self):
        self.assertEqual(classify_password_pattern("123456"), "Numeric PIN (6 digits)")
        self.assertEqual(classify_password_pattern("summer2019"), "Word + Year Pattern (e.g. 2019/2020 Persona)")
        self.assertEqual(classify_password_pattern("Summer2024!"), "Corporate Enterprise Standard (TitleCase + Year + Symbol)")
        self.assertEqual(classify_password_pattern("filipos123"), "Word + Numeric Suffix")

    def test_audit_password_phrase(self):
        ctx = {"email": "filipos123.91@gmail.com", "full_name": "Filipos"}
        # Candidate tied to identity
        res = audit_password_phrase("filipos123", target_context=ctx, check_hibp=False)
        self.assertTrue(res["is_identity_bound"])
        self.assertGreaterEqual(res["spillover_risk_score"], 40)

        # High-entropy phrase not tied to identity
        res_clean = audit_password_phrase("Xk8#mZ9$vL2!pQ5@", target_context=ctx, check_hibp=False)
        self.assertFalse(res_clean["is_identity_bound"])

    def test_get_target_connected_strings(self):
        ctx = {"email": "filipos123.91@gmail.com", "full_name": "Filipos"}
        strings = get_target_connected_strings(ctx, limit=10)
        self.assertGreater(len(strings), 0)
        passwords = [s["password"] for s in strings]
        # Should include base stem or handle permutations
        self.assertTrue(any("filipos" in p.lower() for p in passwords))

if __name__ == "__main__":
    unittest.main()
