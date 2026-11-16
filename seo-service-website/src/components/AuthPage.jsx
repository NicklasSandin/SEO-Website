import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { useAuth } from '@/lib/auth.jsx'

const PLAN_LIMITS = { starter: 10, professional: 25, enterprise: 50 }

export default function AuthPage({ mode }) {
  const isRegister = mode === 'register'
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [params] = useSearchParams()
  const initialPlan = PLAN_LIMITS[params.get('plan')] ? params.get('plan') : 'starter'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [plan, setPlan] = useState(initialPlan)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      if (isRegister) await register({ email, password, plan })
      else await login(email, password)
      navigate(location.state?.from || '/dashboard', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-[70vh] bg-gray-50 py-16">
      <div className="container mx-auto px-4 max-w-md">
        <div className="bg-white rounded-2xl shadow p-8">
          <h1 className="text-2xl font-bold mb-6">{isRegister ? 'Create an account' : 'Sign in'}</h1>
          <form onSubmit={submit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                required
                minLength={isRegister ? 10 : undefined}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              {isRegister && <p className="text-sm text-gray-500">At least 10 characters.</p>}
            </div>
            {isRegister && (
              <div className="space-y-2">
                <Label htmlFor="plan">Plan</Label>
                <select
                  id="plan"
                  value={plan}
                  onChange={(e) => setPlan(e.target.value)}
                  className="w-full h-9 rounded-md border border-gray-300 bg-white px-3 text-sm"
                >
                  {Object.entries(PLAN_LIMITS).map(([id, limit]) => (
                    <option key={id} value={id}>
                      {id[0].toUpperCase() + id.slice(1)}: up to {limit} keywords per project
                    </option>
                  ))}
                </select>
                <p className="text-sm text-gray-500">There is no billing. The plan only sets the keyword limit.</p>
              </div>
            )}
            {error && (
              <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
                {error}
              </p>
            )}
            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700" disabled={busy}>
              {busy ? 'Please wait...' : isRegister ? 'Create account' : 'Sign in'}
            </Button>
          </form>
          <p className="text-sm text-gray-600 mt-6">
            {isRegister ? (
              <>
                Already have an account? <Link className="text-blue-600 underline" to="/login">Sign in</Link>
              </>
            ) : (
              <>
                New here? <Link className="text-blue-600 underline" to="/register">Create an account</Link>
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}
