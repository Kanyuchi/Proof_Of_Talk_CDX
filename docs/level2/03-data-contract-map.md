# Level 2 Data Contract Map

## Contract Coverage By Screen

| Screen | Required Fields | Current Source |
|---|---|---|
| Attendee Home | `target_name`, `score`, `confidence`, `rationale` | `/api/matches?profile_id=<id>` |
| Top Matches List | `priority_rank`, `target_name`, `fit_score`, `complementarity_score`, `readiness_score`, `score`, `confidence` | `/api/matches` |
| Match Detail | `source profile`, `target profile`, `score`, `fit_score`, `complementarity_score`, `readiness_score`, `rationale` | `/api/matches` + `data/test_profiles.json` |
| Organizer Queue | `from_name`, `to_name`, `score`, `action.status`, `action.notes`, `rationale` | `/api/dashboard`, `/api/actions` |

## Endpoint-Level Field Map

### `GET /api/matches?profile_id=p1`
- `profile_id`
- `matches[]`
- `matches[].target_id`
- `matches[].target_name`
- `matches[].priority_rank`
- `matches[].score`
- `matches[].fit_score`
- `matches[].complementarity_score`
- `matches[].readiness_score`
- `matches[].confidence`
- `matches[].rationale`
- `matches[].action.status`
- `matches[].action.notes`

### `GET /api/dashboard`
- `overview.attendee_count`
- `overview.recommended_intro_count`
- `overview.actioned_intro_count`
- `top_intro_pairs[]`
- `top_intro_pairs[].from_name`
- `top_intro_pairs[].to_name`
- `top_intro_pairs[].score`
- `top_intro_pairs[].rationale`
- `top_intro_pairs[].action.status`
- `per_profile` (full per-attendee ranking map)

## Gap Check
- No schema blocker for Level 2 wireframe requirements.
- Existing backend already exposes required fields for attendee and organizer views.
