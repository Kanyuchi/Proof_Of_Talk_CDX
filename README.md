# Proof of Talk 2026 - AI Matchmaking Engine

AI matchmaking prototype for the XVentures Labs Internal Entrepreneur case study.

## Case Study Goal
Build a premium matchmaking product for Proof of Talk 2026 that:
- identifies high-value intros for 2,500 attendees
- prioritizes deal-ready meetings
- explains why each recommendation matters
- gives organizers control and visibility

## Current Implementation
- `app/main.py`: FastAPI backend with interactive docs (`/docs`)
- `app/server.py`: compatibility launcher for FastAPI (`python3 app/server.py`)
- `app/matching.py`: weighted matching logic (fit, complementarity, readiness)
- `app/enrichment.py`: mock enrichment layer for profile signal expansion
- `app/db.py`: SQLite persistence for organizer actions and notes
- `app/static/*`: organizer dashboard (overview, top intro pairs, per-profile matches)
- `scripts/generate_matches.py`: offline match generation
- `data/test_profiles.json`: 5 required case-study personas
- `data/match_results.json`: generated ranked matches

## How To Run
1. Install dependencies:
```bash
pip install -r requirements.txt
```
If pip install is blocked in your environment, `python3 app/server.py` falls back to a stdlib server without `/docs`.
2. Generate match output:
```bash
python3 scripts/generate_matches.py
```
3. Start API + dashboard:
```bash
python3 app/server.py
```
or
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
4. Open:
`http://127.0.0.1:8000`
FastAPI docs (when dependencies are installed): `http://127.0.0.1:8000/docs`

## API Endpoints
- `GET /health`
- `GET /api/profiles`
- `GET /api/matches`
- `GET /api/matches?profile_id=p1`
- `GET /api/dashboard`
- `GET /api/actions`
- `POST /api/actions`
- `GET /docs` (FastAPI interactive docs)

## Level Mapping
- Level 1: strategy docs in `docs/case-study-response.md` (to be completed with final business narrative)
- Level 2: working recommendation script + initial UI
- Level 3 (starter complete): clickable dashboard + enrichment + ranking + rationale generation

## Organizer Action Payload
```json
{
  "from_id": "p1",
  "to_id": "p2",
  "status": "approved",
  "notes": "Strong RWA custody alignment; prioritize for Day 1."
}
```

## Optional Runtime Flags
- `ENABLE_LIVE_ENRICHMENT=1`: run live connectors (company website + structured funding signals) with graceful fallback on fetch failures.
- `ENABLE_LLM_RATIONALE=1`: enable LLM-generated explanations.
- `OPENAI_API_KEY=<key>`: required when `ENABLE_LLM_RATIONALE=1`.
- `OPENAI_MODEL=gpt-4.1-mini`: optional LLM model override.

## Next Build Steps
1. Replace mock enrichment with live connectors/APIs where available.
2. Add LLM-generated rationales with fallback templates.
3. Add scheduling workflow and CRM/event tool exports.
4. Add auth and multi-event dataset support.
