from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


COMPANY_WEBSITE_HINTS = {
    "abu dhabi sovereign wealth fund": "https://www.adia.ae",
    "vaultbridge": "https://vaultbridge.example.com",
    "meridian crypto ventures": "https://meridian-crypto.example.com",
    "nexalayer": "https://nexalayer.example.com",
    "deutsche bundesbank": "https://www.bundesbank.de",
}

KEYWORD_TAGS = {
    "custody": "institutional custody",
    "compliance": "compliance operations",
    "regulatory": "regulatory readiness",
    "tokenized": "tokenized securities",
    "defi": "institutional DeFi",
    "sandbox": "regulatory sandbox",
    "pilot": "pilot readiness",
}


def infer_company_website(profile: Dict[str, Any]) -> Optional[str]:
    explicit = profile.get("website")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    org = str(profile.get("organization", "")).lower()
    return COMPANY_WEBSITE_HINTS.get(org)


def _download_text(url: str, timeout_seconds: int = 4) -> str:
    req = Request(url=url, headers={"User-Agent": "ProofOfTalk-Matchmaker/0.3"})
    with urlopen(req, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def website_signal_enrichment(profile: Dict[str, Any]) -> Dict[str, Any]:
    website = infer_company_website(profile)
    if not website:
        return {
            "tags": [],
            "confidence_delta": 0.0,
            "sources": [],
            "errors": ["website_not_available"],
        }

    try:
        text = _download_text(website)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return {
            "tags": [],
            "confidence_delta": 0.0,
            "sources": [f"company_website_live:{website}"],
            "errors": [f"website_fetch_failed:{type(exc).__name__}"],
        }

    tags: List[str] = []
    for keyword, tag in KEYWORD_TAGS.items():
        if keyword in text:
            tags.append(tag)
    tags = sorted(set(tags))

    return {
        "tags": tags,
        "confidence_delta": 0.08 if tags else 0.02,
        "sources": [f"company_website_live:{website}"],
        "errors": [],
    }


def funding_signal_enrichment(profile: Dict[str, Any]) -> Dict[str, Any]:
    # Pluggable connector point; can be replaced with Crunchbase/Pitchbook adapters.
    stage = str(profile.get("stage", "")).lower()
    raised = str(profile.get("capital_raised", "")).lower()
    tags: List[str] = []
    if "series" in stage:
        tags.append(f"funding_stage:{stage}")
    if raised:
        tags.append("venture_backed")
    return {
        "tags": tags,
        "confidence_delta": 0.05 if tags else 0.0,
        "sources": ["funding_connector_structured_profile"],
        "errors": [],
    }


def run_live_connectors(profile: Dict[str, Any]) -> Dict[str, Any]:
    website = website_signal_enrichment(profile)
    funding = funding_signal_enrichment(profile)

    all_tags = sorted(set(website["tags"] + funding["tags"]))
    all_sources = website["sources"] + funding["sources"]
    all_errors = website["errors"] + funding["errors"]
    confidence_delta = website["confidence_delta"] + funding["confidence_delta"]

    return {
        "tags": all_tags,
        "confidence_delta": confidence_delta,
        "sources": all_sources,
        "errors": all_errors,
    }
