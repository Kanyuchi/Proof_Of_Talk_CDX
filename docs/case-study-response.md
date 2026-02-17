# Case Study Response Draft

## 1. Product Vision
Proof of Talk should provide concierge-level matchmaking that behaves like an investment-banking intro desk, not a conference attendee directory. The experience begins at registration, enriches each attendee profile before arrival, and delivers prioritized intros with clear reasons and deal-readiness indicators.

## 2. Architecture & Data Intelligence
- Ingestion: registration form + structured profile.
- Enrichment: company/funding/context signals via connector pipeline with graceful fallback when live sources are unavailable.
- Intelligence: normalized profile tags + weighted scoring.
- Output: ranked matches with rationale and confidence.
- Surface: organizer dashboard with top pairs and per-attendee recommendations.
- Control plane: organizer decisioning (`approved/rejected/pending`) plus intro notes persisted in SQLite.

## 3. Matching Logic & Explanations
Scoring uses a weighted model:
- `fit_score` (semantic overlap proxy)
- `complementarity_score` (investor-builder-regulator pairing quality)
- `readiness_score` (near-term transacting signals)
- `final_score = 0.4*fit + 0.35*complementarity + 0.25*readiness`

Each match includes an explanation string and confidence value for human review.
Explanation generation uses an LLM when enabled (`ENABLE_LLM_RATIONALE=1` with API key), with deterministic fallback templates for reliability.

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
- Primary model: premium feature for Proof of Talk ticket tiers and sponsor packages.
- Secondary model: white-label B2B licensing for other high-signal events.
- Moat: proprietary behavioral and outcomes data from elite attendee interactions.
- Expansion: cross-event intelligence graph + partner CRM integrations.

## 6. Level 2 and Level 3 Build Evidence
- `scripts/generate_matches.py` demonstrates recommendation generation.
- `app/main.py` provides a FastAPI backend with documented endpoints and dashboard serving.
- `app/server.py` starts the FastAPI stack for quick local execution.
- `app/static` provides a clickable web dashboard with organizer actions (approve/reject + notes).
- `app/db.py` persists organizer actions in SQLite (`data/matchmaking.db`).
- `data/match_results.json` contains reproducible output from the 5 profile test set.

## 7. Commercialization & Scale Path
- Tiered monetization:
  - included with premium event ticket tiers for attendees
  - sponsor upsell for guaranteed high-value intro visibility
  - white-label licensing for external enterprise conferences
- Data flywheel:
  - track accepted/rejected intros and outcomes
  - retrain ranking weights by real conversion to meetings/deals
  - increase confidence scoring quality event over event
