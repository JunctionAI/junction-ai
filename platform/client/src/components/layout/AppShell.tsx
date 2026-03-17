import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../lib/auth'
import './AppShell.css'

export function AppShell() {
  const { user, signOut } = useAuth()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <img src="/logo-dark.png" alt="Junction AI" className="logo-img" />
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Dashboard
          </NavLink>
          <NavLink to="/agents/new" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            + New Agent
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Settings
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
