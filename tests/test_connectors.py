from __future__ import annotations

import os
import unittest

from app.connectors import (
    infer_company_website,
    parse_clearbit_payload,
    parse_crunchbase_payload,
    parse_openalex_payload,
    run_live_connectors,
    structured_profile_funding_enrichment,
)


class ConnectorsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_live = os.environ.get("LIVE_CONNECTORS")

    def tearDown(self) -> None:
        if self._previous_live is None:
            os.environ.pop("LIVE_CONNECTORS", None)
        else:
            os.environ["LIVE_CONNECTORS"] = self._previous_live

    def test_infer_company_website_from_hint(self) -> None:
        profile = {"organization": "Deutsche Bundesbank"}
        self.assertEqual(infer_company_website(profile), "https://www.bundesbank.de")

    def test_structured_funding_enrichment(self) -> None:
        profile = {"stage": "Series B", "capital_raised": "$40M"}
        result = structured_profile_funding_enrichment(profile)
        self.assertIn("funding_stage:series b", result["tags"])
        self.assertIn("venture_backed", result["tags"])

    def test_parse_clearbit_payload(self) -> None:
        payload = {
            "category": {"sector": "Financial Services", "industry": "Capital Markets"},
            "metrics": {"employees": 220},
        }
        tags = parse_clearbit_payload(payload)
        self.assertIn("industry:financial services", tags)
        self.assertIn("industry:capital markets", tags)
        self.assertIn("company_size:mid_market", tags)

    def test_parse_crunchbase_payload(self) -> None:
        payload = {
            "funding_stage": "Series B",
            "total_funding_usd": "40000000",
            "cards": {"raised_investments": [{"announced_on": "2025-03-01"}]},
        }
        tags = parse_crunchbase_payload(payload)
        self.assertIn("funding_stage:series b", tags)
        self.assertIn("venture_backed", tags)
        self.assertIn("active_funding_history", tags)

    def test_parse_openalex_payload(self) -> None:
        payload = {
            "results": [
                {
                    "works_count": 12000,
                    "x_concepts": [
                        {"display_name": "Blockchain"},
                        {"display_name": "Financial Regulation"},
                    ],
                }
            ]
        }
        tags = parse_openalex_payload(payload)
        self.assertIn("research_intensity:high", tags)
        self.assertIn("research_topic:blockchain", tags)

    def test_run_live_connectors_with_missing_keys(self) -> None:
        os.environ["LIVE_CONNECTORS"] = "clearbit,crunchbase,structured_funding"
        profile = {"organization": "VaultBridge", "stage": "Series B", "capital_raised": "$40M"}
        result = run_live_connectors(profile)
        self.assertIn("funding_stage:series b", result["tags"])
        self.assertIn("clearbit_api_key_missing", result["errors"])
        self.assertIn("crunchbase_api_key_missing", result["errors"])


if __name__ == "__main__":
    unittest.main()
