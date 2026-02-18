from __future__ import annotations

import os
from typing import Any, Dict

from app.connectors import run_live_connectors

KEYWORD_ENRICHMENT = {
    "custody": ["institutional custody", "regulated operations", "asset security"],
    "defi": ["institutional DeFi", "on-chain yield", "smart contract risk"],
    "cbdc": ["public infrastructure", "monetary policy", "regulatory sandbox"],
    "compliance": ["KYC/AML", "governance controls", "auditability"],
    "tokenized": ["tokenized securities", "RWA rails", "settlement modernization"],
}


def enrich_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Mock enrichment layer for demo reliability.

    In production, this is where connectors for company sites, social data, and
    funding databases would normalize and merge additional signals.
    """

    text_blob = " ".join(
        [
            str(profile.get("mandate", "")),
            str(profile.get("product", "")),
            str(profile.get("thesis", "")),
            str(profile.get("focus", "")),
            str(profile.get("bio", "")),
            " ".join(profile.get("looking_for", [])),
        ]
    ).lower()

    inferred_tags = []
    for keyword, tags in KEYWORD_ENRICHMENT.items():
        if keyword in text_blob:
            inferred_tags.extend(tags)

    inferred_tags = sorted(set(inferred_tags))

    live_enabled = os.getenv("ENABLE_LIVE_ENRICHMENT", "0") == "1"
    live_result = run_live_connectors(profile) if live_enabled else {
        "tags": [],
        "confidence_delta": 0.0,
        "sources": [],
        "errors": [],
    }

    merged_tags = sorted(set(inferred_tags + live_result["tags"]))
    base_confidence = 0.68 if inferred_tags else 0.52
    confidence = min(base_confidence + live_result["confidence_delta"], 0.95)

    profile_copy = dict(profile)
    profile_copy["enrichment"] = {
        "inferred_tags": merged_tags,
        "source_confidence": round(confidence, 3),
        "sources": [
            "registration_form",
            "company_website_mock",
            "market_data_mock",
            *live_result["sources"],
        ],
        "live_connectors_enabled": live_enabled,
        "live_connector_errors": live_result["errors"],
        "live_connector_results": live_result.get("connector_results", []),
    }
    return profile_copy
