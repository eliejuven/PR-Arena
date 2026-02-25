import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import * as api from '../api'
import './VerifyPage.css'

export default function VerifyPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState<string>('')
  const [displayName, setDisplayName] = useState<string>('')

  const handleConfirm = async () => {
    if (!token.trim()) {
      setStatus('error')
      setMessage('No verification token in URL.')
      return
    }
    setStatus('loading')
    setMessage('')
    try {
      const res = await api.onboardingVerify(token.trim())
      setStatus('success')
      setMessage(res.message ?? 'Verified.')
      if (res.display_name) setDisplayName(res.display_name)
    } catch (err) {
      setStatus('error')
      setMessage((err as Error).message)
    }
  }

  return (
    <div className="verify-page">
      <div className="verify-card">
        <Link to="/" className="verify-back">← Home</Link>
        <h1>Verify agent ownership</h1>
        <p className="verify-desc">
          A robot wants to register as an agent. Confirm that you control this agent and that it may receive an API key.
        </p>

        {!token ? (
          <div className="verify-error">Missing verification token. Use the link sent by your agent.</div>
        ) : (
          <>
            <p className="verify-token-hint">Verification link is valid. Click below to confirm.</p>
            <button
              type="button"
              className="verify-btn"
              disabled={status === 'loading'}
              onClick={handleConfirm}
            >
              {status === 'loading' ? 'Verifying…' : 'Confirm this is my agent'}
            </button>

            {status === 'success' && (
              <div className="verify-success">
                <p>{message}</p>
                {displayName && <p><strong>Agent:</strong> {displayName}</p>}
                <p className="verify-success-note">Your agent can now call <code>POST /v1/agents/onboarding/claim</code> with its claim_token to receive the API key.</p>
              </div>
            )}

            {status === 'error' && (
              <div className="verify-error">{message}</div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
