# Proof of Talk 2026 - AI Matchmaking Engine

AI matchmaking prototype for the XVentures Labs Internal Entrepreneur case study.

## Case Study Goal
Build a premium matchmaking product for Proof of Talk 2026 that:
- identifies high-value intros for 2,500 attendees
- prioritizes deal-ready meetings
- explains why each recommendation matters
- gives organizers control and visibility

## Current Implementation
- `app/server.py`: local API + static dashboard server
- `app/matching.py`: weighted matching logic (fit, complementarity, readiness)
- `app/enrichment.py`: mock enrichment layer for profile signal expansion
- `app/static/*`: organizer dashboard (overview, top intro pairs, per-profile matches)
- `scripts/generate_matches.py`: offline match generation
- `data/test_profiles.json`: 5 required case-study personas
- `data/match_results.json`: generated ranked matches

## How To Run
1. Generate match output:
```bash
python3 scripts/generate_matches.py
```
2. Start dashboard server:
```bash
python3 app/server.py
```
3. Open:
`http://127.0.0.1:8000`

## API Endpoints
- `GET /health`
- `GET /api/profiles`
- `GET /api/matches`
- `GET /api/matches?profile_id=p1`
- `GET /api/dashboard`

## Level Mapping
- Level 1: strategy docs in `docs/case-study-response.md` (to be completed with final business narrative)
- Level 2: working recommendation script + initial UI
- Level 3 (starter complete): clickable dashboard + enrichment + ranking + rationale generation

## Next Build Steps Toward Stronger Level 3
1. Replace mock enrichment with live connectors/APIs where available.
2. Add LLM-generated rationales and quality guardrails.
3. Add organizer actions: approve/reject intros, notes, scheduling intent.
4. Add auth + persistence for multiple events and attendee cohorts.
