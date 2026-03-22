import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/auth'
import { AppShell } from './components/layout/AppShell'
import { LoginPage } from './pages/auth/LoginPage'
import { AuthCallback } from './pages/auth/AuthCallback'
import { OnboardingWizard } from './pages/onboarding/OnboardingWizard'
import { DashboardPage } from './pages/dashboard/DashboardPage'
import { AgentCreateWizard } from './pages/agents/AgentCreateWizard'
import { AgentDetailPage } from './pages/agents/AgentDetailPage'
import { SettingsPage } from './pages/settings/SettingsPage'
import { IntegrationsPage } from './pages/integrations/IntegrationsPage'
import { TidefixDashboard } from './pages/tidefix/TidefixDashboard'
import { CompanionsDashboard } from './pages/companions/CompanionsDashboard'
import { LandingPage } from './pages/LandingPage'
import './App.css'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading, onboardingComplete } = useAuth()
  const location = useLocation()
  if (loading || (user && onboardingComplete === null)) return <div className="loading-screen">Loading...</div>
  if (!user) return <Navigate to="/login" />
  if (onboardingComplete === false && !location.pathname.startsWith('/onboarding')) return <Navigate to="/onboarding" />
  return <>{children}</>
}

function AppRoutes() {
  const { user, loading, onboardingComplete } = useAuth()
  if (loading) return <div className="loading-screen">Loading...</div>

  // Only redirect away from login/landing if already fully authenticated
  // Never silently redirect to /onboarding from the login page — ProtectedRoute handles that after sign-in
  const alreadyAuthed = user && onboardingComplete === true

  return (
    <Routes>
      <Route path="/" element={alreadyAuthed ? <Navigate to="/agents" /> : <LandingPage />} />
      <Route path="/login" element={alreadyAuthed ? <Navigate to="/agents" /> : <LoginPage />} />
      <Route path="/dashboard" element={<Navigate to="/agents" replace />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/onboarding" element={
        <ProtectedRoute><OnboardingWizard /></ProtectedRoute>
      } />
      <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
        <Route path="/agents" element={<DashboardPage />} />
        <Route path="/agents/new" element={<AgentCreateWizard />} />
        <Route path="/agents/:id" element={<AgentDetailPage />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/tidefix" element={<TidefixDashboard />} />
        <Route path="/companions" element={<CompanionsDashboard />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
