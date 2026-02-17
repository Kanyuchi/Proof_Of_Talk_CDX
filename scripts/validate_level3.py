from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATCHES_PATH = ROOT / "data" / "match_results.json"


def main() -> None:
    payload = json.loads(MATCHES_PATH.read_text(encoding="utf-8"))
    matches = payload.get("matches", {})
    assert matches, "missing matches"

    for pid, rows in matches.items():
        assert rows, f"no rows for {pid}"
        for row in rows:
            assert "risk_level" in row, f"missing risk_level for {pid}"
            assert row["risk_level"] in {"low", "medium", "high"}, f"invalid risk level for {pid}"
            assert "risk_reasons" in row, f"missing risk_reasons for {pid}"

    non_obvious = payload.get("top_non_obvious_pairs", [])
    assert non_obvious, "missing top_non_obvious_pairs"
    for row in non_obvious:
        assert "novelty_score" in row, "non-obvious row missing novelty_score"
        assert row["novelty_score"] >= 0.0, "novelty_score must be non-negative"

    print("Level 3 validation passed")


if __name__ == "__main__":
    main()
