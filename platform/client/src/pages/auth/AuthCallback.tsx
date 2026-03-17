import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../../lib/supabase'

export function AuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    // Subscribe FIRST — navigation only happens once auth state is confirmed in context.
    // This avoids the race where navigate('/dashboard') fires before React has re-rendered
    // with the new user, causing ProtectedRoute to bounce back to /login.
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) {
        subscription.unsubscribe()
        clearTimeout(fallback)
        navigate('/dashboard', { replace: true })
      }
    })

    const fallback = setTimeout(() => {
      subscription.unsubscribe()
      navigate('/login', { replace: true })
    }, 8000)

    // Trigger PKCE code exchange if present — will fire onAuthStateChange above on success
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    if (code) {
      supabase.auth.exchangeCodeForSession(code).then(({ error }) => {
        if (error) {
          console.error('Code exchange failed:', error)
          subscription.unsubscribe()
          clearTimeout(fallback)
          navigate('/login', { replace: true })
        }
      })
    }

    return () => {
      subscription.unsubscribe()
      clearTimeout(fallback)
    }
  }, [navigate])

  return <div className="loading-screen">Signing you in...</div>
}
