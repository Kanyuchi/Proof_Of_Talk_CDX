import { Navigate, Route, Routes } from 'react-router-dom'
import ConciergeWidget from './components/ConciergeWidget'
import Layout from './components/Layout'
import AttendeesPage from './pages/AttendeesPage'
import AuthPage from './pages/AuthPage'
import DashboardPage from './pages/DashboardPage'
import HomePage from './pages/HomePage'
import MessagesPage from './pages/MessagesPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/attendees" element={<AttendeesPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/messages" element={<MessagesPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <ConciergeWidget />
    </Layout>
  )
}
