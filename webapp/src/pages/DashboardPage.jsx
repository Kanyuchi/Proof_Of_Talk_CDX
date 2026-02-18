import { useMemo, useState } from 'react'
import EmptyState from '../components/EmptyState'
import { useDashboardData, useDrilldown, useSaveAction, useSegments } from '../hooks/useDashboard'

export default function DashboardPage() {
  const dashboard = useDashboardData()
  const segments = useSegments()
  const saveAction = useSaveAction()
  const [selectedPair, setSelectedPair] = useState({ from: '', to: '' })

  const pairs = dashboard.data?.top_intro_pairs || []
  const drilldown = useDrilldown(selectedPair.from, selectedPair.to)

  const overview = dashboard.data?.overview
  const perProfileKeys = useMemo(() => Object.keys(dashboard.data?.per_profile || {}), [dashboard.data])

  async function quickAction(pair, status) {
    await saveAction.mutateAsync({
      from_id: pair.from_id,
      to_id: pair.to_id,
      status,
      notes: `Set via dashboard quick action to ${status}`
    })
  }

  return (
    <section className="stack">
      <div className="panel">
        <h2>Interactive Dashboard</h2>
        {!overview ? (
          <EmptyState title="No dashboard data" description="Run the backend and refresh." />
        ) : (
          <div className="stats-grid">
            <div className="stat"><span>Attendees</span><strong>{overview.attendee_count}</strong></div>
            <div className="stat"><span>Top Intros</span><strong>{overview.recommended_intro_count}</strong></div>
            <div className="stat"><span>Actioned</span><strong>{overview.actioned_intro_count}</strong></div>
          </div>
        )}
      </div>

      <div className="grid two-cols">
        <article className="panel">
          <h3>Top Intro Pairs</h3>
          {!pairs.length && <EmptyState title="No pairs yet" description="No ranked pairs are available." />}
          {pairs.map((pair, idx) => (
            <div key={`${pair.from_id}-${pair.to_id}`} className="item">
              <h4>#{idx + 1}: {pair.from_name} ↔ {pair.to_name}</h4>
              <p className="muted">Score {pair.score} | Risk {pair.risk_level} | Confidence {pair.confidence}</p>
              <p>{pair.rationale}</p>
              <div className="row">
                <button className="btn ghost" onClick={() => setSelectedPair({ from: pair.from_id, to: pair.to_id })}>Drill down</button>
                <button className="btn ghost" onClick={() => quickAction(pair, 'approved')}>Approve</button>
                <button className="btn ghost" onClick={() => quickAction(pair, 'rejected')}>Reject</button>
              </div>
            </div>
          ))}
        </article>

        <article className="panel">
          <h3>Drilldown</h3>
          {!selectedPair.from && <EmptyState title="Pick a pair" description="Select ‘Drill down’ on a top pair to inspect details." />}
          {drilldown.isFetching && <p className="muted">Loading drilldown...</p>}
          {drilldown.data?.match && (
            <div className="item">
              <h4>{drilldown.data.from_profile?.name} ↔ {drilldown.data.to_profile?.name}</h4>
              <p className="muted">Risk {drilldown.data.match.risk_level} | Fit {drilldown.data.match.fit_score} | Readiness {drilldown.data.match.readiness_score}</p>
              <p>{drilldown.data.match.rationale}</p>
              <p className="muted">Source enrichment: {(drilldown.data.from_profile?.enrichment?.inferred_tags || []).slice(0, 4).join(', ') || '-'}</p>
              <p className="muted">Target enrichment: {(drilldown.data.to_profile?.enrichment?.inferred_tags || []).slice(0, 4).join(', ') || '-'}</p>
            </div>
          )}
        </article>
      </div>

      <div className="grid two-cols">
        <article className="panel">
          <h3>Role Segments</h3>
          {Object.keys(segments.data?.roles || {}).length === 0 ? (
            <EmptyState title="No role segments" description="Segments will appear when attendee data is loaded." />
          ) : (
            <ul className="simple-list">
              {Object.entries(segments.data.roles).map(([role, count]) => (
                <li key={role}>{role}: <strong>{count}</strong></li>
              ))}
            </ul>
          )}
        </article>

        <article className="panel">
          <h3>Top Interest Tags</h3>
          {!(segments.data?.top_interest_tags || []).length ? (
            <EmptyState title="No tags" description="Enrichment tags will appear here." />
          ) : (
            <div className="chips">
              {segments.data.top_interest_tags.map((row) => (
                <span key={row.tag} className="chip-alt">{row.tag} ({row.count})</span>
              ))}
            </div>
          )}
        </article>
      </div>

      {!!perProfileKeys.length && (
        <article className="panel">
          <h3>Per-profile coverage</h3>
          <p className="muted">Profiles with ranked recommendations: {perProfileKeys.length}</p>
        </article>
      )}
    </section>
  )
}
