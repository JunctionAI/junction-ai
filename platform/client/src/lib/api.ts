import { supabase } from './supabase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api'

async function authHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession()
  return {
    'Content-Type': 'application/json',
    ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = await authHeaders()
  let res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers as Record<string, string> || {}) },
  })

  // On 401, try refreshing the session token and retry once
  if (res.status === 401) {
    const { error } = await supabase.auth.refreshSession()
    if (!error) {
      const freshHeaders = await authHeaders()
      res = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: { ...freshHeaders, ...(options.headers as Record<string, string> || {}) },
      })
    }
  }

  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }
  return res.json()
}

export const api = {
  // Profile
  getProfile: () => request<{ profile_text: string; raw_answers: Record<string, unknown> }>('/profile'),
  updateProfile: (data: { raw_answers: Record<string, unknown> }) =>
    request('/profile', { method: 'PUT', body: JSON.stringify(data) }),
  compileProfile: () => request<{ profile_text: string }>('/profile/compile', { method: 'POST' }),

  // Voice transcription — uses multipart/form-data (cannot use request() helper)
  transcribeVoice: async (audioBlob: Blob, filename: string): Promise<{ transcript: string }> => {
    const { data: { session } } = await supabase.auth.getSession()
    const formData = new FormData()
    formData.append('audio', audioBlob, filename)
    const res = await fetch(`${API_URL}/profile/voice`, {
      method: 'POST',
      headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {},
      body: formData,
    })
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
    return res.json()
  },

  // Agents
  getAgents: () => request<Agent[]>('/agents'),
  createAgent: (data: CreateAgentInput) =>
    request<Agent>('/agents', { method: 'POST', body: JSON.stringify(data) }),
  getAgent: (id: string) => request<Agent>(`/agents/${id}`),
  updateAgent: (id: string, data: Partial<Agent>) =>
    request<Agent>(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAgent: (id: string) =>
    request(`/agents/${id}`, { method: 'DELETE' }),

  // Preview first message (Opus 4.6, no agent created)
  previewFirstMessage: (data: CreateAgentInput) =>
    request<{ first_message: string }>('/agents/preview-first-message', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Agent messages
  getMessages: (agentId: string, page = 1) =>
    request<{ messages: Message[]; total: number }>(`/agents/${agentId}/messages?page=${page}`),

  // Agent memory
  getMemory: (agentId: string) =>
    request<{ facts: Fact[] }>(`/agents/${agentId}/memory`),
  forgetFact: (agentId: string, factId: number) =>
    request(`/agents/${agentId}/memory/${factId}`, { method: 'DELETE' }),

  // Agent test chat
  testMessage: (agentId: string, message: string) =>
    request<{ response: string }>(`/agents/${agentId}/test`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),

  // Telegram
  verifyTelegram: (code: string) =>
    request<{ verified: boolean }>('/telegram/verify', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),

  // Account
  deleteAccount: () => request('/profile/account', { method: 'DELETE' }),

  // Usage
  getUsage: () => request<UsageSummary>('/usage'),
  getAgentUsage: () => request<AgentUsage[]>('/usage/agents'),
}

// Types
export interface Agent {
  id: string
  slug: string
  display_name: string
  purpose: string
  agent_md: string
  knowledge_md: string
  context_md: string
  model: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateAgentInput {
  display_name: string
  purpose: string
  personality: string
  knowledge?: string
  schedule?: {
    cron_expression: string
    task_prompt: string
    description: string
  }
  // New fields
  goal_domain?: string
  dream_outcome?: string
  inspirations?: string
  expertise?: string
  accountability_level?: number
  check_in_frequency?: string
  check_in_style?: string
}

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Fact {
  id: number
  fact: string
  category: string
  confidence: number
  created_at: string
}

export interface UsageSummary {
  total_input_tokens: number
  total_output_tokens: number
  total_cost_usd: number
  total_requests: number
}

export interface AgentUsage {
  agent_id: string
  agent_name: string
  input_tokens: number
  output_tokens: number
  cost_usd: number
  requests: number
}
