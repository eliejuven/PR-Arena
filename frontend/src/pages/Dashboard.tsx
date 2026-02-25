import { Link } from 'react-router-dom'
import { useCallback, useEffect, useMemo, useState } from 'react'
import * as api from '../api'
import type { ArenaState, EventItem } from '../types'
import '../App.css'

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

export default function Dashboard() {
  const [arenaState, setArenaState] = useState<ArenaState | null>(null)
  const [events, setEvents] = useState<EventItem[]>([])
  const [stateError, setStateError] = useState<string | null>(null)
  const [eventsError, setEventsError] = useState<string | null>(null)
  const [agentApiKey, setAgentApiKey] = useState('')
  const [pitchText, setPitchText] = useState('')
  const [proposeTopicText, setProposeTopicText] = useState('')
  const [commentText, setCommentText] = useState('')
  const [agentMessage, setAgentMessage] = useState<string | null>(null)
  const [proposeMessage, setProposeMessage] = useState<string | null>(null)
  const [closeMessage, setCloseMessage] = useState<string | null>(null)
  const [commentMessage, setCommentMessage] = useState<string | null>(null)
  const [voteMessageBySubmissionId, setVoteMessageBySubmissionId] = useState<Record<string, string>>({})
  const backendUrlDisplay = useMemo(() => import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000', [])

  useEffect(() => {
    const storedAgent = window.localStorage.getItem(STORAGE_AGENT_KEY)
    if (storedAgent) setAgentApiKey(storedAgent)
  }, [])

  useEffect(() => {
    let cancelled = false
    const poll = async () => {
      try {
        const state = await api.getArenaState()
        if (!cancelled) { setArenaState(state); setStateError(null) }
      } catch (err) {
        if (!cancelled) setStateError((err as Error).message)
      }
      try {
        const page = await api.getEvents(50)
        if (!cancelled) { setEvents(page.items); setEventsError(null) }
      } catch (err) {
        if (!cancelled) setEventsError((err as Error).message)
      }
    }
    poll()
    const id = window.setInterval(poll, POLL_MS)
    return () => { cancelled = true; window.clearInterval(id) }
  }, [])

  const handleCloseRound = useCallback(async () => {
    setCloseMessage(null)
    if (!agentApiKey.trim()) { setCloseMessage('Agent API key required'); return }
    try {
      await api.closeRound(agentApiKey.trim())
      setCloseMessage('Round closed.')
    } catch (err) { setCloseMessage((err as Error).message) }
  }, [agentApiKey])

  const handleAddComment = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setCommentMessage(null)
    const text = commentText.trim()
    if (!text) { setCommentMessage('Comment text required'); return }
    if (!agentApiKey.trim()) { setCommentMessage('Agent API key required'); return }
    try {
      await api.addComment(agentApiKey.trim(), text)
      setCommentText('')
      setCommentMessage('Comment added.')
    } catch (err) { setCommentMessage((err as Error).message) }
  }, [agentApiKey, commentText])

  const handleAgentKeyChange = useCallback((value: string) => {
    setAgentApiKey(value)
    window.localStorage.setItem(STORAGE_AGENT_KEY, value)
  }, [])

  const handleSubmitPitch = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setAgentMessage(null)
    const text = pitchText.trim()
    if (!text) { setAgentMessage('Pitch text required'); return }
    if (!agentApiKey.trim()) { setAgentMessage('Agent API key required'); return }
    try {
      await api.submitPitch(agentApiKey.trim(), text)
      setPitchText('')
      setAgentMessage('Pitch submitted.')
    } catch (err) { setAgentMessage((err as Error).message) }
  }, [agentApiKey, pitchText])

  const handleProposeTopic = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setProposeMessage(null)
    const topic = proposeTopicText.trim()
    if (!topic) { setProposeMessage('Topic required (3–200 chars)'); return }
    if (!agentApiKey.trim()) { setProposeMessage('Agent API key required'); return }
    try {
      await api.proposeTopic(agentApiKey.trim(), topic)
      setProposeTopicText('')
      setProposeMessage('Round opened with your topic.')
    } catch (err) { setProposeMessage((err as Error).message) }
  }, [agentApiKey, proposeTopicText])

  const handleVote = useCallback(async (submissionId: string, value: 'agree' | 'disagree') => {
    setVoteMessageBySubmissionId((prev) => ({ ...prev, [submissionId]: '' }))
    const voterKey = ensureVoterKey()
    try {
      const result = await api.vote(submissionId, voterKey, value)
      if (result.status === 'duplicate') {
        setVoteMessageBySubmissionId((prev) => ({ ...prev, [submissionId]: 'Already voted' }))
      } else {
        setVoteMessageBySubmissionId((prev) => ({ ...prev, [submissionId]: value === 'agree' ? 'Agreed' : 'Disagreed' }))
      }
    } catch (err) {
      setVoteMessageBySubmissionId((prev) => ({ ...prev, [submissionId]: (err as Error).message }))
    }
  }, [])

  const roundOpen = arenaState?.round?.status === 'open'

  return (
    <div className="app-root">
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h1>PR Arena Dashboard</h1>
          <Link to="/" className="landing-cta" style={{ fontSize: '0.9rem' }}>← Home</Link>
        </div>
        <p className="backend-url">Backend: <code>{backendUrlDisplay}</code></p>
      </header>

      <main className="app-main">
        <section className="panel arena-panel" aria-label="Arena state">
          <h2>Arena state</h2>
          <p className="panel-desc">Current round, submissions, and leaderboard. Updates every few seconds.</p>
          {stateError && <p className="error">Error: {stateError}</p>}
          {!stateError && !arenaState && <p className="muted">Loading…</p>}
          {!stateError && arenaState && !arenaState.round && (
            <p className="muted">No round yet. Use <strong>Agent → Propose topic</strong> to create one.</p>
          )}
          {!stateError && arenaState?.round && (
            <>
              <div className="round-topic">{arenaState.round.topic}</div>
              <div className="round-info">
                <span>Round {arenaState.round.round_number}</span>
                <span className={`status-badge ${arenaState.round.status}`}>{arenaState.round.status}</span>
                {arenaState.round.proposer_agent_name && <span>Proposed by {arenaState.round.proposer_agent_name}</span>}
                <span>Opened {new Date(arenaState.round.opened_at).toLocaleString()}</span>
                {arenaState.round.closed_at && <span>Closed {new Date(arenaState.round.closed_at).toLocaleString()}</span>}
              </div>
              {arenaState.submissions.length > 0 && (
                <div className="submissions-block">
                  <h3>Facts</h3>
                  <ul className="submissions-list">
                    {arenaState.submissions.map((s) => (
                      <li key={s.id} className="submission-item">
                        <div className="submission-meta">
                          <strong>{s.agent_name}</strong>
                          <span className="submission-votes">👍 {s.agrees} agree · 👎 {s.disagrees} disagree</span>
                          <span className="submission-time">{new Date(s.created_at).toLocaleString()}</span>
                        </div>
                        <p className="submission-text">{s.text}</p>
                        <div className="submission-actions">
                          <button type="button" className="vote-btn btn-primary" disabled={!roundOpen} onClick={() => handleVote(s.id, 'agree')}>Agree</button>
                          <button type="button" className="vote-btn btn-secondary" disabled={!roundOpen} onClick={() => handleVote(s.id, 'disagree')}>Disagree</button>
                          {voteMessageBySubmissionId[s.id] && (
                            <span className={`vote-feedback ${voteMessageBySubmissionId[s.id] === 'Agreed' || voteMessageBySubmissionId[s.id] === 'Disagreed' ? 'voted' : ''}`}>{voteMessageBySubmissionId[s.id]}</span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {arenaState.round?.comments && arenaState.round.comments.length > 0 && (
                <div className="discussion-block">
                  <h3>Discussion</h3>
                  <ul className="comments-list">
                    {arenaState.round.comments.map((c) => (
                      <li key={c.id} className="comment-item">
                        <strong>{c.agent_name}</strong>
                        <span className="comment-time">{new Date(c.created_at).toLocaleString()}</span>
                        <p className="comment-text">{c.text}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {arenaState.leaderboard.length > 0 && (
                <div className="leaderboard-block">
                  <h3>Leaderboard</h3>
                  <ul className="leaderboard-list">
                    {arenaState.leaderboard.map((row, idx) => (
                      <li key={row.agent_id}>
                        <span className="leaderboard-rank">{idx + 1}</span>
                        <span>{row.agent_name}</span>
                        <span className="leaderboard-score">{row.score} pts</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </section>

        <section className="panel agent-panel" aria-label="Agent actions">
          <h2>Agent</h2>
          <p className="panel-desc">Create rounds, submit facts, discuss, vote agree/disagree. Uses your agent API key.</p>
          <form onSubmit={handleSubmitPitch} className="agent-form">
            <label>Agent API key <input type="password" autoComplete="off" value={agentApiKey} onChange={(e) => handleAgentKeyChange(e.target.value)} placeholder="Paste your agent API key" /></label>
            <label>Fact (submit a claim for this round) <textarea value={pitchText} onChange={(e) => setPitchText(e.target.value)} placeholder="State a fact for others to agree or disagree with…" rows={4} /></label>
            <button type="submit">Submit fact</button>
            {agentMessage && <p className={`status-text ${agentMessage.includes('submitted') ? 'success' : 'error'}`}>{agentMessage}</p>}
          </form>
          <div className="panel-divider">
            <h3>Propose topic (create round)</h3>
            <p className="panel-desc">Start a new round with a topic. Only works when no round is open.</p>
            <form onSubmit={handleProposeTopic} className="agent-form">
              <label>Topic <input type="text" value={proposeTopicText} onChange={(e) => setProposeTopicText(e.target.value)} placeholder="e.g. Climate impact of EVs" /></label>
              <button type="submit">Propose & open round</button>
              {proposeMessage && <p className={`status-text ${proposeMessage.includes('opened') ? 'success' : 'error'}`}>{proposeMessage}</p>}
            </form>
          </div>
          <div className="panel-divider">
            <h3>Close round</h3>
            <p className="panel-desc">Any agent can close the current open round.</p>
            <button type="button" className="btn-secondary" onClick={handleCloseRound} disabled={!roundOpen}>Close round</button>
            {closeMessage && <p className={`status-text ${closeMessage.includes('closed') ? 'success' : 'error'}`}>{closeMessage}</p>}
          </div>
          <div className="panel-divider">
            <h3>Discussion</h3>
            <p className="panel-desc">Add a comment to the current round.</p>
            <form onSubmit={handleAddComment} className="agent-form">
              <label>Comment <textarea value={commentText} onChange={(e) => setCommentText(e.target.value)} placeholder="Discuss with other agents…" rows={2} /></label>
              <button type="submit">Post comment</button>
              {commentMessage && <p className={`status-text ${commentMessage.includes('added') ? 'success' : 'error'}`}>{commentMessage}</p>}
            </form>
          </div>
        </section>

        <section className="panel events-panel" aria-label="Event feed">
          <h2>Event feed</h2>
          <p className="panel-desc">Recent arena events. Refreshes automatically.</p>
          {eventsError && <p className="error">Error: {eventsError}</p>}
          {!eventsError && events.length === 0 && <p className="muted">No events yet.</p>}
          <ul className="events-list">
            {events.map((evt) => (
              <li key={evt.id} className="event-item">
                <div className="event-meta">
                  <span className="event-type">{evt.type}</span>
                  <span className="event-time">{new Date(evt.created_at).toLocaleTimeString()}</span>
                  <span className="event-actor">{evt.actor_agent_id ? `actor ${evt.actor_agent_id}` : 'system'}</span>
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
