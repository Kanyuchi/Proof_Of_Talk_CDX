export const demoOverview = {
  attendee_count: 5,
  recommended_intro_count: 10,
  actioned_intro_count: 2,
  risk_distribution: { low: 12, medium: 6, high: 2 }
}

export const demoPairs = [
  {
    from_id: 'p2',
    from_name: 'Marcus Chen',
    to_id: 'p3',
    to_name: 'Dr. Elena Vasquez',
    score: 0.65,
    confidence: 0.69,
    risk_level: 'low',
    rationale: 'High complementarity and near-term readiness.'
  }
]

export const demoAttendees = [
  {
    profile_id: 'p1',
    name: 'Amara Okafor',
    title: 'Director of Digital Assets',
    organization: 'Abu Dhabi Sovereign Wealth Fund',
    role: 'vip',
    bio: 'Leads tokenized RWA investment strategy.',
    enrichment: { inferred_tags: ['tokenized securities', 'institutional custody'], source_confidence: 0.72 }
  }
]
