import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../../lib/supabase'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignUp, setIsSignUp] = useState(true)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [checkEmail, setCheckEmail] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isSignUp) {
        const { data, error } = await supabase.auth.signUp({ email, password })
        if (error) throw error
        // If session is returned, email confirmation is disabled — go straight to onboarding
        if (data.session) {
          navigate('/onboarding')
        } else {
          // Email confirmation required — show check email message
          setCheckEmail(true)
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) throw error
        navigate('/dashboard')
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    })
    if (error) setError(error.message)
  }

  if (checkEmail) {
    return (
      <div className="auth-page">
        <div className="auth-card card" style={{ textAlign: 'center' }}>
          <img src="/logomark.png" alt="Junction AI" style={{ height: 40, marginBottom: 24 }} />
          <h1>Check your email</h1>
          <p className="subtitle" style={{ marginTop: 12 }}>
            We sent a confirmation link to <strong>{email}</strong>.<br />
            Click it to activate your account, then come back and sign in.
          </p>
          <button onClick={() => { setCheckEmail(false); setIsSignUp(false) }}
            className="btn btn-gradient" style={{ marginTop: 24, width: '100%', justifyContent: 'center' }}>
            Back to sign in
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <img src="/logomark.png" alt="Junction AI" style={{ height: 40, marginBottom: 16 }} />
        </div>
        <h1>{isSignUp ? 'Create account' : 'Welcome back'}</h1>
        <p className="subtitle">
          {isSignUp ? 'Start building your AI agents' : 'Sign in to your Junction AI account'}
        </p>

        <button className="btn btn-secondary" onClick={handleGoogleLogin} style={{ width: '100%', justifyContent: 'center', marginBottom: 20 }}>
          Continue with Google
        </button>

        <div style={{ textAlign: 'center', color: 'var(--text-dim)', fontSize: 12, margin: '16px 0', position: 'relative' }}>
          <span style={{ background: 'var(--bg-card)', padding: '0 12px', position: 'relative', zIndex: 1 }}>or</span>
          <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: 1, background: 'var(--border)' }} />
        </div>

        {error && (
          <div style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', padding: '10px 14px', borderRadius: 'var(--radius)', fontSize: 13, marginBottom: 16 }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Min 6 characters" required minLength={6} />
          </div>
          <button type="submit" className="btn btn-gradient" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
            {loading ? 'Loading...' : isSignUp ? 'Create account' : 'Sign in'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--text-dim)' }}>
          {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button onClick={() => { setIsSignUp(!isSignUp); setError('') }} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit' }}>
            {isSignUp ? 'Sign in' : 'Sign up'}
          </button>
        </p>

        <Link to="/" style={{ display: 'block', textAlign: 'center', marginTop: 16, fontSize: 12, color: 'var(--text-dim)' }}>
          Back to home
        </Link>
      </div>
    </div>
  )
}
