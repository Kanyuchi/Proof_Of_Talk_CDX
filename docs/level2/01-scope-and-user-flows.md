# Level 2 Scope And User Flows

## Level 2 Goal
Deliver evidence that the matchmaking concept is productized enough for stakeholder walkthroughs before full Level 3 scale-out.

## Definition Of Done
- Wireframes completed for attendee and organizer core flows.
- Runnable demo (`scripts/generate_matches.py` and notebook) produces ranked, explainable matches.
- Output includes top recommendations for all 5 required profiles.
- Documentation contains run steps and evidence summary.

## In-Scope Screens
1. Attendee Home
2. Top Matches List
3. Match Detail And Rationale
4. Organizer Queue And Action Panel

## Out-Of-Scope For Level 2
- Full authentication and RBAC
- Calendar scheduling integrations
- Production-grade API quotas and billing controls

## User Flow A: Attendee
1. Attendee lands on recommendations home.
2. System shows ranked top matches with score, confidence, and rationale teaser.
3. Attendee opens a match detail view.
4. Attendee reviews rationale, score breakdown, and suggested intro objective.

## User Flow B: Organizer
1. Organizer opens queue of top intro pairs.
2. Organizer filters by priority and confidence.
3. Organizer reviews per-profile recommendations.
4. Organizer approves/rejects and adds notes.
5. Actions persist and appear in dashboard state.
