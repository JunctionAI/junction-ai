import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { supabase } from './supabase'
import type { User, Session } from '@supabase/supabase-js'

interface AuthState {
  user: User | null
  session: Session | null
  loading: boolean
  onboardingComplete: boolean | null  // null = still checking
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthState>({
  user: null,
  session: null,
  loading: true,
  onboardingComplete: null,
  signOut: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [onboardingComplete, setOnboardingComplete] = useState<boolean | null>(null)

  // Whenever user changes, fetch their onboarding status
  useEffect(() => {
    if (!user) {
      setOnboardingComplete(null)
      return
    }
    // Safety timeout — never block the UI forever
    const timeout = setTimeout(() => setOnboardingComplete(false), 3000)
    const fetchStatus = async () => {
      try {
        const { data } = await supabase
          .from('users')
          .select('onboarding_complete')
          .eq('id', user.id)
          .single()
        clearTimeout(timeout)
        setOnboardingComplete(data?.onboarding_complete ?? false)
      } catch {
        clearTimeout(timeout)
        setOnboardingComplete(false)
      }
    }
    void fetchStatus()
    return () => clearTimeout(timeout)
  }, [user?.id])

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    const timeout = setTimeout(async () => {
      const { data: { session } } = await supabase.auth.getSession()
      setSession(s => s ?? session)
      setUser(u => u ?? session?.user ?? null)
      setLoading(false)
    }, 500)

    return () => {
      subscription.unsubscribe()
      clearTimeout(timeout)
    }
  }, [])

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, onboardingComplete, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
