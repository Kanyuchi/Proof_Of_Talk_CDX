from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.concierge import concierge_reply


class ConciergeTest(unittest.TestCase):
    def setUp(self) -> None:
        self._prev_enable = os.environ.get("ENABLE_CONCIERGE_LLM")
        self._prev_key = os.environ.get("OPENAI_API_KEY")
        os.environ["ENABLE_CONCIERGE_LLM"] = "0"
        os.environ.pop("OPENAI_API_KEY", None)

    def tearDown(self) -> None:
        if self._prev_enable is None:
            os.environ.pop("ENABLE_CONCIERGE_LLM", None)
        else:
            os.environ["ENABLE_CONCIERGE_LLM"] = self._prev_enable
        if self._prev_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = self._prev_key

    def test_fallback_mode_when_llm_disabled(self) -> None:
        out = concierge_reply(
            message="suggest intros",
            profile={"name": "Amara", "looking_for": ["institutional partnerships"]},
            dashboard={"top_intro_pairs": [{"from_name": "A", "to_name": "B"}]},
            history=[],
        )
        self.assertEqual(out["mode"], "fallback")
        self.assertIn("Concierge recommendation", out["reply"])

    @patch("app.concierge._openai_reply", side_effect=TimeoutError("timeout"))
    def test_llm_error_falls_back(self, _mock_openai) -> None:
        os.environ["ENABLE_CONCIERGE_LLM"] = "1"
        os.environ["OPENAI_API_KEY"] = "x"
        out = concierge_reply(message="hello", profile=None, dashboard=None, history=[])
        self.assertEqual(out["mode"], "fallback")


if __name__ == "__main__":
    unittest.main()
