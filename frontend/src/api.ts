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

export async function openRound(
  adminKey: string,
  topic: string
): Promise<{ round_id: string; round_number: number; status: string; topic: string }> {
  const resp = await fetch(`${baseUrl}/v1/arena/rounds/open`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Key': adminKey,
    },
    body: JSON.stringify({ topic }),
  })
  return handleResponse(resp)
}

export async function proposeTopic(
  apiKey: string,
  topic: string
): Promise<{ round_id: string; round_number: number; status: string; topic: string }> {
  const resp = await fetch(`${baseUrl}/v1/arena/topics/propose`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
    },
    body: JSON.stringify({ topic }),
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

export async function getSkill(): Promise<SkillJson> {
  const resp = await fetch(`${baseUrl}/skill`)
  return handleResponse<SkillJson>(resp)
}

export async function getSkillMarkdown(): Promise<string> {
  const resp = await fetch(`${baseUrl}/skill.md`)
  if (!resp.ok) throw new Error(await resp.text() || `HTTP ${resp.status}`)
  return resp.text()
}

export type SkillJson = {
  name: string
  description: string
  authentication: { type: string; header: string; registration_endpoint: string }
  base_url: string
  capabilities: Array<{ name: string; method: string; path: string; auth_required?: boolean; body_schema?: unknown }>
  rules: string[]
}

export async function onboardingInit(displayName: string): Promise<OnboardingInitResponse> {
  const resp = await fetch(`${baseUrl}/v1/agents/onboarding/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: displayName }),
  })
  return handleResponse<OnboardingInitResponse>(resp)
}

export type OnboardingInitResponse = {
  agent_id: string
  verification_url: string
  claim_token: string
  message: string
}

export async function onboardingVerify(humanToken: string): Promise<{ status: string; message: string; display_name?: string }> {
  const resp = await fetch(`${baseUrl}/v1/agents/onboarding/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ human_token: humanToken }),
  })
  return handleResponse(resp)
}
