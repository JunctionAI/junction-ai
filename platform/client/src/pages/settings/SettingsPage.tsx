import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../lib/auth'
import { api } from '../../lib/api'

export function SettingsPage() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [usage, setUsage] = useState({ total_input_tokens: 0, total_output_tokens: 0, total_cost_usd: 0, total_requests: 0 })
  const [deleting, setDeleting] = useState(false)

  const deleteAccount = async () => {
    if (!confirm('Delete your account? This cannot be undone.')) return
    setDeleting(true)
    try {
      await api.deleteAccount()
      await signOut()
      navigate('/login')
    } catch (err) {
      alert('Failed to delete account. Try again.')
      setDeleting(false)
    }
  }

  useEffect(() => {
    api.getUsage().then(setUsage).catch(console.error)
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <h1>Settings</h1>
      </div>

      <div style={{ display: 'grid', gap: 24, maxWidth: 600 }}>
        <div className="card">
          <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Account</h3>
          <div className="field">
            <label>Email</label>
            <input value={user?.email || ''} disabled />
          </div>
        </div>

        <div className="card">
          <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Telegram</h3>
          <p style={{ color: 'var(--text)', fontSize: 14, marginBottom: 12 }}>
            Connected via @JunctionAIBot
          </p>
          <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>
            To connect an agent: add @JunctionAIBot to a Telegram group, then send /link [agent-slug]
          </p>
        </div>

        <div className="card">
          <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Usage This Month</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>Requests</p>
              <p style={{ color: 'var(--text-h)', fontSize: 24, fontWeight: 600 }}>{usage.total_requests.toLocaleString()}</p>
            </div>
            <div>
              <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>Cost</p>
              <p style={{ color: 'var(--text-h)', fontSize: 24, fontWeight: 600 }}>${usage.total_cost_usd.toFixed(2)}</p>
            </div>
            <div>
              <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>Input Tokens</p>
              <p style={{ color: 'var(--text-h)', fontSize: 16 }}>{(usage.total_input_tokens / 1000).toFixed(1)}K</p>
            </div>
            <div>
              <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>Output Tokens</p>
              <p style={{ color: 'var(--text-h)', fontSize: 16 }}>{(usage.total_output_tokens / 1000).toFixed(1)}K</p>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ color: 'var(--text-h)', marginBottom: 16 }}>Billing</h3>
          <p style={{ color: 'var(--text)', fontSize: 14, marginBottom: 12 }}>
            Plan: <strong style={{ color: 'var(--accent)' }}>Free</strong>
          </p>
          <p style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 16 }}>
            3 agents, 100 messages/month
          </p>
          <button className="btn btn-primary">Upgrade Plan</button>
        </div>

        <div className="card" style={{ borderColor: 'rgba(239,68,68,0.3)' }}>
          <h3 style={{ color: '#ef4444', marginBottom: 8 }}>Danger Zone</h3>
          <p style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 16 }}>
            Permanently delete your account and all data. Cannot be undone.
          </p>
          <button
            onClick={deleteAccount}
            disabled={deleting}
            style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.4)', padding: '8px 16px', borderRadius: 8, fontSize: 13, cursor: 'pointer' }}
          >
            {deleting ? 'Deleting...' : 'Delete Account'}
          </button>
        </div>
      </div>
    </div>
  )
}
