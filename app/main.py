from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.auth import bearer_token, create_access_token, decode_access_token, hash_password, verify_password
from app.concierge import concierge_reply
from app.db import (
    action_map,
    backend_summary,
    create_user,
    get_all_actions,
    get_chat_messages_between,
    get_recent_chat_activity_for_user,
    get_user_by_email,
    get_user_by_id,
    init_db,
    insert_chat_message,
    list_users,
    update_user_profile_fields,
    upsert_action,
)
from app.enrichment import enrich_profile
from app.matching import generate_all_matches, top_intro_pairs, top_non_obvious_pairs


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "test_profiles.json"
INGESTED_DATA_PATH = ROOT / "data" / "runtime_profiles.json"
STATIC_DIR = ROOT / "app" / "static"

ROLE_CHOICES = {"vip", "speaker", "sponsor", "delegate", "attendee"}


class ActionUpsert(BaseModel):
    from_id: str = Field(min_length=1)
    to_id: str = Field(min_length=1)
    status: Literal["pending", "approved", "rejected"]
    notes: str = Field(default="")


class ProfileIngestRequest(BaseModel):
    profiles: List[Dict[str, Any]]
    overwrite: bool = True


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    title: str = Field(default="")
    organization: str = Field(default="")
    role: str = Field(default="attendee")
    bio: str = Field(default="")
    website: str = Field(default="")
    looking_for: List[str] = Field(default_factory=list)
    focus: List[str] = Field(default_factory=list)
    social_links: Dict[str, str] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=1)


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=2)
    title: str = Field(default="")
    organization: str = Field(default="")
    role: str = Field(default="attendee")
    bio: str = Field(default="")
    website: str = Field(default="")
    looking_for: List[str] = Field(default_factory=list)
    focus: List[str] = Field(default_factory=list)
    social_links: Dict[str, str] = Field(default_factory=dict)


class ChatMessageCreate(BaseModel):
    to_user_id: str = Field(min_length=1)
    body: str = Field(min_length=1, max_length=3000)


class ConciergeChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    profile_id: Optional[str] = None
    history: List[Dict[str, str]] = Field(default_factory=list)


class EnrichmentRefreshRequest(BaseModel):
    profile_id: Optional[str] = None
    live_enabled: bool = True
    connectors: List[str] = Field(default_factory=list)


app = FastAPI(
    title="Proof of Talk Matchmaking API",
    description="AI matchmaking, explainability, and organizer control plane for Proof of Talk 2026.",
    version="0.4.0",
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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _active_profiles_path() -> Path:
    return INGESTED_DATA_PATH if INGESTED_DATA_PATH.exists() else DATA_PATH


def _read_raw_profiles() -> List[Dict[str, Any]]:
    path = _active_profiles_path()
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, list):
        raise ValueError("profiles source must be a JSON array")
    return loaded


def _persist_runtime_profiles(profiles: List[Dict[str, Any]]) -> None:
    INGESTED_DATA_PATH.write_text(json.dumps(profiles, indent=2), encoding="utf-8")


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
        _persist_runtime_profiles(merged)
        return len(merged)

    _persist_runtime_profiles(profiles)
    return len(profiles)


def _upsert_runtime_profile(profile: Dict[str, Any]) -> None:
    _validate_profile_minimum(profile)
    current = _read_raw_profiles()
    by_id = {str(x.get("id")): x for x in current if isinstance(x, dict) and x.get("id")}
    by_id[str(profile["id"])] = profile
    merged = list(by_id.values())
    _persist_runtime_profiles(merged)


def _sanitize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    safe = dict(user)
    safe.pop("password_hash", None)
    return safe


def _normalize_role(role: str) -> str:
    value = role.lower().strip()
    return value if value in ROLE_CHOICES else "attendee"


def _profile_from_user_input(profile_id: str, payload: ProfileUpdateRequest | RegisterRequest) -> Dict[str, Any]:
    return {
        "id": profile_id,
        "name": payload.full_name,
        "title": payload.title,
        "organization": payload.organization,
        "focus": payload.focus,
        "looking_for": payload.looking_for,
        "bio": payload.bio,
        "website": payload.website,
        "social_links": payload.social_links,
        "attendee_type": _normalize_role(payload.role),
    }


def load_profiles() -> List[Dict[str, Any]]:
    return [enrich_profile(p) for p in _read_raw_profiles()]


def _raw_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    for profile in _read_raw_profiles():
        if str(profile.get("id", "")) == profile_id:
            return profile
    return None


def _profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    for profile in load_profiles():
        if str(profile.get("id", "")) == profile_id:
            return profile
    return None


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


def _authenticated_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    try:
        token = bearer_token(authorization)
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user = get_user_by_id(str(payload.get("sub", "")))
    if not user:
        raise HTTPException(status_code=401, detail="user not found")
    return user


def _optional_user(authorization: Optional[str] = Header(default=None)) -> Optional[Dict[str, Any]]:
    if not authorization:
        return None
    try:
        token = bearer_token(authorization)
        payload = decode_access_token(token)
        return get_user_by_id(str(payload.get("sub", "")))
    except ValueError:
        return None


def _is_admin_role(role: str) -> bool:
    return role in {"vip", "sponsor", "admin"}


def _admin_user(user: Dict[str, Any] = Depends(_authenticated_user)) -> Dict[str, Any]:
    role = str(user.get("role", "attendee")).lower().strip()
    if not _is_admin_role(role):
        raise HTTPException(status_code=403, detail="admin role required")
    return user


def _allowed_chat_peer_ids(user: Dict[str, Any], profiles_list: List[Dict[str, Any]]) -> set[str]:
    users = list_users()
    profile_to_user = {u["profile_id"]: u["id"] for u in users}
    current_profile_id = user.get("profile_id", "")
    if not current_profile_id:
        return set()

    per_profile = generate_all_matches(profiles_list)
    current_targets = {m["target_id"] for m in per_profile.get(current_profile_id, [])[:4]}

    allowed: set[str] = set()
    for profile_id, user_id in profile_to_user.items():
        if user_id == user["id"]:
            continue
        reverse_targets = {m["target_id"] for m in per_profile.get(profile_id, [])[:4]}
        if profile_id in current_targets or current_profile_id in reverse_targets:
            allowed.add(user_id)
    return allowed


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "db_backend": backend_summary()["backend"]}


@app.post("/api/auth/register")
def register(payload: RegisterRequest) -> Dict[str, Any]:
    email = payload.email.strip().lower()
    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="email already registered")

    role = _normalize_role(payload.role)
    user_id = f"u_{uuid.uuid4().hex[:12]}"
    profile_id = f"p_{uuid.uuid4().hex[:12]}"
    created_at = _utc_now()

    try:
        create_user(
            user_id=user_id,
            email=email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            title=payload.title,
            organization=payload.organization,
            role=role,
            profile_id=profile_id,
            created_at=created_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"user creation failed: {type(exc).__name__}") from exc

    _upsert_runtime_profile(_profile_from_user_input(profile_id, payload))
    token = create_access_token(user_id=user_id, email=email, role=role)
    user = get_user_by_id(user_id)
    return {"status": "ok", "token": token, "user": _sanitize_user(user or {})}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> Dict[str, Any]:
    email = payload.email.strip().lower()
    user = get_user_by_email(email)
    if not user or not verify_password(payload.password, str(user.get("password_hash", ""))):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = create_access_token(user_id=user["id"], email=user["email"], role=user["role"])
    return {"status": "ok", "token": token, "user": _sanitize_user(user)}


@app.get("/api/auth/me")
def me(user: Dict[str, Any] = Depends(_authenticated_user)) -> Dict[str, Any]:
    return {"user": _sanitize_user(user)}


@app.put("/api/profile/me")
def update_my_profile(payload: ProfileUpdateRequest, user: Dict[str, Any] = Depends(_authenticated_user)) -> Dict[str, Any]:
    role = _normalize_role(payload.role)
    update_user_profile_fields(
        user_id=user["id"],
        full_name=payload.full_name,
        title=payload.title,
        organization=payload.organization,
        role=role,
    )
    profile_id = str(user.get("profile_id", ""))
    _upsert_runtime_profile(_profile_from_user_input(profile_id, payload))
    updated_user = get_user_by_id(user["id"])
    return {"status": "ok", "user": _sanitize_user(updated_user or user)}


@app.get("/api/profiles")
def profiles() -> Dict[str, Any]:
    path = _active_profiles_path()
    return {"profiles": load_profiles(), "source": str(path.name)}


@app.get("/api/attendees")
def attendees(
    search: str = Query(default=""),
    role: Optional[str] = Query(default=None),
    roles: Optional[str] = Query(default=None, description="Comma-separated role filters."),
) -> Dict[str, Any]:
    role_filter = role.lower().strip() if role else None
    multi_filters = {r.strip().lower() for r in (roles or "").split(",") if r.strip()}
    if role_filter:
        multi_filters.add(role_filter)
    users_by_profile = {u["profile_id"]: u for u in list_users()}
    output: List[Dict[str, Any]] = []
    query = search.lower().strip()

    for profile in load_profiles():
        user_row = users_by_profile.get(profile.get("id", ""))
        attendee_role = (
            _normalize_role(str(user_row.get("role", "")))
            if user_row
            else _normalize_role(str(profile.get("attendee_type", "attendee")))
        )
        row = {
            "profile_id": profile.get("id", ""),
            "name": profile.get("name", ""),
            "title": profile.get("title", ""),
            "organization": profile.get("organization", ""),
            "role": attendee_role,
            "bio": profile.get("bio", ""),
            "website": profile.get("website", ""),
            "social_links": profile.get("social_links", {}),
            "registered_user_id": user_row.get("id") if user_row else "",
            "enrichment": profile.get("enrichment", {}),
        }
        haystack = " ".join([row["name"], row["title"], row["organization"]]).lower()
        if query and query not in haystack:
            continue
        if multi_filters and attendee_role not in multi_filters:
            continue
        output.append(row)

    output.sort(key=lambda r: r["name"])
    return {"attendees": output, "count": len(output)}


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
    now = _utc_now()
    upsert_action(payload.from_id, payload.to_id, payload.status, payload.notes, now)
    return {"status": "ok", "updated_at": now}


@app.post("/api/admin/actions")
def save_action_admin(payload: ActionUpsert, _admin: Dict[str, Any] = Depends(_admin_user)) -> Dict[str, str]:
    now = _utc_now()
    upsert_action(payload.from_id, payload.to_id, payload.status, payload.notes, now)
    return {"status": "ok", "updated_at": now, "admin": _admin.get("email", "")}


@app.get("/api/chat/peers")
def chat_peers(user: Dict[str, Any] = Depends(_authenticated_user)) -> Dict[str, Any]:
    profiles_list = load_profiles()
    allowed = _allowed_chat_peer_ids(user, profiles_list)
    all_users = list_users()
    users_by_id = {u["id"]: u for u in all_users}
    recent = get_recent_chat_activity_for_user(user["id"])

    latest_by_peer: Dict[str, Dict[str, Any]] = {}
    for msg in recent:
        peer_id = msg["to_user_id"] if msg["from_user_id"] == user["id"] else msg["from_user_id"]
        if peer_id not in latest_by_peer:
            latest_by_peer[peer_id] = msg

    peers: List[Dict[str, Any]] = []
    for peer_id in allowed:
        peer = users_by_id.get(peer_id)
        if not peer:
            continue
        latest = latest_by_peer.get(peer_id)
        peers.append(
            {
                "user_id": peer_id,
                "full_name": peer.get("full_name", ""),
                "title": peer.get("title", ""),
                "organization": peer.get("organization", ""),
                "role": peer.get("role", "attendee"),
                "profile_id": peer.get("profile_id", ""),
                "latest_message": latest.get("body", "") if latest else "",
                "latest_at": latest.get("created_at", "") if latest else "",
            }
        )

    peers.sort(key=lambda p: p.get("latest_at", ""), reverse=True)
    return {"peers": peers}


@app.get("/api/chat/messages/{peer_user_id}")
def chat_messages(peer_user_id: str, user: Dict[str, Any] = Depends(_authenticated_user)) -> Dict[str, Any]:
    profiles_list = load_profiles()
    allowed = _allowed_chat_peer_ids(user, profiles_list)
    if peer_user_id not in allowed:
        raise HTTPException(status_code=403, detail="chat is allowed only for matched peers")
    return {"messages": get_chat_messages_between(user["id"], peer_user_id)}


@app.post("/api/chat/messages")
def send_chat_message(payload: ChatMessageCreate, user: Dict[str, Any] = Depends(_authenticated_user)) -> Dict[str, Any]:
    profiles_list = load_profiles()
    allowed = _allowed_chat_peer_ids(user, profiles_list)
    if payload.to_user_id not in allowed:
        raise HTTPException(status_code=403, detail="chat is allowed only for matched peers")
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="message body cannot be empty")
    message = insert_chat_message(user["id"], payload.to_user_id, body, _utc_now())
    return {"status": "ok", "message": message}


@app.post("/api/concierge/chat")
def concierge_chat(payload: ConciergeChatRequest, user: Optional[Dict[str, Any]] = Depends(_optional_user)) -> Dict[str, Any]:
    dashboard_data = dashboard()
    profile = _profile_by_id(payload.profile_id) if payload.profile_id else None
    actor = _sanitize_user(user) if user else {}
    response = concierge_reply(
        message=payload.message,
        profile=profile,
        dashboard=dashboard_data,
        history=payload.history,
    )
    return {
        "status": "ok",
        "assistant": response.get("reply", ""),
        "mode": response.get("mode", "fallback"),
        "history_used": response.get("history_used", len(payload.history)),
        "actor": actor,
    }


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


@app.get("/api/dashboard/drilldown")
def dashboard_drilldown(from_id: str = Query(min_length=1), to_id: str = Query(min_length=1)) -> Dict[str, Any]:
    profiles_list = load_profiles()
    per_profile = with_actions(generate_all_matches(profiles_list))
    rows = per_profile.get(from_id, [])
    match_row = next((r for r in rows if r.get("target_id") == to_id), None)
    if not match_row:
        raise HTTPException(status_code=404, detail="match pair not found")
    source = next((p for p in profiles_list if p.get("id") == from_id), None)
    target = next((p for p in profiles_list if p.get("id") == to_id), None)
    return {
        "from_profile": source or {},
        "to_profile": target or {},
        "match": match_row,
        "related_non_obvious": [
            x for x in top_non_obvious_pairs(profiles_list, limit=10) if {x.get("from_id"), x.get("to_id")} == {from_id, to_id}
        ],
    }


@app.get("/api/dashboard/segments")
def dashboard_segments() -> Dict[str, Any]:
    profiles_list = load_profiles()
    users_by_profile = {u["profile_id"]: u for u in list_users()}
    role_counts: Dict[str, int] = {r: 0 for r in sorted(ROLE_CHOICES)}
    tag_counts: Dict[str, int] = {}

    for p in profiles_list:
        role = _normalize_role(str((users_by_profile.get(p.get("id", ""), {}) or {}).get("role", p.get("attendee_type", "attendee"))))
        role_counts[role] = role_counts.get(role, 0) + 1
        for tag in p.get("enrichment", {}).get("inferred_tags", [])[:8]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:12]
    return {
        "roles": role_counts,
        "top_interest_tags": [{"tag": t, "count": c} for t, c in top_tags],
    }


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
        for match in rows:
            level = match.get("risk_level", "medium")
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


@app.get("/api/enrichment")
def enrichment_overview() -> Dict[str, Any]:
    profiles_list = load_profiles()
    rows = []
    for profile in profiles_list:
        enrich = profile.get("enrichment", {})
        rows.append(
            {
                "profile_id": profile.get("id", ""),
                "name": profile.get("name", ""),
                "source_confidence": enrich.get("source_confidence", 0),
                "inferred_tags": enrich.get("inferred_tags", []),
                "sources": enrich.get("sources", []),
                "live_connector_errors": enrich.get("live_connector_errors", []),
                "live_connector_results": enrich.get("live_connector_results", []),
            }
        )
    return {"enrichment": rows}


@app.post("/api/enrichment/refresh")
def enrichment_refresh(payload: EnrichmentRefreshRequest) -> Dict[str, Any]:
    if payload.profile_id:
        raw = _raw_profile_by_id(payload.profile_id)
        if not raw:
            raise HTTPException(status_code=404, detail="profile not found")
        enriched = enrich_profile(raw, live_enabled=payload.live_enabled, connectors_override=payload.connectors or None)
        return {"status": "ok", "profile": enriched, "connectors": payload.connectors}

    enriched_all = [
        enrich_profile(raw, live_enabled=payload.live_enabled, connectors_override=payload.connectors or None)
        for raw in _read_raw_profiles()
    ]
    return {"status": "ok", "profiles": enriched_all, "count": len(enriched_all), "connectors": payload.connectors}


@app.get("/api/enrichment/{profile_id}")
def enrichment_detail(profile_id: str) -> Dict[str, Any]:
    profile = _profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="profile not found")
    return {
        "profile_id": profile_id,
        "name": profile.get("name", ""),
        "enrichment": profile.get("enrichment", {}),
        "social_links": profile.get("social_links", {}),
    }


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(STATIC_DIR / "index.html")
