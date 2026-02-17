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
from app.matching import generate_all_matches, top_intro_pairs, top_non_obvious_pairs


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "test_profiles.json"
INGESTED_DATA_PATH = ROOT / "data" / "runtime_profiles.json"
STATIC_DIR = ROOT / "app" / "static"


class ActionUpsert(BaseModel):
    from_id: str = Field(min_length=1)
    to_id: str = Field(min_length=1)
    status: Literal["pending", "approved", "rejected"]
    notes: str = Field(default="")


class ProfileIngestRequest(BaseModel):
    profiles: List[Dict[str, Any]]
    overwrite: bool = True


app = FastAPI(
    title="Proof of Talk Matchmaking API",
    description="AI matchmaking, explainability, and organizer control plane for Proof of Talk 2026.",
    version="0.3.0",
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


def _active_profiles_path() -> Path:
    return INGESTED_DATA_PATH if INGESTED_DATA_PATH.exists() else DATA_PATH


def _read_raw_profiles() -> List[Dict[str, Any]]:
    path = _active_profiles_path()
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, list):
        raise ValueError("profiles source must be a JSON array")
    return loaded


def _validate_profile_minimum(profile: Dict[str, Any]) -> None:
    if not profile.get("id"):
        raise ValueError("profile missing id")
    if not profile.get("name"):
        raise ValueError("profile missing name")


def _write_profiles(profiles: List[Dict[str, Any]], overwrite: bool) -> int:
    for p in profiles:
        _validate_profile_minimum(p)

    if not overwrite and INGESTED_DATA_PATH.exists():
        existing = json.loads(INGESTED_DATA_PATH.read_text(encoding="utf-8"))
        by_id = {str(x["id"]): x for x in existing if isinstance(x, dict) and x.get("id")}
        for p in profiles:
            by_id[str(p["id"])] = p
        merged = list(by_id.values())
        INGESTED_DATA_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
        return len(merged)

    INGESTED_DATA_PATH.write_text(json.dumps(profiles, indent=2), encoding="utf-8")
    return len(profiles)


def load_profiles() -> List[Dict[str, Any]]:
    return [enrich_profile(p) for p in _read_raw_profiles()]


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
def profiles() -> Dict[str, Any]:
    path = _active_profiles_path()
    return {"profiles": load_profiles(), "source": str(path.name)}


@app.post("/api/profiles/ingest")
def ingest_profiles(payload: ProfileIngestRequest) -> Dict[str, Any]:
    count = _write_profiles(payload.profiles, overwrite=payload.overwrite)
    return {
        "status": "ok",
        "stored_profiles": count,
        "source": str(INGESTED_DATA_PATH.name),
        "overwrite": payload.overwrite,
    }


@app.post("/api/profiles/reset")
def reset_profiles() -> Dict[str, Any]:
    if INGESTED_DATA_PATH.exists():
        INGESTED_DATA_PATH.unlink()
    return {"status": "ok", "source": str(DATA_PATH.name)}


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


@app.get("/api/non-obvious-matches")
def non_obvious_matches(limit: int = Query(default=5, ge=1, le=20)) -> Dict[str, Any]:
    profiles_list = load_profiles()
    pairs = top_non_obvious_pairs(profiles_list, limit=limit)
    actions = action_map()
    for row in pairs:
        key = f"{row['from_id']}::{row['to_id']}"
        row["action"] = actions.get(
            key,
            {
                "from_id": row["from_id"],
                "to_id": row["to_id"],
                "status": "pending",
                "notes": "",
                "updated_at": "",
            },
        )
    return {"non_obvious_pairs": pairs}


@app.get("/api/dashboard")
def dashboard() -> Dict[str, Any]:
    profiles_list = load_profiles()
    per_profile = with_actions(generate_all_matches(profiles_list))
    pairs = top_intro_pairs(profiles_list, limit=10)
    non_obvious = top_non_obvious_pairs(profiles_list, limit=5)
    actions = action_map()

    for row in pairs:
        key = f"{row['from_id']}::{row['to_id']}"
        row["action"] = actions.get(
            key,
            {
                "from_id": row["from_id"],
                "to_id": row["to_id"],
                "status": "pending",
                "notes": "",
                "updated_at": "",
            },
        )

    for row in non_obvious:
        key = f"{row['from_id']}::{row['to_id']}"
        row["action"] = actions.get(
            key,
            {
                "from_id": row["from_id"],
                "to_id": row["to_id"],
                "status": "pending",
                "notes": "",
                "updated_at": "",
            },
        )

    risk_counts = {"low": 0, "medium": 0, "high": 0}
    for rows in per_profile.values():
        for m in rows:
            level = m.get("risk_level", "medium")
            if level in risk_counts:
                risk_counts[level] += 1

    return {
        "overview": {
            "attendee_count": len(profiles_list),
            "recommended_intro_count": len(pairs),
            "actioned_intro_count": len(get_all_actions()),
            "risk_distribution": risk_counts,
        },
        "top_intro_pairs": pairs,
        "top_non_obvious_pairs": non_obvious,
        "per_profile": per_profile,
    }
