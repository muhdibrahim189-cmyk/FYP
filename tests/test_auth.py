import unittest

import pandas as pd

from utils.auth import USERS, authenticate, role_has_permission, visible_rows


class AuthTests(unittest.TestCase):
    def test_valid_credentials_case_insensitive_username(self):
        self.assertEqual(authenticate("Admin", "admin123")["role"], "admin")
        self.assertEqual(authenticate("user", "user123")["role"], "government")
        self.assertEqual(authenticate("BP", "bp123")["company"], "BP")

    def test_wrong_password_or_user(self):
        self.assertIsNone(authenticate("admin", "wrong"))
        self.assertIsNone(authenticate("nobody", "admin123"))
        self.assertIsNone(authenticate("bp", "chevron123"))

    def test_permission_matrix(self):
        self.assertTrue(role_has_permission("company", "approve"))
        self.assertFalse(role_has_permission("company", "report"))
        self.assertTrue(role_has_permission("government", "report"))
        self.assertFalse(role_has_permission("government", "audit_log"))
        self.assertFalse(role_has_permission("government", "approve"))
        self.assertTrue(role_has_permission("admin", "audit_log"))
        self.assertFalse(role_has_permission(None, "all_companies"))

    def test_company_users_see_only_their_company(self):
        df = pd.DataFrame({"facility": ["BP", "Chevron", "BP"], "company": ["BP", "Chevron", "BP"]})
        self.assertEqual(list(visible_rows(df, USERS["bp"])["facility"]), ["BP", "BP"])
        self.assertEqual(list(visible_rows(df, USERS["chevron"], "company")["company"]), ["Chevron"])
        self.assertEqual(len(visible_rows(df, USERS["admin"])), 3)
        self.assertEqual(len(visible_rows(df, USERS["user"])), 3)
        self.assertTrue(visible_rows(df, None).empty)  # fail closed when signed out
        self.assertTrue(visible_rows(pd.DataFrame(), USERS["bp"]).empty)


if __name__ == "__main__":
    unittest.main()
