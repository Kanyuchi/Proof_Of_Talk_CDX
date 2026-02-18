from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _llm_enabled() -> bool:
    return os.getenv("ENABLE_CONCIERGE_LLM", "0") == "1" and bool(os.getenv("OPENAI_API_KEY"))


def _fallback_reply(message: str, profile: Dict[str, Any] | None, dashboard: Dict[str, Any] | None) -> str:
    profile_hint = ""
    if profile:
        name = profile.get("name", "this attendee")
        looking_for = ", ".join(profile.get("looking_for", [])[:2]) if isinstance(profile.get("looking_for"), list) else ""
        profile_hint = f"For {name}, prioritize meetings aligned with {looking_for or 'their strategic priorities'}."

    top_pair_hint = ""
    if dashboard and dashboard.get("top_intro_pairs"):
        pair = dashboard["top_intro_pairs"][0]
        top_pair_hint = f" Current top intro candidate is {pair.get('from_name')} ↔ {pair.get('to_name')}."

    return (
        "Concierge recommendation: start with high-confidence, low-risk intros first, then add one non-obvious pair."
        f" {profile_hint}{top_pair_hint} Next step based on your request '{message}': shortlist 3 intros and send tailored context notes."
    ).strip()


def _openai_reply(message: str, profile: Dict[str, Any] | None, dashboard: Dict[str, Any] | None) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": (
                    "You are an AI concierge for a premium conference matchmaking engine. "
                    "Give concise, practical recommendations with explicit next actions."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "message": message,
                        "profile": profile or {},
                        "dashboard_overview": (dashboard or {}).get("overview", {}),
                        "top_intro_pairs": (dashboard or {}).get("top_intro_pairs", [])[:3],
                        "top_non_obvious_pairs": (dashboard or {}).get("top_non_obvious_pairs", [])[:2],
                    }
                ),
            },
        ],
        "max_output_tokens": 180,
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
    with urlopen(req, timeout=8) as response:
        body = json.loads(response.read().decode("utf-8"))
    text = str(body.get("output_text", "")).strip()
    if not text:
        raise ValueError("No output_text in response")
    return text


def concierge_reply(
    message: str,
    profile: Dict[str, Any] | None,
    dashboard: Dict[str, Any] | None,
    history: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    if not message.strip():
        return {"reply": "Please share a specific ask (e.g., 'suggest 3 intros for Amara').", "mode": "fallback"}

    try:
        if _llm_enabled():
            text = _openai_reply(message=message, profile=profile, dashboard=dashboard)
            return {"reply": text, "mode": "llm"}
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        pass

    return {
        "reply": _fallback_reply(message=message, profile=profile, dashboard=dashboard),
        "mode": "fallback",
        "history_used": len(history or []),
    }
