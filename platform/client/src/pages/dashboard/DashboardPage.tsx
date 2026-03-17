import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, type Agent } from '../../lib/api'

export function DashboardPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.getAgents()
      .then(setAgents)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="page"><p style={{ color: 'var(--text-dim)' }}>Loading agents...</p></div>

  return (
    <div className="page">
      <div className="page-header">
        <h1>Your Agents</h1>
        <Link to="/agents/new" className="btn btn-primary">+ New Agent</Link>
      </div>

      {agents.length === 0 ? (
        <div className="welcome-state">
          <div className="welcome-header">
            <h2>Your agents are ready to be created</h2>
            <p>Your profile is built. Now create your first agent — they'll check in with you daily via Telegram.</p>
          </div>
          <div className="suggested-agents">
            <p className="suggested-label">Suggested first agents:</p>
            <div className="suggestion-grid">
              {[
                { domain: 'Work/Business', emoji: '💼', name: 'Business Coach', desc: 'Daily accountability on revenue, growth, and execution' },
                { domain: 'Health & Fitness', emoji: '⚡', name: 'Health Coach', desc: 'Morning check-ins on training, nutrition, and energy' },
                { domain: 'Mental Wellbeing', emoji: '🧠', name: 'Mindset Coach', desc: 'Evening reflections and stress management' },
              ].map(s => (
                <div
                  key={s.domain}
                  className="suggestion-card"
                  onClick={() => navigate(`/agents/new?domain=${encodeURIComponent(s.domain)}&name=${encodeURIComponent(s.name)}`)}
                >
                  <span className="suggestion-emoji">{s.emoji}</span>
                  <div>
                    <strong>{s.name}</strong>
                    <p>{s.desc}</p>
                  </div>
                  <span className="suggestion-arrow">→</span>
                </div>
              ))}
            </div>
            <button className="btn btn-primary" onClick={() => navigate('/agents/new')} style={{ marginTop: '1.5rem' }}>
              + Create a custom agent
            </button>
          </div>
        </div>
      ) : (
        <div className="grid-3">
          {agents.map(agent => (
            <Link key={agent.id} to={`/agents/${agent.id}`} style={{ textDecoration: 'none' }}>
              <div className="card" style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <h3 style={{ color: 'var(--text-h)', fontSize: 16, fontWeight: 600 }}>
                    {agent.display_name}
                  </h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {agent.is_active === false && (
                      <span className="badge badge-paused">Paused</span>
                    )}
                    <span className={`badge ${agent.is_active ? 'badge-active' : 'badge-inactive'}`}>
                      {agent.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
                <p style={{ color: 'var(--text)', fontSize: 13, lineHeight: 1.5, marginBottom: 12 }}>
                  {agent.purpose}
                </p>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-dim)' }}>
                  <span>{agent.model.replace('claude-', '').replace('-4-6', '')}</span>
                  <span>Created {new Date(agent.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
