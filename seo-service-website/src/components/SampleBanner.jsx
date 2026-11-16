import { FlaskConical } from 'lucide-react'

// Rendered wherever sample (invented) numbers are on screen.
export default function SampleBanner({ className = '' }) {
  return (
    <div
      className={`flex items-start gap-3 rounded-lg border-2 border-amber-400 bg-amber-50 p-4 text-amber-900 ${className}`}
      role="alert"
      data-testid="sample-banner"
    >
      <FlaskConical className="h-5 w-5 mt-0.5 shrink-0" />
      <div>
        <p className="font-bold">SAMPLE DATA</p>
        <p className="text-sm">
          The numbers and competitor names on this page are invented fixture values. They are not real search
          results and say nothing about any real website. Real data needs DataForSEO credentials on the server.
        </p>
      </div>
    </div>
  )
}

export function SampleTag() {
  return (
    <span className="inline-flex items-center rounded bg-amber-100 px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-amber-800 border border-amber-300">
      Sample data
    </span>
  )
}
