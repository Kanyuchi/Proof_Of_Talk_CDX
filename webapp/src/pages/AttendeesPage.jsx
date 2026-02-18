import { useMemo, useState } from 'react'
import EmptyState from '../components/EmptyState'
import { useAttendees, useEnrichmentList, useRefreshEnrichment } from '../hooks/useAttendees'

const roleOptions = ['vip', 'speaker', 'sponsor', 'delegate', 'attendee']

export default function AttendeesPage() {
  const [search, setSearch] = useState('')
  const [roles, setRoles] = useState([])
  const [connectors, setConnectors] = useState(['social_profiles', 'structured_funding'])
  const attendees = useAttendees(search, roles)
  const enrichment = useEnrichmentList()
  const refresh = useRefreshEnrichment()

  const items = attendees.data?.attendees || []

  function toggleRole(role) {
    setRoles((prev) => (prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]))
  }

  function toggleConnector(name) {
    setConnectors((prev) => (prev.includes(name) ? prev.filter((r) => r !== name) : [...prev, name]))
  }

  async function refreshProfile(profileId) {
    await refresh.mutateAsync({ profile_id: profileId, live_enabled: true, connectors })
  }

  const confidenceMap = useMemo(() => {
    const map = {}
    for (const row of enrichment.data?.enrichment || []) {
      map[row.profile_id] = row.source_confidence
    }
    return map
  }, [enrichment.data])

  return (
    <section className="stack">
      <article className="panel">
        <h2>Attendees</h2>
        <div className="toolbar">
          <input
            placeholder="Search by name, company, or title"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <div className="chips">
            {roleOptions.map((role) => (
              <button
                key={role}
                className={`chip-toggle ${roles.includes(role) ? 'active' : ''}`}
                onClick={() => toggleRole(role)}
              >
                {role}
              </button>
            ))}
          </div>
        </div>
        <p className="muted">Showing {attendees.data?.count || 0} attendees</p>
      </article>

      <article className="panel">
        <h3>Enrichment Controls</h3>
        <p className="muted">Choose connectors for manual refresh.</p>
        <div className="chips">
          {['social_profiles', 'structured_funding', 'website', 'openalex'].map((c) => (
            <button key={c} onClick={() => toggleConnector(c)} className={`chip-toggle ${connectors.includes(c) ? 'active' : ''}`}>
              {c}
            </button>
          ))}
          <button className="btn ghost" onClick={() => refresh.mutateAsync({ live_enabled: true, connectors })}>Refresh all</button>
        </div>
      </article>

      {!items.length ? (
        <EmptyState title="No attendees found" description="Try clearing filters or ingest profiles." />
      ) : (
        <div className="list">
          {items.map((a) => (
            <article key={a.profile_id} className="item">
              <h4>{a.name} <span className="badge">{a.role}</span></h4>
              <p className="muted">{a.title} · {a.organization}</p>
              <p>{a.bio || 'No bio yet.'}</p>
              <p className="muted">Confidence: {confidenceMap[a.profile_id] ?? a.enrichment?.source_confidence ?? '-'} | Website: {a.website || '-'}</p>
              <div className="chips">
                {(a.enrichment?.inferred_tags || []).slice(0, 8).map((tag) => (
                  <span key={tag} className="chip-alt">{tag}</span>
                ))}
              </div>
              <div className="row">
                <button className="btn ghost" onClick={() => refreshProfile(a.profile_id)}>Refresh enrichment</button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
