import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Plus } from 'lucide-react'
import { api } from '@/lib/api.js'
import { useAuth } from '@/lib/auth.jsx'

const LIMITS = { starter: 10, professional: 25, enterprise: 50 }

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : 'never'
}

export default function Dashboard() {
  const { user } = useAuth()
  const [projects, setProjects] = useState(null)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({ name: '', website_url: '', keywords: '', location_name: 'Sweden', language_code: 'sv' })
  const [formError, setFormError] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    try {
      setProjects((await api.projects()).projects)
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  const create = async (event) => {
    event.preventDefault()
    setBusy(true)
    setFormError(null)
    try {
      await api.createProject(form)
      setForm({ ...form, name: '', website_url: '', keywords: '' })
      await load()
    } catch (err) {
      setFormError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">Your projects</h1>
          <p className="text-gray-600">
            Signed in as {user.email}. Plan: {user.plan} (up to {LIMITS[user.plan]} keywords per project).
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 grid lg:grid-cols-2 gap-8">
        <section>
          <h2 className="text-xl font-semibold mb-4">Projects</h2>
          {error && <p role="alert" className="text-red-700 mb-4">{error}</p>}
          {projects === null && !error && <p className="text-gray-600">Loading...</p>}
          {projects && projects.length === 0 && (
            <p className="bg-white rounded-lg shadow-sm p-6 text-gray-600">
              No projects yet. Add a website and its keywords with the form to get started.
            </p>
          )}
          <div className="space-y-4">
            {projects?.map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="block bg-white rounded-lg shadow-sm p-5 hover:shadow-md transition-shadow"
              >
                <h3 className="font-semibold text-gray-900">{project.name}</h3>
                <p className="text-sm text-gray-600">{project.domain}</p>
                <p className="text-sm text-gray-500 mt-1">
                  {project.keywords.length} keywords. Last analysis: {formatDate(project.last_analyzed_at)}
                </p>
              </Link>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-4">New project</h2>
          <form onSubmit={create} className="bg-white rounded-lg shadow-sm p-6 space-y-5">
            <div className="space-y-2">
              <Label htmlFor="name">Project name</Label>
              <Input id="name" name="name" required maxLength={100} value={form.name} onChange={update} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="website_url">Website</Label>
              <Input id="website_url" name="website_url" required placeholder="https://yourwebsite.com" value={form.website_url} onChange={update} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="keywords">Keywords</Label>
              <Textarea id="keywords" name="keywords" required rows={3} placeholder="plumber malmö, emergency plumbing" value={form.keywords} onChange={update} />
              <p className="text-sm text-gray-500">Separate with commas. Up to {LIMITS[user.plan]} on your plan.</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="location_name">Country or location</Label>
                <Input id="location_name" name="location_name" value={form.location_name} onChange={update} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="language_code">Language code</Label>
                <Input id="language_code" name="language_code" value={form.language_code} onChange={update} />
              </div>
            </div>
            {formError && (
              <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
                {formError}
              </p>
            )}
            <Button type="submit" disabled={busy} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4" />
              {busy ? 'Creating...' : 'Create project'}
            </Button>
          </form>
        </section>
      </div>
    </div>
  )
}
