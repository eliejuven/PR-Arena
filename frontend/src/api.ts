import type { ArenaState, EventsPage } from './types'

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function handleResponse<T>(resp: Response): Promise<T> {
  const text = await resp.text()
  if (!resp.ok) {
    let message = text
    try {
      const json = JSON.parse(text) as { detail?: string | Array<{ msg?: string }> }
      if (typeof json.detail === 'string') message = json.detail
      else if (Array.isArray(json.detail)) message = json.detail.map((d) => d.msg ?? String(d)).join('; ')
    } catch {
      // use raw text
    }
    throw new Error(message || `HTTP ${resp.status}`)
  }
  return text ? (JSON.parse(text) as T) : ({} as T)
}

export async function getArenaState(): Promise<ArenaState> {
  const resp = await fetch(`${baseUrl}/v1/arena/state`)
  return handleResponse<ArenaState>(resp)
}

export async function openRound(adminKey: string): Promise<{ round_id: string; round_number: number; status: string }> {
  const resp = await fetch(`${baseUrl}/v1/arena/rounds/open`, {
    method: 'POST',
    headers: {
      'X-Admin-Key': adminKey,
    },
  })
  return handleResponse(resp)
}

export async function closeRound(adminKey: string): Promise<{ round_id: string; round_number: number; status: string }> {
  const resp = await fetch(`${baseUrl}/v1/arena/rounds/close`, {
    method: 'POST',
    headers: {
      'X-Admin-Key': adminKey,
    },
  })
  return handleResponse(resp)
}

export async function submitPitch(apiKey: string, text: string): Promise<{ id: string }> {
  const resp = await fetch(`${baseUrl}/v1/arena/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
    },
    body: JSON.stringify({ text }),
  })
  return handleResponse(resp)
}

export type VoteResult = { status: 'ok' } | { status: 'duplicate' }

export async function vote(submissionId: string, voterKey: string): Promise<VoteResult> {
  const resp = await fetch(`${baseUrl}/v1/arena/vote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ submission_id: submissionId, voter_key: voterKey }),
  })
  if (!resp.ok) {
    await handleResponse<never>(resp)
  }
  return resp.json() as Promise<VoteResult>
}

export async function getEvents(limit = 50): Promise<EventsPage> {
  const resp = await fetch(`${baseUrl}/v1/events?limit=${limit}`)
  return handleResponse<EventsPage>(resp)
}
