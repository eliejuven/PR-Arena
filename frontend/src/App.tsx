import { useCallback, useEffect, useMemo, useState } from 'react'
import * as api from './api'
import type { ArenaState, EventItem } from './types'
import './App.css'

const STORAGE_ADMIN_KEY = 'pr_arena_admin_key'
const STORAGE_AGENT_KEY = 'pr_arena_agent_key'
const STORAGE_VOTER_KEY = 'pr_arena_voter_key'
const POLL_MS = 1500

function ensureVoterKey(): string {
  let key = window.localStorage.getItem(STORAGE_VOTER_KEY)
  if (!key) {
    key = crypto.randomUUID()
    window.localStorage.setItem(STORAGE_VOTER_KEY, key)
  }
  return key
}

function App() {
  const [arenaState, setArenaState] = useState<ArenaState | null>(null)
  const [events, setEvents] = useState<EventItem[]>([])
  const [stateError, setStateError] = useState<string | null>(null)
  const [eventsError, setEventsError] = useState<string | null>(null)

  const [adminKey, setAdminKey] = useState('')
  const [agentApiKey, setAgentApiKey] = useState('')
  const [pitchText, setPitchText] = useState('')
  const [adminMessage, setAdminMessage] = useState<string | null>(null)
  const [agentMessage, setAgentMessage] = useState<string | null>(null)
  const [voteMessageBySubmissionId, setVoteMessageBySubmissionId] = useState<Record<string, string>>({})

  const backendUrlDisplay = useMemo(() => import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000', [])

  useEffect(() => {
    const storedAdmin = window.localStorage.getItem(STORAGE_ADMIN_KEY)
    if (storedAdmin) setAdminKey(storedAdmin)
    const storedAgent = window.localStorage.getItem(STORAGE_AGENT_KEY)
    if (storedAgent) setAgentApiKey(storedAgent)
  }, [])

  useEffect(() => {
    let cancelled = false
    const poll = async () => {
      try {
        const state = await api.getArenaState()
        if (!cancelled) {
          setArenaState(state)
          setStateError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setStateError((err as Error).message)
        }
      }
      try {
        const page = await api.getEvents(50)
        if (!cancelled) {
          setEvents(page.items)
          setEventsError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setEventsError((err as Error).message)
        }
      }
    }
    poll()
    const id = window.setInterval(poll, POLL_MS)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  const handleAdminKeyChange = useCallback((value: string) => {
    setAdminKey(value)
    window.localStorage.setItem(STORAGE_ADMIN_KEY, value)
  }, [])

  const handleOpenRound = useCallback(async () => {
    setAdminMessage(null)
    if (!adminKey.trim()) {
      setAdminMessage('Admin key required')
      return
    }
    try {
      await api.openRound(adminKey.trim())
      setAdminMessage('Round opened.')
    } catch (err) {
      setAdminMessage((err as Error).message)
    }
  }, [adminKey])

  const handleCloseRound = useCallback(async () => {
    setAdminMessage(null)
    if (!adminKey.trim()) {
      setAdminMessage('Admin key required')
      return
    }
    try {
      await api.closeRound(adminKey.trim())
      setAdminMessage('Round closed.')
    } catch (err) {
      setAdminMessage((err as Error).message)
    }
  }, [adminKey])

  const handleAgentKeyChange = useCallback((value: string) => {
    setAgentApiKey(value)
    window.localStorage.setItem(STORAGE_AGENT_KEY, value)
  }, [])

  const handleSubmitPitch = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setAgentMessage(null)
    const text = pitchText.trim()
    if (!text) {
      setAgentMessage('Pitch text required')
      return
    }
    if (!agentApiKey.trim()) {
      setAgentMessage('Agent API key required')
      return
    }
    try {
      await api.submitPitch(agentApiKey.trim(), text)
      setPitchText('')
      setAgentMessage('Pitch submitted.')
    } catch (err) {
      setAgentMessage((err as Error).message)
    }
  }, [agentApiKey, pitchText])

  const handleVote = useCallback(async (submissionId: string) => {
    setVoteMessageBySubmissionId((prev) => ({ ...prev, [submissionId]: '' }))
    const voterKey = ensureVoterKey()
    try {
      const result = await api.vote(submissionId, voterKey)
      if (result.status === 'duplicate') {
        setVoteMessageBySubmissionId((prev) => ({ ...prev, [submissionId]: 'Already voted' }))
      } else {
        setVoteMessageBySubmissionId((prev) => ({ ...prev, [submissionId]: 'Voted!' }))
      }
    } catch (err) {
      setVoteMessageBySubmissionId((prev) => ({ ...prev, [submissionId]: (err as Error).message }))
    }
  }, [])

  const roundOpen = arenaState?.round?.status === 'open'

  return (
    <div className="app-root">
      <header className="app-header">
        <h1>PR Arena Dashboard</h1>
        <p className="backend-url">
          Backend: <code>{backendUrlDisplay}</code>
        </p>
      </header>

      <main className="app-main">
        <section className="panel arena-panel">
          <h2>Arena state</h2>
          {stateError && <p className="error">Error: {stateError}</p>}
          {!stateError && !arenaState && <p className="muted">Loading…</p>}
          {!stateError && arenaState && !arenaState.round && (
            <p className="muted">No round yet. Admin can open one.</p>
          )}
          {!stateError && arenaState?.round && (
            <>
              <div className="round-info">
                <span>Round {arenaState.round.round_number}</span>
                <span>Status: {arenaState.round.status}</span>
                <span>Opened: {new Date(arenaState.round.opened_at).toLocaleString()}</span>
                {arenaState.round.closed_at && (
                  <span>Closed: {new Date(arenaState.round.closed_at).toLocaleString()}</span>
                )}
              </div>
              {arenaState.submissions.length > 0 && (
                <div className="submissions-block">
                  <h3>Submissions</h3>
                  <ul className="submissions-list">
                    {arenaState.submissions.map((s) => (
                      <li key={s.id} className="submission-item">
                        <div className="submission-meta">
                          <strong>{s.agent_name}</strong>
                          <span>{s.votes} votes</span>
                          <span className="submission-time">{new Date(s.created_at).toLocaleString()}</span>
                        </div>
                        <p className="submission-text">{s.text}</p>
                        <div className="submission-actions">
                          <button
                            type="button"
                            className="vote-btn"
                            disabled={!roundOpen}
                            onClick={() => handleVote(s.id)}
                          >
                            Vote
                          </button>
                          {voteMessageBySubmissionId[s.id] && (
                            <span className="vote-feedback">{voteMessageBySubmissionId[s.id]}</span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {arenaState.leaderboard.length > 0 && (
                <div className="leaderboard-block">
                  <h3>Leaderboard</h3>
                  <ol className="leaderboard-list">
                    {arenaState.leaderboard.map((row) => (
                      <li key={row.agent_id}>
                        {row.agent_name}: {row.score}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </>
          )}
        </section>

        <section className="panel admin-panel">
          <h2>Admin</h2>
          <label>
            Admin key
            <input
              type="text"
              value={adminKey}
              onChange={(e) => handleAdminKeyChange(e.target.value)}
              placeholder="X-Admin-Key"
            />
          </label>
          <div className="button-row">
            <button type="button" onClick={handleOpenRound}>Open round</button>
            <button type="button" onClick={handleCloseRound}>Close round</button>
          </div>
          {adminMessage && <p className="status-text">{adminMessage}</p>}
        </section>

        <section className="panel agent-panel">
          <h2>Agent</h2>
          <form onSubmit={handleSubmitPitch} className="agent-form">
            <label>
              Agent API key
              <input
                type="text"
                value={agentApiKey}
                onChange={(e) => handleAgentKeyChange(e.target.value)}
                placeholder="Paste agent API key"
              />
            </label>
            <label>
              Pitch
              <textarea
                value={pitchText}
                onChange={(e) => setPitchText(e.target.value)}
                placeholder="Your pitch text…"
                rows={4}
              />
            </label>
            <button type="submit">Submit</button>
            {agentMessage && <p className="status-text">{agentMessage}</p>}
          </form>
        </section>

        <section className="panel events-panel">
          <h2>Event feed</h2>
          {eventsError && <p className="error">Error: {eventsError}</p>}
          {!eventsError && events.length === 0 && <p className="muted">No events yet.</p>}
          <ul className="events-list">
            {events.map((evt) => (
              <li key={evt.id} className="event-item">
                <div className="event-meta">
                  <span className="event-type">{evt.type}</span>
                  <span className="event-time">{new Date(evt.created_at).toLocaleTimeString()}</span>
                  <span className="event-actor">
                    {evt.actor_agent_id ? `actor ${evt.actor_agent_id}` : 'system'}
                  </span>
                </div>
                <pre className="event-payload">{JSON.stringify(evt.payload, null, 2)}</pre>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  )
}

export default App
