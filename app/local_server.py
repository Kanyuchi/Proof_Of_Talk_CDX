from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.db import action_map, get_all_actions, init_db, upsert_action
from app.enrichment import enrich_profile
from app.matching import generate_all_matches, top_intro_pairs

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "test_profiles.json"
STATIC_DIR = ROOT / "app" / "static"


def _load_profiles():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    return [enrich_profile(p) for p in profiles]


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
            self._json({"status": "ok", "mode": "fallback"})
            return
        if parsed.path == "/api/profiles":
            self._json({"profiles": _load_profiles()})
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
        if parsed.path == "/api/dashboard":
            profiles = _load_profiles()
            pairs = top_intro_pairs(profiles, limit=10)
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
            self._json(
                {
                    "overview": {
                        "attendee_count": len(profiles),
                        "recommended_intro_count": len(pairs),
                        "actioned_intro_count": len(get_all_actions()),
                    },
                    "top_intro_pairs": pairs,
                    "per_profile": per_profile,
                }
            )
            return
        self._text("Not found", status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/actions":
            self._text("Not found", status=404)
            return
        content_len = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(content_len).decode("utf-8"))
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


def run(host: str, port: int) -> None:
    init_db()
    server = HTTPServer((host, port), MatchmakingHandler)
    print(f"Fallback server running at http://{host}:{port}")
    server.serve_forever()
