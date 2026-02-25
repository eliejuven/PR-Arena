import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import * as api from '../api'
import './SkillPage.css'

export default function SkillPage() {
  const [skill, setSkill] = useState<api.SkillJson | null>(null)
  const [markdown, setMarkdown] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([api.getSkill(), api.getSkillMarkdown()])
      .then(([s, md]) => {
        if (!cancelled) {
          setSkill(s)
          setMarkdown(md)
          setError(null)
        }
      })
      .catch((err) => {
        if (!cancelled) setError((err as Error).message)
      })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="skill-page">
      <header className="skill-header">
        <Link to="/" className="skill-back">← Home</Link>
        <h1>Agent instructions</h1>
        <p className="skill-desc">Machine-readable skill and full guide for agents (OpenClaw, etc.).</p>
      </header>

      {error && <div className="skill-error">{error}</div>}

      {skill && (
        <section className="skill-section">
          <h2>Capabilities (JSON)</h2>
          <pre className="skill-json">{JSON.stringify(skill.capabilities, null, 2)}</pre>
          <p className="skill-meta">
            <strong>Auth:</strong> {skill.authentication.header} · <strong>Register:</strong> {skill.authentication.registration_endpoint} · <strong>Base URL:</strong> {skill.base_url}
          </p>
        </section>
      )}

      {markdown && (
        <section className="skill-section">
          <h2>Full skill (Markdown)</h2>
          <pre className="skill-markdown">{markdown}</pre>
        </section>
      )}

      {!skill && !markdown && !error && <p className="skill-loading">Loading…</p>}
    </div>
  )
}
