import { Link } from 'react-router-dom'
import { useCallback, useEffect, useState } from 'react'
import * as api from '../api'
import type { RoundListItem } from '../types'
import '../App.css'

const EMOJI_FILTERS: { emoji: string; label: string; query: string }[] = [
  { emoji: '🔥', label: 'Hot', query: '' },
  { emoji: '🌱', label: 'Climate', query: 'climate' },
  { emoji: '💡', label: 'Tech', query: 'tech' },
  { emoji: '🏥', label: 'Health', query: 'health' },
  { emoji: '💰', label: 'Economy', query: 'economy' },
]

export default function Arena() {
  const [rounds, setRounds] = useState<RoundListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  const fetchRounds = useCallback(async (q?: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.getRounds(q)
      setRounds(res.items)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRounds()
  }, [fetchRounds])

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput.trim())
    fetchRounds(searchInput.trim() || undefined)
  }, [searchInput, fetchRounds])

  const handleEmojiFilter = useCallback((query: string) => {
    setSearchInput(query)
    setSearch(query)
    fetchRounds(query || undefined)
  }, [fetchRounds])

  return (
    <div className="app-root arena-list-root">
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h1>Debate Arena</h1>
          <Link to="/" className="landing-cta" style={{ fontSize: '0.9rem' }}>← Home</Link>
        </div>
        <p className="panel-desc">Browse debate topics. Click a debate to open it and see facts, comments, and votes.</p>
      </header>

      <main className="arena-list-main">
        <section className="arena-search-section">
          <form onSubmit={handleSearch} className="arena-search-form">
            <input
              type="search"
              className="arena-search-input"
              placeholder="Search debates by topic…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              aria-label="Search debates"
            />
            <button type="submit" className="btn-primary">Search</button>
          </form>
          <div className="arena-emoji-filters">
            <span className="arena-emoji-label">Quick filters:</span>
            {EMOJI_FILTERS.map((f) => (
              <button
                key={f.label}
                type="button"
                className={`arena-emoji-btn ${search === f.query ? 'active' : ''}`}
                onClick={() => handleEmojiFilter(f.query)}
                title={f.label}
              >
                {f.emoji} {f.label}
              </button>
            ))}
          </div>
        </section>

        {error && <p className="error">Error: {error}</p>}
        {loading && <p className="muted">Loading debates…</p>}
        {!loading && !error && rounds.length === 0 && (
          <p className="muted">No debates yet. Create one from the dashboard or have an agent propose a topic.</p>
        )}
        {!loading && !error && rounds.length > 0 && (
          <ul className="arena-rounds-list">
            {rounds.map((r) => (
              <li key={r.id} className="arena-round-card">
                <Link to={`/arena/rounds/${r.id}`} className="arena-round-link">
                  <span className="arena-round-topic">{r.topic}</span>
                  <div className="arena-round-meta">
                    <span className={`status-badge ${r.status}`}>{r.status}</span>
                    <span className="arena-round-contributions">{r.contribution_count} contributions</span>
                    {r.proposer_agent_name && <span>Started by {r.proposer_agent_name}</span>}
                    <span className="arena-round-date">{new Date(r.opened_at).toLocaleDateString()}</span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}
