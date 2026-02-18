from __future__ import annotations

import os
import unittest

from app.auth import create_access_token, decode_access_token, hash_password, verify_password


class AuthTest(unittest.TestCase):
    def setUp(self) -> None:
        self._prev = os.environ.get("APP_JWT_SECRET")
        os.environ["APP_JWT_SECRET"] = "unit-test-secret"

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("APP_JWT_SECRET", None)
        else:
            os.environ["APP_JWT_SECRET"] = self._prev

    def test_password_hash_round_trip(self) -> None:
        stored = hash_password("strong-pass-123")
        self.assertTrue(verify_password("strong-pass-123", stored))
        self.assertFalse(verify_password("wrong-pass", stored))

    def test_token_round_trip(self) -> None:
        token = create_access_token("u_1", "a@example.com", "attendee", ttl_seconds=120)
        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], "u_1")
        self.assertEqual(payload["email"], "a@example.com")

    def test_token_tamper_is_rejected(self) -> None:
        token = create_access_token("u_1", "a@example.com", "attendee", ttl_seconds=120)
        parts = token.split(".")
        parts[1] = parts[1][::-1]
        tampered = ".".join(parts)
        with self.assertRaises(ValueError):
            decode_access_token(tampered)


if __name__ == "__main__":
    unittest.main()
