# Level 2 Wireframes (Low Fidelity)

## 1. Attendee Home

```text
+--------------------------------------------------------------------------------+
| Proof of Talk 2026                                                            |
| Welcome, [Attendee Name]                   [Profile Strength: High]           |
+--------------------------------------------------------------------------------+
| Your Best Intro Opportunities                                                   |
| 1) Marcus Chen                     Score 0.64  Confidence 0.70   [View]       |
| 2) James Whitfield                 Score 0.52  Confidence 0.63   [View]       |
| 3) Dr. Elena Vasquez               Score 0.42  Confidence 0.66   [View]       |
+--------------------------------------------------------------------------------+
| Why this matters: Curated for transactable meetings, not networking volume.   |
+--------------------------------------------------------------------------------+
```

## 2. Top Matches List

```text
+--------------------------------------------------------------------------------+
| Top Matches                                                                     |
+--------------------------------------------------------------------------------+
| Rank | Match Name          | Fit | Comp | Readiness | Final | Confidence | CTA |
| 1    | Marcus Chen         | .17 | 1.00 | .88       | .64   | .70        | Open|
| 2    | James Whitfield     | .07 | 1.00 | .58       | .52   | .63        | Open|
| 3    | Dr. Elena Vasquez   | .07 | .50  | .88       | .42   | .66        | Open|
+--------------------------------------------------------------------------------+
```

## 3. Match Detail + Rationale

```text
+--------------------------------------------------------------------------------+
| Match Detail: Amara Okafor ↔ Marcus Chen                                      |
+--------------------------------------------------------------------------------+
| Final Score: 0.6354      Confidence: 0.6958                                   |
| Fit: 0.1667   Complementarity: 1.0000   Readiness: 0.8750                     |
+--------------------------------------------------------------------------------+
| Rationale                                                                       |
| High strategic complementarity and near-term execution readiness across        |
| institutional custody, RWA deployment, and partnership intent.                 |
+--------------------------------------------------------------------------------+
| Suggested Intro Objective                                                       |
| Validate pilot scope and timeline for sovereign-backed deployment pathway.      |
+--------------------------------------------------------------------------------+
```

## 4. Organizer Queue + Action Panel

```text
+--------------------------------------------------------------------------------+
| Organizer Queue                      [Filter: Pending] [Sort: Highest Score]   |
+--------------------------------------------------------------------------------+
| Pair                                Score  Status     Notes         Action      |
| Marcus ↔ Elena                      0.65   pending    -             [Approve]   |
| Amara ↔ Marcus                      0.64   approved   Day1 priority [Edit]      |
| Elena ↔ James                       0.53   pending    -             [Approve]   |
+--------------------------------------------------------------------------------+
| Selected Pair Detail                                                         |
| Rationale...                                                                  |
| [Approve] [Reject] [Save Note]                                               |
+--------------------------------------------------------------------------------+
```

## Wireframe Data Dependencies
- Identity: `id`, `name`, `title`, `organization`
- Ranking: `score`, `fit_score`, `complementarity_score`, `readiness_score`
- Explainability: `rationale`, `confidence`
- Control plane: `action.status`, `action.notes`, `action.updated_at`
