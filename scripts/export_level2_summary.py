from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATCHES_PATH = ROOT / "data" / "match_results.json"
CSV_OUT_PATH = ROOT / "data" / "level2_summary.csv"
MD_OUT_PATH = ROOT / "data" / "level2_summary.md"


def main() -> None:
    payload = json.loads(MATCHES_PATH.read_text(encoding="utf-8"))
    matches = payload["matches"]

    rows = []
    for profile_id, ranked in matches.items():
        for item in ranked[:3]:
            rows.append(
                {
                    "profile_id": profile_id,
                    "priority_rank": item["priority_rank"],
                    "target_name": item["target_name"],
                    "score": item["score"],
                    "confidence": item["confidence"],
                    "rationale": item["rationale"],
                }
            )

    with open(CSV_OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "profile_id",
                "priority_rank",
                "target_name",
                "score",
                "confidence",
                "rationale",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    lines = ["# Level 2 Summary", "", "| Profile | Rank | Match | Score | Confidence | Why |", "|---|---:|---|---:|---:|---|"]
    for r in rows:
        lines.append(
            f"| {r['profile_id']} | {r['priority_rank']} | {r['target_name']} | {r['score']} | {r['confidence']} | {r['rationale']} |"
        )
    MD_OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {CSV_OUT_PATH}")
    print(f"Wrote {MD_OUT_PATH}")


if __name__ == "__main__":
    main()
