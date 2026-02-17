from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from app.explanations import generate_match_rationale


@dataclass
class MatchScore:
    target_id: str
    target_name: str
    score: float
    fit_score: float
    complementarity_score: float
    readiness_score: float
    confidence: float
    rationale: str


def _to_bag(profile: Dict[str, Any]) -> List[str]:
    tokens: List[str] = []
    for key in ["mandate", "product", "thesis", "focus"]:
        value = profile.get(key)
        if isinstance(value, str):
            tokens.extend(value.lower().replace("/", " ").replace("-", " ").split())
        if isinstance(value, list):
            for item in value:
                tokens.extend(str(item).lower().replace("/", " ").replace("-", " ").split())

    for item in profile.get("looking_for", []):
        tokens.extend(str(item).lower().replace("/", " ").replace("-", " ").split())

    stop_words = {
        "and",
        "or",
        "the",
        "to",
        "of",
        "for",
        "with",
        "in",
        "at",
        "a",
        "an",
        "is",
        "are",
        "into",
        "over",
        "under",
    }
    return [t.strip(",.") for t in tokens if t and t not in stop_words and len(t) > 2]


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _role_type(profile: Dict[str, Any]) -> str:
    org = profile.get("organization", "").lower()
    title = profile.get("title", "").lower()
    if "fund" in org or "ventures" in org or "partner" in title:
        return "investor"
    if "bank" in org or "bundesbank" in org or "regulator" in title:
        return "regulator"
    if "cto" in title or "ceo" in title or "co-founder" in title:
        return "builder"
    return "operator"


def _deal_readiness(profile: Dict[str, Any]) -> float:
    text = " ".join(
        [
            str(profile.get("mandate", "")),
            str(profile.get("product", "")),
            str(profile.get("thesis", "")),
            " ".join(profile.get("looking_for", [])),
        ]
    ).lower()

    score = 0.2
    if "deploy" in text or "invest" in text:
        score += 0.35
    if "series" in text or "raised" in text or "live" in text:
        score += 0.25
    if "pilot" in text or "partnership" in text or "co-invest" in text:
        score += 0.2
    return min(score, 1.0)


def _complementarity(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    ta, tb = _role_type(a), _role_type(b)
    pair = {ta, tb}
    if pair == {"investor", "builder"}:
        return 1.0
    if pair == {"regulator", "builder"}:
        return 0.9
    if pair == {"investor", "regulator"}:
        return 0.75
    if ta == tb == "builder":
        return 0.6
    if ta == tb == "investor":
        return 0.5
    return 0.45


def _rationale(a: Dict[str, Any], b: Dict[str, Any], fit: float, comp: float, ready: float) -> str:
    return generate_match_rationale(a, b, fit, comp, ready)


def rank_for_profile(source: Dict[str, Any], targets: List[Dict[str, Any]]) -> List[MatchScore]:
    source_bag = _to_bag(source)
    source_ready = _deal_readiness(source)
    results: List[MatchScore] = []

    for target in targets:
        target_bag = _to_bag(target)
        fit = _jaccard(source_bag, target_bag)
        comp = _complementarity(source, target)
        ready = (source_ready + _deal_readiness(target)) / 2

        weighted = (0.4 * fit) + (0.35 * comp) + (0.25 * ready)
        confidence = min(0.55 + (0.35 * fit) + (0.1 * ready), 0.98)

        results.append(
            MatchScore(
                target_id=target["id"],
                target_name=target["name"],
                score=round(weighted, 4),
                fit_score=round(fit, 4),
                complementarity_score=round(comp, 4),
                readiness_score=round(ready, 4),
                confidence=round(confidence, 4),
                rationale=_rationale(source, target, fit, comp, ready),
            )
        )

    return sorted(results, key=lambda x: x.score, reverse=True)


def generate_all_matches(profiles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by_profile: Dict[str, List[Dict[str, Any]]] = {}

    for profile in profiles:
        targets = [p for p in profiles if p["id"] != profile["id"]]
        ranked = rank_for_profile(profile, targets)
        by_profile[profile["id"]] = [
            {
                "target_id": r.target_id,
                "target_name": r.target_name,
                "priority_rank": idx + 1,
                "score": r.score,
                "fit_score": r.fit_score,
                "complementarity_score": r.complementarity_score,
                "readiness_score": r.readiness_score,
                "confidence": r.confidence,
                "rationale": r.rationale,
            }
            for idx, r in enumerate(ranked)
        ]

    return by_profile


def top_intro_pairs(profiles: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    pairs: List[Tuple[float, Dict[str, Any]]] = []

    for a, b in itertools.combinations(profiles, 2):
        fit = _jaccard(_to_bag(a), _to_bag(b))
        comp = _complementarity(a, b)
        ready = (_deal_readiness(a) + _deal_readiness(b)) / 2
        score = (0.4 * fit) + (0.35 * comp) + (0.25 * ready)

        pairs.append(
            (
                score,
                {
                    "from_id": a["id"],
                    "from_name": a["name"],
                    "to_id": b["id"],
                    "to_name": b["name"],
                    "score": round(score, 4),
                    "rationale": _rationale(a, b, fit, comp, ready),
                },
            )
        )

    pairs.sort(key=lambda x: x[0], reverse=True)
    return [p[1] for p in pairs[:limit]]
