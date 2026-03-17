import { Link } from 'react-router-dom'

export function LandingPage() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 20px', textAlign: 'center' }}>
      <div style={{ marginBottom: 24 }}>
        <img src="/logo-dark.png" alt="Junction AI" style={{ height: 36 }} />
      </div>
      <h1 style={{ fontSize: 48, color: 'var(--text-h)', fontWeight: 600, marginBottom: 16, lineHeight: 1.1 }}>
        Your <span className="gt">AI Operating Layer</span>
      </h1>
      <p style={{ fontSize: 18, color: 'var(--text)', maxWidth: 520, marginBottom: 40, lineHeight: 1.6 }}>
        Create personal AI agents that learn about you, work on a schedule, and communicate via Telegram.
        No coding. No API keys. Just tell them what to do.
      </p>
      <div style={{ display: 'flex', gap: 12 }}>
        <Link to="/login" className="btn btn-gradient btn-lg">
          Get Started
        </Link>
      </div>
      <p style={{ marginTop: 24, fontSize: 13, color: 'var(--text-dim)' }}>
        Free to start. No credit card required.
      </p>
    </div>
  )
}
