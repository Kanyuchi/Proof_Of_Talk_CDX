import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">POT Matchmaker</Link>
        <nav className="nav-links">
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/attendees">Attendees</NavLink>
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/messages">Messages</NavLink>
        </nav>
        <div className="auth-bar">
          {user ? (
            <>
              <span className="muted">{user.full_name}</span>
              <button className="btn ghost" onClick={logout}>Logout</button>
            </>
          ) : (
            <Link className="btn ghost" to="/auth">Login</Link>
          )}
        </div>
      </header>
      <main className="page">{children}</main>
    </div>
  )
}
