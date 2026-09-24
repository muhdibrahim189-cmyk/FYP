import unittest

from utils.auth import authenticate, role_has_permission


class AuthTests(unittest.TestCase):
    def test_valid_credentials_case_insensitive_username(self):
        self.assertEqual(authenticate("Admin", "admin123")["role"], "admin")

    def test_wrong_password_or_user(self):
        self.assertIsNone(authenticate("admin", "wrong"))
        self.assertIsNone(authenticate("nobody", "admin123"))

    def test_permission_matrix(self):
        self.assertTrue(role_has_permission("manager", "approve"))
        self.assertFalse(role_has_permission("data_entry", "approve"))
        self.assertFalse(role_has_permission(None, "view"))


if __name__ == "__main__":
    unittest.main()
