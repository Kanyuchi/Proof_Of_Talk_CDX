from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.enrichment import enrich_profile
from app.matching import generate_all_matches, top_intro_pairs

DATA_PATH = ROOT / "data" / "test_profiles.json"
STATIC_DIR = ROOT / "app" / "static"


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

    def _load_profiles(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
        return [enrich_profile(p) for p in profiles]

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ["/", "/index.html"]:
            index = STATIC_DIR / "index.html"
            if not index.exists():
                self._text("index.html not found", status=404)
                return
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

        if parsed.path == "/health":
            self._json({"status": "ok"})
            return

        if parsed.path == "/api/profiles":
            profiles = self._load_profiles()
            self._json({"profiles": profiles})
            return

        if parsed.path == "/api/matches":
            profiles = self._load_profiles()
            match_map = generate_all_matches(profiles)

            profile_id = parse_qs(parsed.query).get("profile_id", [None])[0]
            if profile_id:
                if profile_id not in match_map:
                    self._json({"error": "profile not found"}, status=404)
                    return
                self._json({"profile_id": profile_id, "matches": match_map[profile_id]})
                return

            self._json({"matches": match_map})
            return

        if parsed.path == "/api/dashboard":
            profiles = self._load_profiles()
            global_intros = top_intro_pairs(profiles, limit=10)
            per_profile = generate_all_matches(profiles)
            self._json(
                {
                    "overview": {
                        "attendee_count": len(profiles),
                        "recommended_intro_count": len(global_intros),
                    },
                    "top_intro_pairs": global_intros,
                    "per_profile": per_profile,
                }
            )
            return

        self._text("Not found", status=404)


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    server = HTTPServer((host, port), MatchmakingHandler)
    print(f"Server running at http://{host}:{port}")
    server.serve_forever()
