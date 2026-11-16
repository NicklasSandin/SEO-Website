import { Button } from '@/components/ui/button.jsx'
import { ArrowRight, Search, Users, FileText } from 'lucide-react'
import { Link } from 'react-router-dom'

const sections = [
  ['Summary', 'A short overview of how many keywords are on page one and what the technical check found.'],
  ['Ranking analysis', 'Each keyword with its position, search volume and difficulty.'],
  ['Competitor analysis', 'The sites that appear most often above or around you.'],
  ['Content suggestions', 'Pages or articles worth checking for keywords where you are not on page one.'],
  ['Technical recommendations', 'Findings from an on-page check of the website address you entered.'],
  ['Action plan', 'A prioritised list of things to look at, starting with a person reviewing the report.'],
]

export default function ServicePage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-16">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">How Siktio works</h1>
          <p className="text-xl opacity-90 max-w-3xl mx-auto">
            You give it a website and keywords. It fetches ranking data, works out who the competitors are and
            drafts a report you can read and review.
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Search className="h-8 w-8 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">1. Enter your site and keywords</h3>
            <p className="text-gray-600">You choose the website, the keywords, and the country and language to check.</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Users className="h-8 w-8 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">2. Run an analysis</h3>
            <p className="text-gray-600">
              For each keyword Siktio asks DataForSEO for Google&apos;s organic results, finds your position, lists
              the competitors in the top 10, and runs an on-page check of your site address. It runs when you press
              the button, not continuously.
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <FileText className="h-8 w-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">3. Read and review the report</h3>
            <p className="text-gray-600">
              A report is drafted from that data. Each report says whether an AI model or a template wrote the text,
              and can be marked as reviewed once a person has read it.
            </p>
          </div>
        </div>

        <div className="bg-gray-50 rounded-2xl p-8 md:p-12 mb-16">
          <h2 className="text-3xl font-bold text-center mb-8">What a report contains</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {sections.map(([title, text]) => (
              <div key={title} className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="font-semibold mb-2">{title}</h3>
                <p className="text-sm text-gray-600">{text}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-8 mb-16">
          <h2 className="text-2xl font-bold mb-4 text-amber-900">Limits you should know about</h2>
          <ul className="space-y-2 text-amber-900 list-disc pl-5">
            <li>Reports are automatically drafted suggestions. They can be wrong. A person must review them.</li>
            <li>Nothing here promises or predicts higher rankings, more traffic or more revenue.</li>
            <li>The technical check covers the one page you entered, not the whole site.</li>
            <li>The competitor list shows who ranks for your keywords. It does not explain why.</li>
            <li>Positions are counted among organic results, within the first 20 results by default. &quot;Not found&quot; means not found within that depth.</li>
            <li>Without DataForSEO credentials on the server, every number is invented sample data and is marked as such. Without an OpenAI key, report text comes from a fixed template.</li>
          </ul>
        </div>

        <div className="text-center">
          <Link to="/register">
            <Button size="lg" className="text-lg px-8 py-4 bg-blue-600 hover:bg-blue-700">
              Create an account
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
