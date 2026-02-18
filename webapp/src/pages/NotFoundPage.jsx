import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <section className="panel">
      <h2>404</h2>
      <p className="muted">The page you requested was not found.</p>
      <Link className="btn ghost" to="/">Go Home</Link>
    </section>
  )
}
