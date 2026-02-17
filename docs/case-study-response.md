# Case Study Response (Submission-Ready)

## 1. Product Vision
Proof of Talk should provide concierge-level matchmaking that behaves like an investment-banking intro desk, not a conference attendee directory. The experience begins at registration, enriches each attendee profile before arrival, and delivers prioritized intros with clear reasons and deal-readiness indicators.

## 2. Architecture & Data Intelligence
- Ingestion: registration form + structured profile + runtime ingestion API (`/api/profiles/ingest`, `/api/profiles/reset`).
- Enrichment: connector registry (`website`, `structured_funding`, `clearbit`, `crunchbase`, `openalex`) with environment-driven enablement and graceful fallback.
- Intelligence: normalized profile tags + weighted scoring.
- Output: ranked matches with rationale and confidence.
- Output: ranked matches with rationale, confidence, and risk labels.
- Surface: organizer dashboard with top pairs, non-obvious high-value pairs, and per-attendee recommendations.
- Control plane: organizer decisioning (`approved/rejected/pending`) plus intro notes persisted in SQLite.

## 3. Matching Logic & Explanations
Scoring uses a weighted model:
- `fit_score` (semantic overlap proxy)
- `complementarity_score` (investor-builder-regulator pairing quality)
- `readiness_score` (near-term transacting signals)
- `final_score = 0.4*fit + 0.35*complementarity + 0.25*readiness`

Each match includes an explanation string and confidence value for human review.
Explanation generation uses an LLM when enabled (`ENABLE_LLM_RATIONALE=1` with API key), with deterministic fallback templates for reliability.
The engine also labels each recommendation with `risk_level`/`risk_reasons` and surfaces a non-obvious match list to highlight complementary opportunities beyond obvious keyword overlap.

## 4. Test Profiles and Recommended Matches
Top recommendations from current engine:
- `p1 Amara Okafor`: Marcus Chen, James Whitfield, Dr. Elena Vasquez
- `p2 Marcus Chen`: Dr. Elena Vasquez, Amara Okafor, Sophie Bergmann
- `p3 Dr. Elena Vasquez`: Marcus Chen, James Whitfield, Sophie Bergmann
- `p4 James Whitfield`: Dr. Elena Vasquez, Amara Okafor, Marcus Chen
- `p5 Sophie Bergmann`: Marcus Chen, Dr. Elena Vasquez, James Whitfield

Non-obvious but high-value example:
- Sophie Bergmann ↔ Marcus Chen: regulator-sandbox perspective paired with live institutional custody infrastructure.

## 5. Business Case
### Monetization Model
- Primary: premium matchmaking add-on bundled into VIP/operator tiers and sold as sponsor intelligence package.
- Secondary: white-label annual license for other flagship conferences and investor summits.
- Data moat: intro acceptance, meeting completion, and deal-outcome feedback loops improve ranking quality per event.

### Unit Economics (Assumption-Based)
- Event scale: 2,500 attendees.
- Matchmaking addressable cohort: 1,000 high-intent attendees (investors, founders, operators, regulators).
- Premium matchmaking attach rate: 25% (250 users).
- Per-user premium add-on: EUR 600.
- Sponsor intelligence packages: 8 packages at EUR 12,500 each.
- Estimated event-level revenue from matchmaking layer:
  - Premium users: 250 x 600 = EUR 150,000
  - Sponsors: 8 x 12,500 = EUR 100,000
  - Total: EUR 250,000 incremental gross revenue
- Estimated direct event-level costs:
  - Data/API + inference ops: EUR 20,000
  - Product + ops support allocation: EUR 55,000
  - Total: EUR 75,000
- Estimated contribution: EUR 175,000 per event (before shared overhead).

### ROI Logic for Organizer
- Higher meeting quality increases attendee renewal probability and sponsor retention.
- Organizer operations become more efficient via ranked intros and manual override workflow.
- Reuse across events compounds returns because model quality improves with historical outcome data.

## 6. Level 2 and Level 3 Build Evidence
### Level 2 Evidence (Completed)
- Scope and flow definition:
  - `docs/level2/01-scope-and-user-flows.md`
- Wireframes:
  - `docs/level2/02-wireframes.md`
- Data contracts mapped to UI:
  - `docs/level2/03-data-contract-map.md`
- Runnable demo:
  - `scripts/generate_matches.py`
  - `notebooks/matching_demo.ipynb`
- Deterministic output artifacts:
  - `data/match_results.json`
  - `data/level2_summary.csv`
  - `data/level2_summary.md`
- Validation:
  - `scripts/validate_level2.py` (ranking order, rationale presence, profile coverage)

### Level 3 Evidence (Implemented)
- `app/main.py` provides a FastAPI backend with documented endpoints and dashboard serving.
- `app/server.py` starts the FastAPI stack for quick local execution.
- `app/static` provides a clickable web dashboard with top pairs, non-obvious pairs, risk indicators, and organizer actions (approve/reject + notes).
- `app/db.py` persists organizer actions in SQLite (`data/matchmaking.db`).
- Runtime profile ingestion is supported via `/api/profiles/ingest` with reset via `/api/profiles/reset`.
- `scripts/validate_level3.py` verifies risk metadata and non-obvious output coverage.

## 7. Commercialization & Scale Path
- Tiered monetization:
  - included with premium event ticket tiers for attendees
  - sponsor upsell for guaranteed high-value intro visibility
  - white-label licensing for external enterprise conferences
- Data flywheel:
  - track accepted/rejected intros and outcomes
  - retrain ranking weights by real conversion to meetings/deals
  - increase confidence scoring quality event over event

## 8. Risks & Mitigations
- Risk: external enrichment APIs can rate-limit or fail.
  Mitigation: connector registry with environment flags and deterministic fallback signals.
- Risk: LLM explanation variability can reduce trust.
  Mitigation: deterministic template fallback and score-grounded rationale generation.
- Risk: weak conversion from recommendation to actual meetings.
  Mitigation: human-in-the-loop organizer controls, action tracking, and feedback-based reweighting.
- Risk: compliance/privacy concerns for attendee data.
  Mitigation: minimum necessary data storage, explicit source logging, and per-event data segregation.
