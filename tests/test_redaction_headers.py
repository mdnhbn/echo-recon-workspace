"""Common HTTP credentials must not survive report redaction."""
import unittest

from echo_recon.security import redact


class HeaderRedactionTests(unittest.TestCase):
    def test_authorization_schemes_and_case_preserve_other_lines(self):
        text = ("HTTP/1.1 200 OK\r\n"
                "aUtHoRiZaTiOn: Bearer fake-bearer-credential\r\n"
                "Proxy-Authorization: Basic fake-basic-credential\r\n"
                "X-Trace: keep-this-value\r\n"
                "Content-Type: text/plain\r\n")
        result = redact(text)
        self.assertNotIn("fake-bearer-credential", result)
        self.assertNotIn("fake-basic-credential", result)
        self.assertIn("aUtHoRiZaTiOn: [REDACTED]\r\n", result)
        self.assertIn("Proxy-Authorization: [REDACTED]\r\n", result)
        self.assertIn("X-Trace: keep-this-value\r\n", result)
        self.assertIn("Content-Type: text/plain\r\n", result)

    def test_all_cookie_parts_and_set_cookie_attributes_are_removed(self):
        text = ("Cookie: session=fake-one; preference=fake-two\n"
                "Set-Cookie: auth=fake-three; Path=/private; Secure; HttpOnly\n"
                "set-cookie: other=fake-four; Domain=example.com\n"
                "Server: example-server\n")
        result = redact(text)
        for value in ("fake-one", "fake-two", "fake-three", "fake-four",
                      "preference=", "Path=/private", "Domain=example.com"):
            self.assertNotIn(value, result)
        self.assertEqual(result.count("[REDACTED]"), 3)
        self.assertIn("Server: example-server\n", result)

    def test_legacy_folded_header_values_do_not_leak_continuations(self):
        text = ("Authorization: Bearer\r\n"
                " fake-folded-token\r\n"
                "Cookie: first=fake-one;\r\n"
                "\tsecond=fake-two\r\n"
                "Accept: text/plain\r\n")
        result = redact(text)
        self.assertNotIn("fake-", result)
        self.assertEqual(result.count("[REDACTED]"), 2)
        self.assertIn("Accept: text/plain\r\n", result)

    def test_url_and_generic_secret_redaction_is_preserved(self):
        text = ("https://fake-user:fake-password@example.com/?api_key=fake-key&password=fake-pass\n"
                "access_token=fake-access secret=fake-secret")
        result = redact(text)
        for value in ("fake-user", "fake-password", "fake-key", "fake-pass", "fake-access", "fake-secret"):
            self.assertNotIn(value, result)
        self.assertIn("example.com", result)


if __name__ == "__main__":
    unittest.main()
