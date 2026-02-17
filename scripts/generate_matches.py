from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.enrichment import enrich_profile
from app.matching import generate_all_matches, top_intro_pairs

DATA_PATH = ROOT / "data" / "test_profiles.json"
OUT_PATH = ROOT / "data" / "match_results.json"


def main() -> None:
    profiles = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    enriched = [enrich_profile(p) for p in profiles]

    out = {
        "matches": generate_all_matches(enriched),
        "top_intro_pairs": top_intro_pairs(enriched, limit=10),
    }

    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote match results to {OUT_PATH}")


if __name__ == "__main__":
    main()
