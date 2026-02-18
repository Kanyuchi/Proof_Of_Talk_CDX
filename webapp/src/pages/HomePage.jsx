import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <section>
      <div className="hero panel">
        <p className="chip">AI-Powered Matchmaking Engine</p>
        <h1>The Right Meeting Changes Everything</h1>
        <p className="lead">
          2,500 decision-makers, $18T in assets, and explainable recommendations for transaction-ready intros.
        </p>
        <div className="row center">
          <Link to="/attendees" className="btn primary">View Matches</Link>
          <Link to="/dashboard" className="btn ghost">Organizer Dashboard</Link>
        </div>
      </div>
    </section>
  )
}
