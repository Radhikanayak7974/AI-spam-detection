import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import DashboardLayout from './layouts/DashboardLayout'
import ProtectedRoute from './components/ProtectedRoute'

// Public Pages
import LandingPage from './pages/LandingPage'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'

// Dashboard Pages
import Overview from './pages/Overview'
import GmailInbox from './pages/GmailInbox'
import SpamEmails from './pages/SpamEmails'
import SafeEmails from './pages/SafeEmails'
import FeedbackManagement from './pages/FeedbackManagement'
import ModelPerformance from './pages/ModelPerformance'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'

export default function App() {
  // Dark mode persisted in localStorage
  const [darkMode, setDarkMode] = useState(() => {
    const stored = localStorage.getItem('darkMode')
    if (stored !== null) return stored === 'true'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    localStorage.setItem('darkMode', darkMode)
  }, [darkMode])

  // Helper to wrap dashboard routes in both Protection and Dashboard Layout
  const renderDashboardPage = (Component) => (
    <ProtectedRoute>
      <DashboardLayout darkMode={darkMode} setDarkMode={setDarkMode}>
        <Component />
      </DashboardLayout>
    </ProtectedRoute>
  )

  return (
    <Routes>
      {/* ── Public SaaS Flow ───────────────────────────────────────── */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<SignIn />} />
      <Route path="/register" element={<SignUp />} />

      {/* ── Dashboard Navigation Flow ──────────────────────────────── */}
      <Route path="/dashboard" element={<Navigate to="/overview" replace />} />
      <Route path="/overview" element={renderDashboardPage(Overview)} />
      <Route path="/inbox" element={renderDashboardPage(GmailInbox)} />
      <Route path="/spam" element={renderDashboardPage(SpamEmails)} />
      <Route path="/safe" element={renderDashboardPage(SafeEmails)} />
      <Route path="/feedback" element={renderDashboardPage(FeedbackManagement)} />
      <Route path="/model-performance" element={renderDashboardPage(ModelPerformance)} />
      <Route path="/analytics" element={renderDashboardPage(Analytics)} />
      <Route path="/settings" element={renderDashboardPage(Settings)} />

      {/* ── Fallback ────────────────────────────────────────────────── */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
