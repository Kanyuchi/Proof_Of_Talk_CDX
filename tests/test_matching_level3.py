from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.enrichment import enrich_profile
from app.matching import generate_all_matches, top_non_obvious_pairs


class MatchingLevel3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        profiles = json.loads(Path("data/test_profiles.json").read_text(encoding="utf-8"))
        cls.enriched = [enrich_profile(p) for p in profiles]

    def test_generate_all_matches_has_risk_fields(self) -> None:
        result = generate_all_matches(self.enriched)
        for _pid, matches in result.items():
            self.assertGreaterEqual(len(matches), 1)
            sample = matches[0]
            self.assertIn("risk_level", sample)
            self.assertIn("risk_reasons", sample)
            self.assertIn(sample["risk_level"], {"low", "medium", "high"})

    def test_non_obvious_pairs_exist(self) -> None:
        pairs = top_non_obvious_pairs(self.enriched, limit=5)
        self.assertGreaterEqual(len(pairs), 1)
        sample = pairs[0]
        self.assertIn("novelty_score", sample)
        self.assertIn("risk_level", sample)
        self.assertGreaterEqual(sample["novelty_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
