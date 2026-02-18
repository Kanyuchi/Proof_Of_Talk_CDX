from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.db import action_map, backend_summary, get_all_actions, init_db, upsert_action
from app.enrichment import enrich_profile
from app.matching import generate_all_matches, top_intro_pairs, top_non_obvious_pairs

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "test_profiles.json"
INGESTED_DATA_PATH = ROOT / "data" / "runtime_profiles.json"
STATIC_DIR = ROOT / "app" / "static"


def _active_profiles_path() -> Path:
    return INGESTED_DATA_PATH if INGESTED_DATA_PATH.exists() else DATA_PATH


def _read_raw_profiles():
    with open(_active_profiles_path(), "r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, list):
        raise ValueError("profiles source must be a JSON array")
    return loaded


def _load_profiles():
    return [enrich_profile(p) for p in _read_raw_profiles()]


def _validate_profile_minimum(profile):
    if not profile.get("id"):
        raise ValueError("profile missing id")
    if not profile.get("name"):
        raise ValueError("profile missing name")


def _write_profiles(profiles, overwrite=True):
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


def _merge_actions(per_profile):
    actions = action_map()
    merged = {}
    for source_id, matches in per_profile.items():
        rows = []
        for match in matches:
            key = f"{source_id}::{match['target_id']}"
            copy = dict(match)
            copy["action"] = actions.get(
                key,
                {
                    "from_id": source_id,
                    "to_id": match["target_id"],
                    "status": "pending",
                    "notes": "",
                    "updated_at": "",
                },
            )
            rows.append(copy)
        merged[source_id] = rows
    return merged


class MatchmakingHandler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, data, content_type="text/plain", status=200):
        body = data.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/", "/index.html"]:
            index = STATIC_DIR / "index.html"
            self._text(index.read_text(encoding="utf-8"), content_type="text/html")
            return
        if parsed.path == "/favicon.ico":
            self._text("", status=204)
            return
        if parsed.path.startswith("/static/"):
            file_name = parsed.path.replace("/static/", "", 1)
            file_path = STATIC_DIR / file_name
            if not file_path.exists():
                self._text("Not found", status=404)
                return
            content_type = "text/plain"
            if file_name.endswith(".css"):
                content_type = "text/css"
            elif file_name.endswith(".js"):
                content_type = "application/javascript"
            self._text(file_path.read_text(encoding="utf-8"), content_type=content_type)
            return
        if parsed.path == "/docs":
            self._text(
                "FastAPI docs unavailable in fallback mode. Install requirements and run with uvicorn.",
                status=503,
            )
            return
        if parsed.path == "/health":
            self._json({"status": "ok", "mode": "fallback", "db_backend": backend_summary()["backend"]})
            return
        if parsed.path == "/api/profiles":
            self._json({"profiles": _load_profiles(), "source": _active_profiles_path().name})
            return
        if parsed.path == "/api/actions":
            self._json({"actions": get_all_actions()})
            return
        if parsed.path == "/api/matches":
            profiles = _load_profiles()
            per_profile = _merge_actions(generate_all_matches(profiles))
            profile_id = parse_qs(parsed.query).get("profile_id", [None])[0]
            if profile_id:
                if profile_id not in per_profile:
                    self._json({"error": "profile not found"}, status=404)
                    return
                self._json({"profile_id": profile_id, "matches": per_profile[profile_id]})
                return
            self._json({"matches": per_profile})
            return
        if parsed.path == "/api/non-obvious-matches":
            profiles = _load_profiles()
            limit = int(parse_qs(parsed.query).get("limit", [5])[0])
            pairs = top_non_obvious_pairs(profiles, limit=max(1, min(limit, 20)))
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
            self._json({"non_obvious_pairs": pairs})
            return
        if parsed.path == "/api/dashboard":
            profiles = _load_profiles()
            pairs = top_intro_pairs(profiles, limit=10)
            non_obvious = top_non_obvious_pairs(profiles, limit=5)
            per_profile = _merge_actions(generate_all_matches(profiles))
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

            self._json(
                {
                    "overview": {
                        "attendee_count": len(profiles),
                        "recommended_intro_count": len(pairs),
                        "actioned_intro_count": len(get_all_actions()),
                        "risk_distribution": risk_counts,
                    },
                    "top_intro_pairs": pairs,
                    "top_non_obvious_pairs": non_obvious,
                    "per_profile": per_profile,
                }
            )
            return
        if not parsed.path.startswith("/api/"):
            index = STATIC_DIR / "index.html"
            self._text(index.read_text(encoding="utf-8"), content_type="text/html")
            return
        self._text("Not found", status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(content_len).decode("utf-8")) if content_len else {}

        if parsed.path == "/api/actions":
            status = payload.get("status", "pending")
            if status not in {"pending", "approved", "rejected"}:
                self._json({"error": "invalid status"}, status=400)
                return
            now = datetime.now(timezone.utc).isoformat()
            upsert_action(
                payload.get("from_id", ""),
                payload.get("to_id", ""),
                status,
                payload.get("notes", ""),
                now,
            )
            self._json({"status": "ok", "updated_at": now})
            return

        if parsed.path == "/api/profiles/ingest":
            profiles = payload.get("profiles", [])
            overwrite = bool(payload.get("overwrite", True))
            if not isinstance(profiles, list):
                self._json({"error": "profiles must be a list"}, status=400)
                return
            try:
                count = _write_profiles(profiles, overwrite=overwrite)
            except ValueError as exc:
                self._json({"error": str(exc)}, status=400)
                return
            self._json(
                {
                    "status": "ok",
                    "stored_profiles": count,
                    "source": INGESTED_DATA_PATH.name,
                    "overwrite": overwrite,
                }
            )
            return

        if parsed.path == "/api/profiles/reset":
            if INGESTED_DATA_PATH.exists():
                INGESTED_DATA_PATH.unlink()
            self._json({"status": "ok", "source": DATA_PATH.name})
            return

        self._text("Not found", status=404)


def run(host: str, port: int) -> None:
    init_db()
    server = HTTPServer((host, port), MatchmakingHandler)
    print(f"Fallback server running at http://{host}:{port}")
    server.serve_forever()
