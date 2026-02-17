# AGENTS.md

## Project
Proof of Talk 2026 AI Matchmaking Engine (XVentures Labs case study).

## Objective
Build a Level 3-ready product concept and implementation plan for an AI-powered matchmaking engine that helps 2,500 high-value decision-makers discover and prioritize the most transactable meetings before and during the event.

## Success Criteria
- Deliver Level 1 artifacts: product vision, architecture, data strategy, matching logic, business model, and prioritized recommendations for 5 test profiles.
- Deliver Level 2 artifacts: wireframes + runnable matching script/notebook.
- Deliver Level 3 artifacts: clickable prototype or working web app with:
  - data enrichment pipeline (web/company/social/professional where feasible)
  - AI matching + explanation engine
  - organizer dashboard
- Demonstrate non-obvious, high-value matches and clear reasoning.

## Core Product Principles
- Decision-maker quality over volume.
- Complementary intelligence over keyword matching.
- Explainable recommendations (every match has a reason).
- Deal-readiness scoring (prioritize likely-to-transact pairs).
- Premium UX consistent with a high-ticket executive event.

## Suggested MVP Scope (Level 3 pass)
- Attendee profile ingestion:
  - registration fields
  - structured profile objects for enrichment
- Enrichment pipeline:
  - company website parsing
  - public profile/company/funding signals (mock/fallback datasets allowed if API limits block live data)
- Matching engine:
  - thesis alignment score
  - strategic complementarity score
  - readiness score
  - final weighted ranking
- Explainability:
  - short natural-language rationale per match
- Organizer dashboard:
  - top recommended intros
  - confidence/risk indicators
  - manual override + notes

## Technical Direction
- Backend: Python + FastAPI (or Node + Express if team chooses JS-first).
- AI layer: LLM-assisted profile normalization and explanation generation.
- Ranking: deterministic weighted scoring + LLM reasoning layer.
- Storage: SQLite/Postgres for attendee profiles, matches, explanations.
- Frontend: lightweight web app (React/Next.js preferred) with attendee and organizer views.

## Build Plan
1. Define schema and scoring rubric.
2. Implement baseline rule-based matching.
3. Add LLM-generated explanations.
4. Add enrichment connectors/mocks.
5. Build dashboard and meeting-priority list.
6. Validate on the 5 provided profiles.
7. Package submission assets (PDF + repo + demo link).

## Required Outputs
- `/README.md` with execution plan and setup.
- `/docs/case-study-response.md` containing Level 1-3 narrative.
- `/data/test_profiles.json` with provided 5 personas.
- `/notebooks` or `/scripts` for match generation demo.
- `/app` or `/web` for clickable prototype.

## Evaluation Lens
Optimize for:
- founder-level thinking
- shipping velocity
- quality of recommendations
- clarity of business case
- practical path to monetization and scale

## Constraints
- Deadline: Sunday EOD (this week, per brief).
- Submission to: z@xventures.de.
- Prefer working software over perfect documentation.

## Non-Goals (for first pass)
- enterprise-perfect data coverage
- fully autonomous scheduling flows
- polished production infra beyond demo reliability

## Working Agreement
- Keep commits small and demonstrable.
- Document assumptions and blocked items explicitly.
- If a live data source is blocked, use realistic mocks and state the gap.
