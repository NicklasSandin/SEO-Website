import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Menu, X, TrendingUp } from 'lucide-react'
import { useAuth } from '@/lib/auth.jsx'

export default function Navigation() {
  const [isOpen, setIsOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const links = [
    { to: '/', label: 'Home', end: true },
    { to: '/service', label: 'How it works' },
    { to: '/pricing', label: 'Plans' },
    ...(user ? [{ to: '/dashboard', label: 'Dashboard' }] : []),
  ]
  const linkClass = ({ isActive }) =>
    `text-sm font-medium transition-colors ${isActive ? 'text-blue-600' : 'text-gray-600 hover:text-gray-900'}`

  const signOut = async () => {
    setIsOpen(false)
    await logout()
    navigate('/')
  }

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-900 rounded-lg flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-yellow-400" />
            </div>
            <span className="text-xl font-bold text-blue-900">Siktio</span>
          </Link>

          <div className="hidden md:flex items-center space-x-8">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
                {l.label}
              </NavLink>
            ))}
            {user ? (
              <Button size="sm" variant="outline" onClick={signOut}>
                Sign out
              </Button>
            ) : (
              <>
                <NavLink to="/login" className={linkClass}>
                  Sign in
                </NavLink>
                <Link to="/register">
                  <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                    Create account
                  </Button>
                </Link>
              </>
            )}
          </div>

          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-gray-600 hover:text-gray-900"
              aria-label={isOpen ? 'Close menu' : 'Open menu'}
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {isOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <div className="flex flex-col space-y-4">
              {links.map((l) => (
                <NavLink key={l.to} to={l.to} end={l.end} className={linkClass} onClick={() => setIsOpen(false)}>
                  {l.label}
                </NavLink>
              ))}
              {user ? (
                <Button size="sm" variant="outline" className="w-fit" onClick={signOut}>
                  Sign out
                </Button>
              ) : (
                <>
                  <NavLink to="/login" className={linkClass} onClick={() => setIsOpen(false)}>
                    Sign in
                  </NavLink>
                  <Link to="/register" onClick={() => setIsOpen(false)}>
                    <Button size="sm" className="bg-blue-600 hover:bg-blue-700 w-fit">
                      Create account
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
