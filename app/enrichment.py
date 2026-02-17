from __future__ import annotations

from typing import Any, Dict


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
            " ".join(profile.get("looking_for", [])),
        ]
    ).lower()

    inferred_tags = []
    for keyword, tags in KEYWORD_ENRICHMENT.items():
        if keyword in text_blob:
            inferred_tags.extend(tags)

    inferred_tags = sorted(set(inferred_tags))

    profile_copy = dict(profile)
    profile_copy["enrichment"] = {
        "inferred_tags": inferred_tags,
        "source_confidence": 0.68 if inferred_tags else 0.52,
        "sources": [
            "registration_form",
            "company_website_mock",
            "market_data_mock",
        ],
    }
    return profile_copy
