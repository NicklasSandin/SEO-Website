// Thin fetch wrapper for the Siktio API. Requests go to the same origin ("/api/..."):
// the Flask app serves the built site, and `npm run dev` proxies /api to it (see vite.config.js).
// The X-Requested-With header is required by the backend on every state-changing request.

export class ApiError extends Error {
  constructor(message, { status, code, field } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.field = field
  }
}

async function request(method, path, body) {
  const headers = { Accept: 'application/json', 'X-Requested-With': 'siktio-web' }
  const options = { method, headers, credentials: 'same-origin' }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }
  let response
  try {
    response = await fetch(`/api${path}`, options)
  } catch {
    throw new ApiError('Could not reach the server. Is the backend running?', { status: 0, code: 'network' })
  }
  if (response.status === 204) return null
  let data = null
  try {
    data = await response.json()
  } catch {
    // not JSON; handled below
  }
  if (!response.ok) {
    throw new ApiError(data?.error || `Request failed (${response.status}).`, {
      status: response.status,
      code: data?.code,
      field: data?.field,
    })
  }
  return data
}

export const api = {
  health: () => request('GET', '/health'),
  me: () => request('GET', '/auth/me'),
  register: (payload) => request('POST', '/auth/register', payload),
  login: (payload) => request('POST', '/auth/login', payload),
  logout: () => request('POST', '/auth/logout'),
  projects: () => request('GET', '/projects'),
  createProject: (payload) => request('POST', '/projects', payload),
  dashboard: (id) => request('GET', `/projects/${id}/dashboard`),
  deleteProject: (id) => request('DELETE', `/projects/${id}`),
  analyze: (id) => request('POST', `/projects/${id}/analyze`),
  createReport: (id) => request('POST', `/projects/${id}/reports`, {}),
  report: (id) => request('GET', `/reports/${id}`),
  reviewReport: (id) => request('POST', `/reports/${id}/review`),
}
