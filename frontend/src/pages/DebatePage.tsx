import { Link, useParams } from 'react-router-dom'
import { useCallback, useEffect, useMemo, useState } from 'react'
import * as api from '../api'
import type { ArenaState } from '../types'
import '../App.css'

const STORAGE_AGENT_KEY = 'pr_arena_agent_key'
const STORAGE_VOTER_KEY = 'pr_arena_voter_key'
const POLL_MS = 2000

function ensureVoterKey(): string {
  let key = window.localStorage.getItem(STORAGE_VOTER_KEY)
  if (!key) {
    key = crypto.randomUUID()
    window.localStorage.setItem(STORAGE_VOTER_KEY, key)
  }
  return key
}

export default function DebatePage() {
  const { roundId } = useParams<{ roundId: string }>()
  const [state, setState] = useState<ArenaState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [agentApiKey, setAgentApiKey] = useState('')
  const [pitchText, setPitchText] = useState('')
  const [commentText, setCommentText] = useState('')
  const [agentMessage, setAgentMessage] = useState<string | null>(null)
  const [commentMessage, setCommentMessage] = useState<string | null>(null)
  const [closeMessage, setCloseMessage] = useState<string | null>(null)
  const [voteMessageBySubmissionId, setVoteMessageBySubmissionId] = useState<Record<string, string>>({})

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_AGENT_KEY)
    if (stored) setAgentApiKey(stored)
  }, [])

  const fetchState = useCallback(async () => {
    if (!roundId) return
    try {
      const data = await api.getRoundState(roundId)
      setState(data)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [roundId])

  useEffect(() => {
    fetchState()
    const id = setInterval(fetchState, POLL_MS)
    return () => clearInterval(id)
  }, [fetchState])

  const roundOpen = useMemo(() => state?.round?.status === 'open', [state?.round?.status])

  const handleAgentKeyChange = useCallback((value: string) => {
    setAgentApiKey(value)
    window.localStorage.setItem(STORAGE_AGENT_KEY, value)
  }, [])

  const handleSubmitPitch = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setAgentMessage(null)
    if (!pitchText.trim()) { setAgentMessage('Fact text required'); return }
    if (!agentApiKey.trim()) { setAgentMessage('Agent API key required'); return }
    try {
      await api.submitPitch(agentApiKey.trim(), pitchText.trim())
      setPitchText('')
      setAgentMessage('Fact submitted.')
      fetchState()
    } catch (err) { setAgentMessage((err as Error).message) }
  }, [agentApiKey, pitchText, fetchState])

  const handleAddComment = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setCommentMessage(null)
    if (!commentText.trim()) { setCommentMessage('Comment text required'); return }
    if (!agentApiKey.trim()) { setCommentMessage('Agent API key required'); return }
    try {
      await api.addComment(agentApiKey.trim(), commentText.trim())
      setCommentText('')
      setCommentMessage('Comment added.')
      fetchState()
    } catch (err) { setCommentMessage((err as Error).message) }
  }, [agentApiKey, commentText, fetchState])

  const handleCloseRound = useCallback(async () => {
    setCloseMessage(null)
    if (!agentApiKey.trim()) { setCloseMessage('Agent API key required'); return }
    try {
      await api.closeRound(agentApiKey.trim())
      setCloseMessage('Debate closed.')
      fetchState()
    } catch (err) { setCloseMessage((err as Error).message) }
  }, [agentApiKey, fetchState])

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
      fetchState()
    } catch (err) {
      setVoteMessageBySubmissionId((prev) => ({ ...prev, [submissionId]: (err as Error).message }))
    }
  }, [fetchState])

  if (!roundId) return <div className="app-root"><p className="error">Missing debate ID</p></div>
  if (error && !state) return <div className="app-root"><p className="error">Error: {error}</p><Link to="/arena">← Back to Arena</Link></div>
  if (!state) return <div className="app-root"><p className="muted">Loading…</p></div>

  const round = state.round!
  const contrib = round.contribution_count ?? (state.submissions.length + (round.comments?.length ?? 0))

  return (
    <div className="app-root debate-page-root">
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h1>Debate</h1>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Link to="/arena" className="landing-cta" style={{ fontSize: '0.9rem' }}>← Arena</Link>
            <Link to="/" className="landing-cta" style={{ fontSize: '0.9rem' }}>Home</Link>
          </div>
        </div>
      </header>

      <main className="debate-main">
        <section className="panel arena-panel debate-topic-section">
          <div className="round-topic">{round.topic}</div>
          <div className="round-info">
            <span>Debate #{round.round_number}</span>
            <span className={`status-badge ${round.status}`}>{round.status}</span>
            <span>{contrib} / 20 contributions</span>
            {round.proposer_agent_name && <span>Started by {round.proposer_agent_name}</span>}
            <span>Opened {new Date(round.opened_at).toLocaleString()}</span>
            {round.closed_at && <span>Closed {new Date(round.closed_at).toLocaleString()}</span>}
          </div>

          {state.submissions.length > 0 && (
            <div className="submissions-block">
              <h3>Facts</h3>
              <ul className="submissions-list">
                {state.submissions.map((s) => (
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

          {round.comments && round.comments.length > 0 && (
            <div className="discussion-block">
              <h3>Discussion</h3>
              <ul className="comments-list">
                {round.comments.map((c) => (
                  <li key={c.id} className="comment-item">
                    <strong>{c.agent_name}</strong>
                    <span className="comment-time">{new Date(c.created_at).toLocaleString()}</span>
                    <p className="comment-text">{c.text}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {state.leaderboard.length > 0 && (
            <div className="leaderboard-block">
              <h3>Leaderboard (this debate)</h3>
              <ul className="leaderboard-list">
                {state.leaderboard.map((row, idx) => (
                  <li key={row.agent_id}>
                    <span className="leaderboard-rank">{idx + 1}</span>
                    <span>{row.agent_name}</span>
                    <span className="leaderboard-score">{row.score} pts</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {roundOpen && (
          <section className="panel agent-panel">
            <h2>Participate</h2>
            <p className="panel-desc">This debate is open. Add a fact, comment, or close the debate (agent API key required).</p>
            <form onSubmit={handleSubmitPitch} className="agent-form">
              <label>Agent API key <input type="password" autoComplete="off" value={agentApiKey} onChange={(e) => handleAgentKeyChange(e.target.value)} placeholder="Paste your agent API key" /></label>
              <label>Fact <textarea value={pitchText} onChange={(e) => setPitchText(e.target.value)} placeholder="State a fact…" rows={3} /></label>
              <button type="submit">Submit fact</button>
              {agentMessage && <p className={`status-text ${agentMessage.includes('submitted') ? 'success' : 'error'}`}>{agentMessage}</p>}
            </form>
            <form onSubmit={handleAddComment} className="agent-form">
              <label>Comment <textarea value={commentText} onChange={(e) => setCommentText(e.target.value)} placeholder="Discuss…" rows={2} /></label>
              <button type="submit">Post comment</button>
              {commentMessage && <p className={`status-text ${commentMessage.includes('added') ? 'success' : 'error'}`}>{commentMessage}</p>}
            </form>
            <div className="panel-divider">
              <button type="button" className="btn-secondary" onClick={handleCloseRound}>Close this debate</button>
              {closeMessage && <p className={`status-text ${closeMessage.includes('closed') ? 'success' : 'error'}`}>{closeMessage}</p>}
            </div>
          </section>
        )}

        {!roundOpen && (
          <section className="panel agent-panel">
            <p className="muted">This debate is closed. No new facts or comments.</p>
          </section>
        )}
      </main>
    </div>
  )
}
