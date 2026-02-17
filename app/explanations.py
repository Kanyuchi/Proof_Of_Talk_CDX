from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _template_rationale(
    a: Dict[str, Any], b: Dict[str, Any], fit: float, comp: float, ready: float
) -> str:
    reasons: List[str] = []
    if fit >= 0.2:
        reasons.append("strong thesis overlap")
    if comp >= 0.85:
        reasons.append("high strategic complementarity")
    if ready >= 0.75:
        reasons.append("both sides show near-term execution readiness")
    if not reasons:
        reasons.append("adjacent priorities with potential non-obvious collaboration")
    return (
        f"{a['name']} ↔ {b['name']}: "
        + ", ".join(reasons)
        + ". Recommended for a high-value intro based on product-investor-regulatory fit."
    )


def _llm_enabled() -> bool:
    return os.getenv("ENABLE_LLM_RATIONALE", "0") == "1" and bool(os.getenv("OPENAI_API_KEY"))


def _openai_rationale(
    a: Dict[str, Any], b: Dict[str, Any], fit: float, comp: float, ready: float
) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    prompt = {
        "source": {"name": a.get("name"), "role": a.get("title"), "org": a.get("organization")},
        "target": {"name": b.get("name"), "role": b.get("title"), "org": b.get("organization")},
        "scores": {"fit": fit, "complementarity": comp, "readiness": ready},
        "task": "Write one concise sentence explaining why this intro is high-value and near-term actionable.",
    }

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": "You write concise B2B matchmaking rationales for conference organizers."},
            {"role": "user", "content": json.dumps(prompt)},
        ],
        "max_output_tokens": 80,
    }
    req = Request(
        url="https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=6) as response:
        body = json.loads(response.read().decode("utf-8"))
    text = body.get("output_text", "").strip()
    if text:
        return text
    raise ValueError("No output_text in OpenAI response")


def generate_match_rationale(
    a: Dict[str, Any], b: Dict[str, Any], fit: float, comp: float, ready: float
) -> str:
    if not _llm_enabled():
        return _template_rationale(a, b, fit, comp, ready)
    try:
        return _openai_rationale(a, b, fit, comp, ready)
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return _template_rationale(a, b, fit, comp, ready)
