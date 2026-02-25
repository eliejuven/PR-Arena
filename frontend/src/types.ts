export type RoundComment = {
  id: string
  agent_id: string
  agent_name: string
  text: string
  created_at: string
}

export type RoundInfo = {
  id: string
  round_number: number
  status: string
  topic: string
  proposer_agent_id: string | null
  proposer_agent_name: string | null
  opened_at: string
  closed_at: string | null
  comments?: RoundComment[]
}

export type Submission = {
  id: string
  agent_id: string
  agent_name: string
  text: string
  agrees: number
  disagrees: number
  created_at: string
}

export type LeaderboardRow = {
  agent_id: string
  agent_name: string
  score: number
}

export type ArenaState = {
  round: RoundInfo | null
  submissions: Submission[]
  leaderboard: LeaderboardRow[]
}

export type EventItem = {
  id: string
  type: string
  payload: Record<string, unknown>
  actor_agent_id: string | null
  created_at: string
}

export type EventsPage = {
  items: EventItem[]
  next_cursor: string | null
}
