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
- `app/auth.py`: custom JWT auth + password hashing (Option 1 implementation)
- `app/matching.py`: weighted matching logic + risk indicators + non-obvious match detection
- `app/enrichment.py`: mock enrichment layer for profile signal expansion
- `app/db.py`: multi-database persistence layer (`SQLite`, `PostgreSQL`, `MySQL`) via `DATABASE_URL`
- `app/static/*`: multi-view UX (Home, Attendees, Dashboard, Chat, Auth/Profile)
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
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `PUT /api/profile/me`
- `GET /api/attendees`
- `GET /api/profiles`
- `POST /api/profiles/ingest`
- `POST /api/profiles/reset`
- `GET /api/matches`
- `GET /api/matches?profile_id=p1`
- `GET /api/non-obvious-matches`
- `GET /api/dashboard`
- `GET /api/actions`
- `POST /api/actions`
- `GET /api/chat/peers` (auth required)
- `GET /api/chat/messages/{peer_user_id}` (auth required + matched peers only)
- `POST /api/chat/messages` (auth required + matched peers only)
- `GET /docs` (FastAPI interactive docs)

## Level Mapping
- Level 1: strategy narrative complete in `docs/case-study-response.md`
- Level 2: wireframes + runnable script/notebook + deterministic outputs complete in `docs/level2/*` and `notebooks/matching_demo.ipynb`
- Level 3: clickable dashboard + enrichment connectors + explainable ranking + ingestion API + organizer control plane

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
- `DATABASE_URL=<url>`: database connection string.
  - Local default: `sqlite:///data/matchmaking.db`
  - PostgreSQL example: `postgresql://user:pass@host:5432/matchmaking?sslmode=require`
  - MySQL example: `mysql://user:pass@host:3306/matchmaking?ssl=true`
- `ENABLE_LIVE_ENRICHMENT=1`: run live connectors (company website + structured funding signals) with graceful fallback on fetch failures.
- `LIVE_CONNECTORS=website,structured_funding,clearbit,crunchbase,openalex`: choose which connectors run when live enrichment is enabled.
- `CLEARBIT_API_KEY=<key>`: enables Clearbit company signal connector.
- `CLEARBIT_COMPANY_URL=<url_template>`: optional override (must include `{domain}`).
- `CRUNCHBASE_API_KEY=<key>`: enables Crunchbase organization signal connector.
- `CRUNCHBASE_BASE_URL=<base_url>`: optional Crunchbase API base URL override.
- `ENABLE_LLM_RATIONALE=1`: enable LLM-generated explanations.
- `OPENAI_API_KEY=<key>`: required when `ENABLE_LLM_RATIONALE=1`.
- `OPENAI_MODEL=gpt-4.1-mini`: optional LLM model override.
- `APP_JWT_SECRET=<strong-random-secret>`: signing key for custom JWT auth tokens.

## Auth Flow (Option 1)
1. Register in UI (`/auth`) or via `POST /api/auth/register`.
2. Sign in with `POST /api/auth/login`.
3. Token is used as `Authorization: Bearer <token>`.
4. Private chat is enabled only for matched attendee pairs.

## Testing
```bash
python3 -m unittest discover -s tests -v
```

## AWS RDS Setup (Level 3)
Recommended: PostgreSQL on RDS.

1. Create an RDS instance (PostgreSQL or MySQL) and allow inbound access from your app host/security group.
2. Create database and user (example: `matchmaking`).
3. Set environment variable before starting app:
```bash
export DATABASE_URL="postgresql://USER:PASSWORD@RDS_ENDPOINT:5432/matchmaking?sslmode=require"
```
or
```bash
export DATABASE_URL="mysql://USER:PASSWORD@RDS_ENDPOINT:3306/matchmaking?ssl=true"
```
4. Validate connection and schema bootstrap:
```bash
python3 scripts/check_db_connection.py
```
5. Start app:
```bash
python3 app/server.py
```

## Level 3 Runbook
```bash
python3 scripts/generate_matches.py
python3 scripts/validate_level3.py
python3 app/server.py
```

Optional ingestion example:
```bash
curl -X POST http://127.0.0.1:8000/api/profiles/ingest \\
  -H "Content-Type: application/json" \\
  -d '{"overwrite":true,"profiles":[{"id":"x1","name":"New Investor"},{"id":"x2","name":"New Builder"}]}'
```

## Level 2 Runbook
```bash
python3 scripts/generate_matches.py
python3 scripts/export_level2_summary.py
python3 scripts/validate_level2.py
```

Level 2 artifacts:
- `docs/level2/01-scope-and-user-flows.md`
- `docs/level2/02-wireframes.md`
- `docs/level2/03-data-contract-map.md`
- `docs/level2/04-completion-checklist.md`
- `notebooks/matching_demo.ipynb`
- `data/level2_summary.csv`
- `data/level2_summary.md`

## Next Build Steps
1. Add provider-specific response mappers for selected paid data vendors.
2. Add scheduling workflow and CRM/event tool exports.
3. Add auth and multi-event dataset support.
4. Add ranking calibration from intro outcome feedback.
