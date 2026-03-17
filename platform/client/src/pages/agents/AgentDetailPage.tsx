import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, type Agent, type Message, type Fact } from '../../lib/api'

type Tab = 'chat' | 'memory' | 'files' | 'settings'

function confidenceLabel(c: number): string {
  if (c >= 90) return 'High confidence'
  if (c >= 70) return 'Likely'
  return 'Uncertain'
}

export function AgentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [agent, setAgent] = useState<Agent | null>(null)
  const [tab, setTab] = useState<Tab>('chat')
  const [messages, setMessages] = useState<Message[]>([])
  const [facts, setFacts] = useState<Fact[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState(false)
  const [showActivationCard, setShowActivationCard] = useState(true)
  const chatInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!id) return
    Promise.all([
      api.getAgent(id),
      api.getMessages(id),
      api.getMemory(id),
    ]).then(([agent, msgData, memData]) => {
      setAgent(agent)
      setMessages(msgData.messages || [])
      setFacts(memData.facts || [])
    }).catch(console.error)
      .finally(() => setLoading(false))
  }, [id])

  const sendMessage = async () => {
    if (!input.trim() || !id) return
    const msg = input
    setInput('')
    setSending(true)

    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: msg, created_at: new Date().toISOString() }])

    try {
      const { response } = await api.testMessage(id, msg)
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: response, created_at: new Date().toISOString() }])
    } catch {
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: 'Error: Failed to get response. Please try again.', created_at: new Date().toISOString() }])
    } finally {
      setSending(false)
    }
  }

  const forgetFact = async (factId: number) => {
    if (!id) return
    await api.forgetFact(id, factId)
    setFacts(prev => prev.filter(f => f.id !== factId))
  }

  async function handleToggleActive() {
    if (!agent) return
    setToggling(true)
    try {
      const updated = await api.updateAgent(agent.id, { is_active: !agent.is_active })
      setAgent(updated)
    } catch (err) {
      console.error('Failed to toggle agent status:', err)
    } finally {
      setToggling(false)
    }
  }

  if (loading) return <div className="page"><p style={{ color: 'var(--text-dim)' }}>Loading...</p></div>
  if (!agent) return <div className="page"><p>Agent not found.</p></div>

  const isNewAgent = Date.now() - new Date(agent.created_at).getTime() < 5 * 60 * 1000
  const hasSchedule = !!(agent as Agent & { schedule?: unknown }).schedule
  // Telegram is user-level only (no telegram_chat_id on agent object).
  // No API exists to check user-level telegram status from this page, so we
  // always show the warning — it guides new users who haven't connected yet.
  const telegramConnected = false

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>{agent.display_name}</h1>
          <p style={{ color: 'var(--text-dim)', fontSize: 13, marginTop: 4 }}>{agent.purpose}</p>
        </div>
        <span className={`badge ${agent.is_active ? 'badge-active' : 'badge-inactive'}`}>
          {agent.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>

      {showActivationCard && (messages.length === 0 || isNewAgent) && (
        <div className="activation-card">
          <button className="activation-card-close" onClick={() => setShowActivationCard(false)}>×</button>
          <div className="activation-card-header">
            <span className="activation-check">✓</span>
            <strong>{agent.display_name} is live</strong>
          </div>
          <div className="activation-card-body">
            <p>
              {hasSchedule
                ? 'Scheduled check-ins are active. Your agent will message you at your configured time.'
                : 'No schedule set. Configure check-ins in the Settings tab.'}
            </p>
            {!telegramConnected && (
              <div className="activation-telegram-warning">
                <span>⚠️</span>
                <span>Telegram not connected — your agent can't message you until you <a href="/settings">connect Telegram</a>.</span>
              </div>
            )}
            <button
              className="btn btn-sm"
              onClick={() => {
                setTab('chat')
                setTimeout(() => chatInputRef.current?.focus(), 50)
              }}
            >
              Send a test message →
            </button>
          </div>
        </div>
      )}

      <div className="card" style={{ padding: 0, marginBottom: 24 }}>
        <p style={{ padding: '16px 24px', color: 'var(--text)', fontSize: 13, borderBottom: '1px solid var(--border)' }}>
          To connect this agent to Telegram: add <strong style={{ color: 'var(--accent)' }}>@JunctionAIBot</strong> to a group, then send <code>/link {agent.slug}</code>
        </p>
      </div>

      <div className="tabs">
        {(['chat', 'memory', 'files', 'settings'] as Tab[]).map(t => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'chat' && (
        <div className="chat-container">
          <div className="chat-messages">
            {messages.length === 0 && (
              <p style={{ color: 'var(--text-dim)', textAlign: 'center', marginTop: 40 }}>
                Send a test message to chat with {agent.display_name}
              </p>
            )}
            {messages.map(msg => (
              <div key={msg.id} className={`chat-message ${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {sending && (
              <div className="chat-message assistant" style={{ opacity: 0.5 }}>Thinking...</div>
            )}
          </div>
          <div className="chat-input">
            <input
              ref={chatInputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={`Message ${agent.display_name}...`}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              disabled={sending}
            />
            <button className="btn btn-primary" onClick={sendMessage} disabled={sending || !input.trim()}>
              Send
            </button>
          </div>
        </div>
      )}

      {tab === 'memory' && (
        <div>
          <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>What {agent.display_name} knows about you</h3>
          {facts.length === 0 ? (
            <div className="memory-empty">
              <p>No facts learned yet.</p>
              <p className="text-secondary">Chat with {agent.display_name} and they'll start remembering things about you automatically.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {facts.map(fact => {
                const confidencePct = Math.round(fact.confidence * 100)
                return (
                  <div key={fact.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <p style={{ color: 'var(--text-h)', fontSize: 14 }}>{fact.fact}</p>
                        {fact.category && (
                          <span className={`badge badge-category badge-${fact.category.toLowerCase()}`}>
                            {fact.category}
                          </span>
                        )}
                      </div>
                      <span className="fact-confidence">{confidenceLabel(confidencePct)}</span>
                    </div>
                    <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => forgetFact(fact.id)}>
                      Forget
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {tab === 'files' && (
        <div>
          <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Agent Identity (AGENT.md)</h3>
          <textarea value={agent.agent_md} readOnly style={{ width: '100%', minHeight: 300, fontFamily: 'monospace', fontSize: 13 }} />

          {agent.knowledge_md && (
            <>
              <h3 style={{ color: 'var(--text-h)', margin: '24px 0 16px' }}>Knowledge</h3>
              <textarea value={agent.knowledge_md} readOnly style={{ width: '100%', minHeight: 200, fontFamily: 'monospace', fontSize: 13 }} />
            </>
          )}
        </div>
      )}

      {tab === 'settings' && (
        <div>
          <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Agent Settings</h3>
          <div className="card" style={{ marginBottom: 16 }}>
            <p style={{ color: 'var(--text-h)', fontWeight: 500 }}>Model: {agent.model}</p>
            <p style={{ color: 'var(--text-dim)', fontSize: 13, marginTop: 4 }}>Slug: {agent.slug}</p>
          </div>

          <div className="settings-section">
            <h3>Agent Status</h3>
            <p className="settings-hint">Paused agents won't send scheduled messages. You can resume anytime.</p>
            <button
              className={`btn ${agent.is_active ? 'btn-secondary' : 'btn-primary'}`}
              onClick={handleToggleActive}
              disabled={toggling}
            >
              {toggling ? 'Updating...' : agent.is_active ? 'Pause agent' : 'Resume agent'}
            </button>
          </div>

          <button className="btn btn-danger" onClick={async () => {
            if (confirm(`Delete ${agent.display_name}? This cannot be undone.`)) {
              await api.deleteAgent(agent.id)
              navigate('/dashboard')
            }
          }}>
            Delete Agent
          </button>
        </div>
      )}
    </div>
  )
}
