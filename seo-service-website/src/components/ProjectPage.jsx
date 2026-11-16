import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { FileText, RefreshCw, Trash2 } from 'lucide-react'
import { api } from '@/lib/api.js'
import SampleBanner, { SampleTag } from './SampleBanner.jsx'

const SEVERITY_STYLE = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  warning: 'bg-amber-100 text-amber-800 border-amber-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
}

function Stat({ label, value }) {
  return (
    <div className="bg-white p-5 rounded-lg shadow-sm">
      <p className="text-sm font-medium text-gray-600">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value ?? 'n/a'}</p>
    </div>
  )
}

function Change({ rank, previous }) {
  if (rank == null || previous == null) return <span className="text-gray-400">n/a</span>
  if (rank === previous) return <span className="text-gray-600">no change</span>
  const up = rank < previous
  return (
    <span className={up ? 'text-green-700' : 'text-red-700'}>
      {up ? 'up' : 'down'} {Math.abs(previous - rank)} (was {previous})
    </span>
  )
}

export default function ProjectPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null)
  const [notice, setNotice] = useState(null)

  const load = useCallback(async () => {
    try {
      setData(await api.dashboard(projectId))
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }, [projectId])

  useEffect(() => {
    load()
  }, [load])

  const run = async (kind, action, doneMessage) => {
    setBusy(kind)
    setNotice(null)
    try {
      await action()
      await load()
      setNotice({ ok: true, text: doneMessage })
    } catch (err) {
      setNotice({ ok: false, text: err.message })
    } finally {
      setBusy(null)
    }
  }

  const remove = async () => {
    if (!window.confirm('Delete this project with all its analyses and reports?')) return
    try {
      await api.deleteProject(projectId)
      navigate('/dashboard')
    } catch (err) {
      setNotice({ ok: false, text: err.message })
    }
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-16">
        <p role="alert" className="text-red-700 mb-4">{error}</p>
        <Link className="text-blue-600 underline" to="/dashboard">Back to projects</Link>
      </div>
    )
  }
  if (!data) return <p className="container mx-auto px-4 py-16 text-gray-600">Loading...</p>

  const { project, latest_analysis: analysis, stats, reports, data_source: source } = data
  const result = analysis?.result
  const depth = result?.serp_depth

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-6 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
          <div>
            <Link className="text-sm text-blue-600 underline" to="/dashboard">All projects</Link>
            <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
            <p className="text-gray-600">
              {project.website_url} &middot; {project.location_name} &middot; language {project.language_code}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={() => run('analyze', () => api.analyze(project.id), 'Analysis finished.')}
              disabled={busy !== null}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <RefreshCw className="h-4 w-4" />
              {busy === 'analyze' ? 'Running analysis...' : 'Run analysis'}
            </Button>
            <Button
              variant="outline"
              onClick={() => run('report', () => api.createReport(project.id), 'Report created.')}
              disabled={busy !== null || !analysis}
              title={analysis ? '' : 'Run an analysis first'}
            >
              <FileText className="h-4 w-4" />
              {busy === 'report' ? 'Writing report...' : 'Generate report'}
            </Button>
            <Button variant="ghost" onClick={remove} aria-label="Delete project">
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 space-y-8">
        {notice && (
          <p
            role={notice.ok ? 'status' : 'alert'}
            className={`rounded border p-3 text-sm ${notice.ok ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}
          >
            {notice.text}
          </p>
        )}

        {source.is_sample && <SampleBanner />}

        {!analysis && (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <p className="text-gray-700 mb-2">No analysis has been run for this project yet.</p>
            <p className="text-sm text-gray-500">
              Press &quot;Run analysis&quot; to fetch positions for {project.keywords.length} keywords
              {source.is_sample ? ' (this will produce sample data).' : ' from DataForSEO. Each keyword is a separate paid API call.'}
            </p>
          </div>
        )}

        {analysis && (
          <>
            <p className="text-sm text-gray-500">
              Latest analysis: {new Date(analysis.created_at).toLocaleString()}. {source.label}.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <Stat label="Keywords tracked" value={stats.keywords_tracked} />
              <Stat label="In the top 10" value={stats.in_top_10} />
              <Stat label={`Not found in top ${depth}`} value={stats.not_found} />
              <Stat label="Avg. monthly searches" value={stats.average_search_volume?.toLocaleString()} />
              <Stat label="Competitors found" value={stats.competitors_found} />
            </div>

            {result.warnings.length > 0 && (
              <ul className="rounded border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 list-disc pl-8">
                {result.warnings.map((w) => <li key={w}>{w}</li>)}
              </ul>
            )}

            <section className="bg-white rounded-lg shadow-sm p-6 overflow-x-auto">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-3">
                Keyword positions {source.is_sample && <SampleTag />}
              </h2>
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b text-gray-600">
                    <th className="py-2 pr-4">Keyword</th>
                    <th className="py-2 pr-4">Position</th>
                    <th className="py-2 pr-4">Since previous check</th>
                    <th className="py-2 pr-4">Searches / month</th>
                    <th className="py-2">Difficulty (0-100)</th>
                  </tr>
                </thead>
                <tbody>
                  {result.keywords.map((k) => (
                    <tr key={k.keyword} className="border-b last:border-0">
                      <td className="py-3 pr-4 font-medium">{k.keyword}</td>
                      <td className="py-3 pr-4">{k.rank != null ? `#${k.rank}` : `not in top ${depth}`}</td>
                      <td className="py-3 pr-4"><Change rank={k.rank} previous={k.previous_rank} /></td>
                      <td className="py-3 pr-4">{k.search_volume?.toLocaleString() ?? 'n/a'}</td>
                      <td className="py-3">{k.difficulty ?? 'n/a'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <div className="grid lg:grid-cols-2 gap-8">
              <section className="bg-white rounded-lg shadow-sm p-6 overflow-x-auto">
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-3">
                  Competitors {source.is_sample && <SampleTag />}
                </h2>
                <p className="text-sm text-gray-500 mb-3">
                  Other domains in the top 10 for your keywords, most frequent first.
                </p>
                {result.competitors.length === 0 ? (
                  <p className="text-gray-600">No competitors found.</p>
                ) : (
                  <table className="w-full text-sm text-left">
                    <thead>
                      <tr className="border-b text-gray-600">
                        <th className="py-2 pr-4">Domain</th>
                        <th className="py-2 pr-4">Keywords</th>
                        <th className="py-2">Avg. position</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.competitors.map((c) => (
                        <tr key={c.domain} className="border-b last:border-0">
                          <td className="py-3 pr-4 font-medium break-all">{c.domain}</td>
                          <td className="py-3 pr-4">{c.keywords_count}</td>
                          <td className="py-3">{c.average_rank}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </section>

              <section className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-3">
                  Technical check {source.is_sample && <SampleTag />}
                </h2>
                {result.technical_audit.available ? (
                  <>
                    <p className="text-sm text-gray-500 mb-3 break-all">
                      One page checked: {result.technical_audit.url}
                      {result.technical_audit.onpage_score != null && <> &middot; on-page score {result.technical_audit.onpage_score} of 100</>}
                    </p>
                    {result.technical_audit.issues.length === 0 ? (
                      <p className="text-gray-600">No issues flagged on this page.</p>
                    ) : (
                      <ul className="space-y-3">
                        {result.technical_audit.issues.map((issue) => (
                          <li key={issue.id} className="flex gap-3 items-start">
                            <span className={`shrink-0 rounded border px-2 py-0.5 text-xs font-semibold ${SEVERITY_STYLE[issue.severity] || ''}`}>
                              {issue.severity}
                            </span>
                            <span>
                              <span className="font-medium">{issue.title}.</span>{' '}
                              <span className="text-gray-600">{issue.detail}</span>
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </>
                ) : (
                  <p className="text-gray-600">The technical check could not be run for this analysis.</p>
                )}
              </section>
            </div>
          </>
        )}

        <section className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Reports</h2>
          {reports.length === 0 ? (
            <p className="text-gray-600">
              {analysis ? 'No reports yet. Press "Generate report".' : 'Run an analysis, then generate a report.'}
            </p>
          ) : (
            <ul className="space-y-3">
              {reports.map((r) => (
                <li key={r.id}>
                  <Link
                    to={`/reports/${r.id}`}
                    className="flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 p-4 hover:bg-gray-50"
                  >
                    <span className="font-medium">Report {new Date(r.created_at).toLocaleString()}</span>
                    <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-700">
                      {r.generator === 'openai' ? `AI-written (${r.model})` : 'Template, not AI'}
                    </span>
                    {r.is_sample && <SampleTag />}
                    <span className={`text-xs font-semibold ${r.reviewed_at ? 'text-green-700' : 'text-amber-700'}`}>
                      {r.reviewed_at ? 'Reviewed by a person' : 'Needs a person to review'}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
