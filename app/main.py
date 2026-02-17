from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import action_map, get_all_actions, init_db, upsert_action
from app.enrichment import enrich_profile
from app.matching import generate_all_matches, top_intro_pairs


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "test_profiles.json"
STATIC_DIR = ROOT / "app" / "static"


class ActionUpsert(BaseModel):
    from_id: str = Field(min_length=1)
    to_id: str = Field(min_length=1)
    status: Literal["pending", "approved", "rejected"]
    notes: str = Field(default="")


app = FastAPI(
    title="Proof of Talk Matchmaking API",
    description="AI matchmaking, explainability, and organizer control plane for Proof of Talk 2026.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def load_profiles() -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    return [enrich_profile(p) for p in profiles]


def with_actions(per_profile: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    actions = action_map()
    merged: Dict[str, List[Dict[str, Any]]] = {}
    for source_id, matches in per_profile.items():
        out: List[Dict[str, Any]] = []
        for match in matches:
            key = f"{source_id}::{match['target_id']}"
            match_copy = dict(match)
            match_copy["action"] = actions.get(
                key,
                {
                    "from_id": source_id,
                    "to_id": match["target_id"],
                    "status": "pending",
                    "notes": "",
                    "updated_at": "",
                },
            )
            out.append(match_copy)
        merged[source_id] = out
    return merged


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/profiles")
def profiles() -> Dict[str, List[Dict[str, Any]]]:
    return {"profiles": load_profiles()}


@app.get("/api/actions")
def actions() -> Dict[str, List[Dict[str, str]]]:
    return {"actions": get_all_actions()}


@app.post("/api/actions")
def save_action(payload: ActionUpsert) -> Dict[str, str]:
    now = datetime.now(timezone.utc).isoformat()
    upsert_action(payload.from_id, payload.to_id, payload.status, payload.notes, now)
    return {"status": "ok", "updated_at": now}


@app.get("/api/matches")
def matches(profile_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    profiles_list = load_profiles()
    per_profile = with_actions(generate_all_matches(profiles_list))
    if profile_id:
        if profile_id not in per_profile:
            raise HTTPException(status_code=404, detail="profile not found")
        return {"profile_id": profile_id, "matches": per_profile[profile_id]}
    return {"matches": per_profile}


@app.get("/api/dashboard")
def dashboard() -> Dict[str, Any]:
    profiles_list = load_profiles()
    per_profile = with_actions(generate_all_matches(profiles_list))
    pairs = top_intro_pairs(profiles_list, limit=10)
    action_lookup = action_map()
    for row in pairs:
        key = f"{row['from_id']}::{row['to_id']}"
        row["action"] = action_lookup.get(
            key,
            {
                "from_id": row["from_id"],
                "to_id": row["to_id"],
                "status": "pending",
                "notes": "",
                "updated_at": "",
            },
        )
    return {
        "overview": {
            "attendee_count": len(profiles_list),
            "recommended_intro_count": len(pairs),
            "actioned_intro_count": len(get_all_actions()),
        },
        "top_intro_pairs": pairs,
        "per_profile": per_profile,
    }
