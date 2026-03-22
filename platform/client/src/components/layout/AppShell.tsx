import { useEffect } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../lib/auth'
import './AppShell.css'

export function AppShell() {
  const { user, signOut } = useAuth()

  // Belt-and-suspenders: inline styles beat any stylesheet, including index.css
  useEffect(() => {
    const html = document.documentElement
    const root = document.getElementById('root')
    html.style.overflow = 'hidden'
    html.style.overscrollBehavior = 'none'
    if (root) {
      root.style.minHeight = '0'
      root.style.height = '100%'
      root.style.overflow = 'hidden'
    }
    return () => {
      html.style.overflow = ''
      html.style.overscrollBehavior = ''
      if (root) {
        root.style.minHeight = ''
        root.style.height = ''
        root.style.overflow = ''
      }
    }
  }, [])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <img src="/logo-dark.png" alt="Junction AI" className="logo-img" />
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/agents" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Agents
          </NavLink>
          <NavLink to="/integrations" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Integrations
            <span className="nav-badge">Soon</span>
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Settings
          </NavLink>
          <NavLink to="/tidefix" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            TIDEFIX
          </NavLink>
          <NavLink to="/companions" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Companions
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-email">{user?.email}</span>
          </div>
          <button className="btn-signout" onClick={signOut}>Sign out</button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
