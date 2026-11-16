import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { CheckCircle2, TriangleAlert } from 'lucide-react'
import { api } from '@/lib/api.js'
import SampleBanner from './SampleBanner.jsx'

const PRIORITY_STYLE = {
  High: 'bg-red-100 text-red-800 border-red-200',
  Medium: 'bg-amber-100 text-amber-800 border-amber-200',
  Low: 'bg-gray-100 text-gray-700 border-gray-200',
}

function Section({ title, children }) {
  return (
    <section className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-xl font-semibold mb-3">{title}</h2>
      {children}
    </section>
  )
}

export default function ReportPage() {
  const { reportId } = useParams()
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.report(reportId).then((d) => setReport(d.report)).catch((err) => setError(err.message))
  }, [reportId])

  const review = async () => {
    setBusy(true)
    try {
      setReport((await api.reviewReport(reportId)).report)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
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
  if (!report) return <p className="container mx-auto px-4 py-16 text-gray-600">Loading...</p>

  const { content } = report
  const s = content.sections
  const isAi = content.generated_by.kind === 'openai'

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl space-y-6">
        <Link className="text-sm text-blue-600 underline" to={`/projects/${report.project_id}`}>Back to the project</Link>
        <h1 className="text-3xl font-bold text-gray-900">{content.title}</h1>
        <p className="text-sm text-gray-500">Created {new Date(report.created_at).toLocaleString()}</p>

        {content.data_source.is_sample && <SampleBanner />}

        <div className="rounded-lg border-2 border-amber-400 bg-amber-50 p-4 text-amber-900 flex gap-3" data-testid="disclaimer">
          <TriangleAlert className="h-5 w-5 mt-0.5 shrink-0" />
          <div>
            <p className="font-bold">A suggestion, not advice. A person must review this report.</p>
            <p className="text-sm">{content.disclaimer}</p>
          </div>
        </div>

        <div className="rounded-lg bg-white shadow-sm p-4 text-sm text-gray-700 space-y-1">
          <p>
            <strong>Text written by:</strong> {isAi ? `AI model (${content.generated_by.model})` : 'a fixed template, not an AI'}
          </p>
          <p className="text-gray-600">{content.generated_by.note}</p>
          <p>
            <strong>Data:</strong> {content.data_source.label}
          </p>
        </div>

        <Section title="Summary">
          <p className="whitespace-pre-line text-gray-800">{s.executive_summary}</p>
        </Section>
        <Section title="Ranking analysis">
          <p className="whitespace-pre-line text-gray-800">{s.ranking_analysis}</p>
        </Section>
        <Section title="Competitor analysis">
          <p className="whitespace-pre-line text-gray-800">{s.competitor_analysis}</p>
        </Section>
        <Section title="Content suggestions">
          <ul className="space-y-4">
            {s.content_suggestions.map((c, i) => (
              <li key={i}>
                <p className="font-medium">{c.title}</p>
                <p className="text-sm text-gray-500">
                  {c.type}
                  {c.keyword && <> &middot; keyword: {c.keyword}</>}
                </p>
                <p className="text-gray-700">{c.description}</p>
              </li>
            ))}
          </ul>
        </Section>
        <Section title="Technical recommendations">
          <ul className="list-disc pl-5 space-y-2 text-gray-800">
            {s.technical_recommendations.map((t, i) => <li key={i}>{t}</li>)}
          </ul>
        </Section>
        <Section title="Action plan">
          <ol className="space-y-4">
            {s.action_plan.map((a, i) => (
              <li key={i} className="flex gap-3 items-start">
                <span className={`shrink-0 rounded border px-2 py-0.5 text-xs font-semibold ${PRIORITY_STYLE[a.priority] || ''}`}>
                  {a.priority}
                </span>
                <span>
                  <span className="font-medium">{a.task}</span>
                  {a.rationale && <span className="block text-sm text-gray-600">{a.rationale}</span>}
                </span>
              </li>
            ))}
          </ol>
        </Section>

        <div className="bg-white rounded-lg shadow-sm p-6 flex flex-wrap items-center gap-4">
          {report.reviewed_at ? (
            <p className="flex items-center gap-2 text-green-700 font-medium">
              <CheckCircle2 className="h-5 w-5" /> Marked as reviewed by you on {new Date(report.reviewed_at).toLocaleString()}
            </p>
          ) : (
            <>
              <p className="text-gray-700">Once you have read and checked this report, mark it as reviewed.</p>
              <Button onClick={review} disabled={busy}>Mark as reviewed</Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
