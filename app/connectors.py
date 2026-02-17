from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


COMPANY_WEBSITE_HINTS = {
    "abu dhabi sovereign wealth fund": "https://www.adia.ae",
    "vaultbridge": "https://vaultbridge.example.com",
    "meridian crypto ventures": "https://meridian-crypto.example.com",
    "nexalayer": "https://nexalayer.example.com",
    "deutsche bundesbank": "https://www.bundesbank.de",
}

WEBSITE_KEYWORD_TAGS = {
    "custody": "institutional custody",
    "compliance": "compliance operations",
    "regulatory": "regulatory readiness",
    "tokenized": "tokenized securities",
    "defi": "institutional defi",
    "sandbox": "regulatory sandbox",
    "pilot": "pilot readiness",
}


def _result(
    connector: str,
    tags: Optional[List[str]] = None,
    confidence_delta: float = 0.0,
    sources: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "connector": connector,
        "tags": sorted(set(tags or [])),
        "confidence_delta": confidence_delta,
        "sources": sources or [],
        "errors": errors or [],
    }


def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout_seconds: int = 5) -> Any:
    req = Request(url=url, headers=headers or {"User-Agent": "ProofOfTalk-Matchmaker/0.4"})
    with urlopen(req, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _download_text(url: str, timeout_seconds: int = 4) -> str:
    req = Request(url=url, headers={"User-Agent": "ProofOfTalk-Matchmaker/0.4"})
    with urlopen(req, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def _slugify(text: str) -> str:
    out = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return out or "unknown"


def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def infer_company_website(profile: Dict[str, Any]) -> Optional[str]:
    explicit = profile.get("website")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    org = str(profile.get("organization", "")).lower()
    return COMPANY_WEBSITE_HINTS.get(org)


def parse_clearbit_payload(payload: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    root = payload.get("company") if isinstance(payload.get("company"), dict) else payload
    category = root.get("category") or {}
    sector = str(category.get("sector", "")).strip().lower()
    industry = str(category.get("industry", "")).strip().lower()
    sub_industry = str(category.get("subIndustry", "")).strip().lower()
    for value in [sector, industry, sub_industry]:
        if value:
            tags.append(f"industry:{value}")

    metrics = root.get("metrics") or {}
    employees = metrics.get("employees")
    if isinstance(employees, int):
        if employees >= 1000:
            tags.append("company_size:enterprise")
        elif employees >= 100:
            tags.append("company_size:mid_market")
        elif employees > 0:
            tags.append("company_size:early")

    return sorted(set(tags))


def parse_crunchbase_payload(payload: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    if isinstance(payload, dict):
        root = payload.get("properties") if isinstance(payload.get("properties"), dict) else payload
        stage = str(root.get("funding_stage", "")).strip().lower()
        if stage:
            tags.append(f"funding_stage:{stage}")
        total_funding = str(root.get("total_funding_usd", "") or root.get("funding_total", "")).strip()
        if total_funding:
            tags.append("venture_backed")

        cards = payload.get("cards") or {}
        raised = cards.get("raised_investments") or []
        if isinstance(raised, dict):
            raised = raised.get("items") or raised.get("edges") or []
        if isinstance(raised, list) and raised:
            tags.append("active_funding_history")

    return sorted(set(tags))


def parse_openalex_payload(payload: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list) or not results:
        return tags

    top = results[0]
    works_count = top.get("works_count")
    if isinstance(works_count, int):
        if works_count >= 10000:
            tags.append("research_intensity:high")
        elif works_count >= 1000:
            tags.append("research_intensity:medium")

    concepts = top.get("x_concepts") or top.get("concepts") or []
    if isinstance(concepts, list):
        for concept in concepts[:3]:
            if not isinstance(concept, dict):
                continue
            name = str(concept.get("display_name", "")).strip().lower()
            if name:
                tags.append(f"research_topic:{name}")
    return sorted(set(tags))


def website_signal_enrichment(profile: Dict[str, Any]) -> Dict[str, Any]:
    website = infer_company_website(profile)
    if not website:
        return _result("website", errors=["website_not_available"])
    try:
        text = _download_text(website)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return _result(
            "website",
            sources=[f"company_website_live:{website}"],
            errors=[f"website_fetch_failed:{type(exc).__name__}"],
        )

    tags: List[str] = []
    for keyword, tag in WEBSITE_KEYWORD_TAGS.items():
        if keyword in text:
            tags.append(tag)
    return _result(
        "website",
        tags=tags,
        confidence_delta=0.08 if tags else 0.02,
        sources=[f"company_website_live:{website}"],
    )


def structured_profile_funding_enrichment(profile: Dict[str, Any]) -> Dict[str, Any]:
    stage = str(profile.get("stage", "")).lower().strip()
    raised = str(profile.get("capital_raised", "")).lower().strip()
    tags: List[str] = []
    if "series" in stage:
        tags.append(f"funding_stage:{stage}")
    if raised:
        tags.append("venture_backed")
    return _result(
        "structured_funding",
        tags=tags,
        confidence_delta=0.05 if tags else 0.0,
        sources=["funding_connector_structured_profile"],
    )


def clearbit_enrichment(profile: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("CLEARBIT_API_KEY", "").strip()
    if not api_key:
        return _result("clearbit", errors=["clearbit_api_key_missing"])

    website = infer_company_website(profile)
    if not website:
        return _result("clearbit", errors=["website_not_available"])
    domain = _extract_domain(website)
    if not domain:
        return _result("clearbit", errors=["company_domain_not_available"])

    endpoint_template = os.getenv(
        "CLEARBIT_COMPANY_URL",
        "https://company.clearbit.com/v2/companies/find?domain={domain}",
    )
    endpoint = endpoint_template.format(domain=quote(domain))
    try:
        payload = _http_get_json(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": "ProofOfTalk-Matchmaker/0.4"},
        )
        tags = parse_clearbit_payload(payload if isinstance(payload, dict) else {})
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return _result(
            "clearbit",
            sources=[f"clearbit:{domain}"],
            errors=[f"clearbit_fetch_failed:{type(exc).__name__}"],
        )
    return _result(
        "clearbit",
        tags=tags,
        confidence_delta=0.06 if tags else 0.01,
        sources=[f"clearbit:{domain}"],
    )


def crunchbase_enrichment(profile: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("CRUNCHBASE_API_KEY", "").strip()
    if not api_key:
        return _result("crunchbase", errors=["crunchbase_api_key_missing"])
    org_name = str(profile.get("organization", "")).strip()
    if not org_name:
        return _result("crunchbase", errors=["organization_missing"])

    base_url = os.getenv("CRUNCHBASE_BASE_URL", "https://api.crunchbase.com/api/v4/entities/organizations")
    org_slug = _slugify(org_name)
    endpoint = f"{base_url}/{quote(org_slug)}?user_key={quote(api_key)}"
    try:
        payload = _http_get_json(endpoint)
        tags = parse_crunchbase_payload(payload if isinstance(payload, dict) else {})
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return _result(
            "crunchbase",
            sources=[f"crunchbase:{org_slug}"],
            errors=[f"crunchbase_fetch_failed:{type(exc).__name__}"],
        )
    return _result(
        "crunchbase",
        tags=tags,
        confidence_delta=0.06 if tags else 0.01,
        sources=[f"crunchbase:{org_slug}"],
    )


def openalex_enrichment(profile: Dict[str, Any]) -> Dict[str, Any]:
    org_name = str(profile.get("organization", "")).strip()
    if not org_name:
        return _result("openalex", errors=["organization_missing"])

    endpoint = f"https://api.openalex.org/institutions?search={quote(org_name)}&per-page=1"
    try:
        payload = _http_get_json(endpoint)
        tags = parse_openalex_payload(payload if isinstance(payload, dict) else {})
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return _result(
            "openalex",
            sources=[f"openalex:{_slugify(org_name)}"],
            errors=[f"openalex_fetch_failed:{type(exc).__name__}"],
        )
    return _result(
        "openalex",
        tags=tags,
        confidence_delta=0.04 if tags else 0.0,
        sources=[f"openalex:{_slugify(org_name)}"],
    )


CONNECTOR_REGISTRY = {
    "website": website_signal_enrichment,
    "structured_funding": structured_profile_funding_enrichment,
    "clearbit": clearbit_enrichment,
    "crunchbase": crunchbase_enrichment,
    "openalex": openalex_enrichment,
}


def _enabled_connectors() -> List[str]:
    raw = os.getenv("LIVE_CONNECTORS", "website,structured_funding")
    requested = [c.strip() for c in raw.split(",") if c.strip()]
    valid = [c for c in requested if c in CONNECTOR_REGISTRY]
    return valid or ["website", "structured_funding"]


def run_live_connectors(profile: Dict[str, Any]) -> Dict[str, Any]:
    connector_results = []
    for connector_name in _enabled_connectors():
        handler = CONNECTOR_REGISTRY[connector_name]
        connector_results.append(handler(profile))

    all_tags: List[str] = []
    all_sources: List[str] = []
    all_errors: List[str] = []
    confidence_delta = 0.0
    for row in connector_results:
        all_tags.extend(row["tags"])
        all_sources.extend(row["sources"])
        all_errors.extend(row["errors"])
        confidence_delta += float(row["confidence_delta"])

    return {
        "tags": sorted(set(all_tags)),
        "confidence_delta": min(confidence_delta, 0.2),
        "sources": all_sources,
        "errors": all_errors,
        "connector_results": connector_results,
    }
