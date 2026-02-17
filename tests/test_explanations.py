from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from app.explanations import generate_match_rationale


class _FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ExplanationsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._prev_enable = os.environ.get("ENABLE_LLM_RATIONALE")
        self._prev_key = os.environ.get("OPENAI_API_KEY")
        os.environ["ENABLE_LLM_RATIONALE"] = "1"
        os.environ["OPENAI_API_KEY"] = "test-key"

    def tearDown(self) -> None:
        if self._prev_enable is None:
            os.environ.pop("ENABLE_LLM_RATIONALE", None)
        else:
            os.environ["ENABLE_LLM_RATIONALE"] = self._prev_enable
        if self._prev_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = self._prev_key

    def _profiles(self):
        a = {"name": "Amara", "title": "Director", "organization": "SWF"}
        b = {"name": "Marcus", "title": "CEO", "organization": "VaultBridge"}
        return a, b

    @patch("app.explanations.urlopen")
    def test_llm_path_returns_output_text(self, mock_urlopen) -> None:
        mock_urlopen.return_value = _FakeResponse({"output_text": "High-value intro due to custody + readiness."})
        a, b = self._profiles()
        text = generate_match_rationale(a, b, 0.31, 0.9, 0.81)
        self.assertEqual(text, "High-value intro due to custody + readiness.")

    @patch("app.explanations.urlopen")
    def test_llm_empty_output_falls_back_to_template(self, mock_urlopen) -> None:
        mock_urlopen.return_value = _FakeResponse({"output_text": ""})
        a, b = self._profiles()
        text = generate_match_rationale(a, b, 0.31, 0.9, 0.81)
        self.assertIn("Amara", text)
        self.assertIn("Marcus", text)

    @patch("app.explanations.urlopen", side_effect=TimeoutError("timeout"))
    def test_llm_timeout_falls_back_to_template(self, _mock_urlopen) -> None:
        a, b = self._profiles()
        text = generate_match_rationale(a, b, 0.1, 0.4, 0.2)
        self.assertIn("Recommended for a high-value intro", text)

    def test_llm_disabled_uses_template(self) -> None:
        os.environ["ENABLE_LLM_RATIONALE"] = "0"
        a, b = self._profiles()
        text = generate_match_rationale(a, b, 0.2, 0.85, 0.75)
        self.assertIn("high strategic complementarity", text)


if __name__ == "__main__":
    unittest.main()
