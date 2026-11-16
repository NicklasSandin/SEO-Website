import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Navigation from './components/Navigation.jsx'
import StatusBanner from './components/StatusBanner.jsx'
import LandingPage from './components/LandingPage.jsx'
import ServicePage from './components/ServicePage.jsx'
import PricingPage from './components/PricingPage.jsx'
import AuthPage from './components/AuthPage.jsx'
import Dashboard from './components/Dashboard.jsx'
import ProjectPage from './components/ProjectPage.jsx'
import ReportPage from './components/ReportPage.jsx'
import { AuthProvider, useAuth } from './lib/auth.jsx'
import './App.css'

function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <p className="container mx-auto px-4 py-16 text-gray-600">Loading...</p>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return children
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="min-h-screen bg-white">
          <StatusBanner />
          <Navigation />
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/service" element={<ServicePage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/login" element={<AuthPage mode="login" />} />
            <Route path="/register" element={<AuthPage mode="register" />} />
            <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
            <Route path="/projects/:projectId" element={<RequireAuth><ProjectPage /></RequireAuth>} />
            <Route path="/reports/:reportId" element={<RequireAuth><ReportPage /></RequireAuth>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  )
}

export default App
