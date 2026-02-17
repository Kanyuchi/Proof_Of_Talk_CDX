from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATCHES_PATH = ROOT / "data" / "match_results.json"


def main() -> None:
    payload = json.loads(MATCHES_PATH.read_text(encoding="utf-8"))
    matches = payload.get("matches", {})

    assert len(matches) == 5, f"Expected 5 profiles, got {len(matches)}"
    for pid, ranked in matches.items():
        assert len(ranked) >= 3, f"Profile {pid} has fewer than 3 ranked matches"
        scores = [float(x["score"]) for x in ranked]
        assert scores == sorted(scores, reverse=True), f"Scores not sorted for {pid}"
        for row in ranked:
            assert row.get("rationale"), f"Missing rationale for {pid}->{row.get('target_id')}"

    pairs = payload.get("top_intro_pairs", [])
    assert len(pairs) == 10, f"Expected 10 top intro pairs, got {len(pairs)}"

    print("Level 2 validation passed")


if __name__ == "__main__":
    main()
