import { useEffect, useState } from 'react'
import { api } from '@/lib/api.js'

// Shown on every page. States what this running copy is, using what the backend reports.
export default function StatusBanner() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ unreachable: true }))
  }, [])

  let mode = 'Checking the backend...'
  if (health?.unreachable) mode = 'The backend is not reachable.'
  else if (health) {
    mode = health.rank_data_is_sample
      ? 'Rank data is SAMPLE DATA (no DataForSEO credentials are configured).'
      : 'Rank data comes from DataForSEO.'
    mode += health.report_generator === 'openai' ? ' Report text is written by an OpenAI model.' : ' Report text comes from a template, not an AI.'
  }

  return (
    <div className="bg-amber-50 border-b border-amber-200 text-amber-900 text-sm" role="status">
      <div className="container mx-auto px-4 py-2">
        <strong>Prototype.</strong> Siktio is not a live service and has no customers. {mode}
      </div>
    </div>
  )
}
