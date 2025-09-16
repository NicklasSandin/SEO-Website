import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation.jsx'
import LandingPage from './components/LandingPage.jsx'
import ServicePage from './components/ServicePage.jsx'
import PricingPage from './components/PricingPage.jsx'
import Dashboard from './components/Dashboard.jsx'
import './App.css'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-white">
        <Navigation />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/service" element={<ServicePage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
