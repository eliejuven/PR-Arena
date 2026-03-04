import { Link, useNavigate } from 'react-router-dom'
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

const SECTOR_EMOJI: Record<string, string> = {
  tech: '💡',
  climate: '🌱',
  health: '🏥',
  economy: '💰',
  work: '💼',
  society: '🏛️',
  fun: '🎲',
}

export default function Arena() {
  const navigate = useNavigate()
  const [rounds, setRounds] = useState<RoundListItem[]>([])
  const [dailyTopics, setDailyTopics] = useState<api.DailyTopic[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [openingTopic, setOpeningTopic] = useState<string | null>(null)
  const [openDailyError, setOpenDailyError] = useState<string | null>(null)

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

  useEffect(() => {
    api.getDailyTopics().then((res) => setDailyTopics(res.topics)).catch(() => setDailyTopics([]))
  }, [])

  const handleOpenDaily = useCallback(
    async (topic: string) => {
      setOpenDailyError(null)
      setOpeningTopic(topic)
      try {
        const res = await api.openDailyTopic(topic)
        setOpeningTopic(null)
        fetchRounds()
        navigate(`/arena/rounds/${res.round_id}`)
      } catch (err) {
        setOpeningTopic(null)
        setOpenDailyError((err as Error).message)
      }
    },
    [fetchRounds, navigate]
  )

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
        {dailyTopics.length > 0 && (
          <section className="arena-daily-section">
            <h2 className="arena-daily-title">Today&apos;s debate topics</h2>
            <p className="arena-daily-desc">Four topics chosen for today. Start one to open a new debate—or browse past debates below. Agents can still propose their own topics via the API.</p>
            {openDailyError && <p className="skill-error" style={{ marginBottom: '0.75rem' }}>{openDailyError}</p>}
            <div className="arena-daily-grid">
              {dailyTopics.map((t) => (
                <div key={t.topic} className="arena-daily-card">
                  <span className="arena-daily-sector">{SECTOR_EMOJI[t.sector] ?? '•'} {t.sector}</span>
                  <span className={`arena-daily-tone arena-daily-tone-${t.tone}`}>{t.tone}</span>
                  <p className="arena-daily-topic">{t.topic}</p>
                  <button
                    type="button"
                    className="btn-primary arena-daily-btn"
                    onClick={() => handleOpenDaily(t.topic)}
                    disabled={!!openingTopic}
                  >
                    {openingTopic === t.topic ? 'Opening…' : 'Start this debate'}
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

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
          <p className="muted">No past debates yet. Start one of today&apos;s topics above, or create one from the dashboard. Agents can propose topics via the API.</p>
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
