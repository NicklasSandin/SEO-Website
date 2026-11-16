import { Button } from '@/components/ui/button.jsx'
import { ArrowRight, TrendingUp, Target, FileText } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <p className="inline-block rounded-full bg-amber-100 text-amber-900 border border-amber-300 px-4 py-1 text-sm font-semibold mb-6">
            Prototype. Not a live service yet.
          </p>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            See where your website shows up on{' '}
            <span className="text-blue-600">Google</span>
          </h1>

          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Siktio checks where your site lands for the keywords you choose, lists the sites that rank around you,
            and drafts a report with suggestions on what to look at first. A person should read the report before
            anything is done with it.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link to="/register">
              <Button size="lg" className="text-lg px-8 py-4 bg-blue-600 hover:bg-blue-700">
                Create an account
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/service">
              <Button size="lg" variant="outline" className="text-lg px-8 py-4 border-blue-600 text-blue-600 hover:bg-blue-50">
                How it works
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto mt-8">
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Position per keyword</h3>
            <p className="text-gray-600">
              Your position in Google&apos;s organic results for each keyword, with monthly search volume and keyword
              difficulty. The data comes from the DataForSEO service.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <Target className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Competitors</h3>
            <p className="text-gray-600">
              The other sites that appear most often in the top 10 for your keywords, with their average position.
              It shows who ranks, not why.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <FileText className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">A drafted report</h3>
            <p className="text-gray-600">
              Summary, ranking analysis, competitor analysis, content suggestions, technical notes and an action plan.
              Written by an OpenAI model when one is configured, otherwise by a plain template that says so.
            </p>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow p-8 mt-16 max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
          <div>
            <h2 className="text-2xl font-bold mb-4">What exists today</h2>
            <ul className="space-y-2 text-gray-700 list-disc pl-5">
              <li>A backend that fetches ranking data, finds competitors and builds reports.</li>
              <li>This web interface: account, projects, dashboard and reports.</li>
              <li>A sample-data mode that runs without any credentials, clearly marked on every screen.</li>
            </ul>
          </div>
          <div>
            <h2 className="text-2xl font-bold mb-4">What does not exist yet</h2>
            <ul className="space-y-2 text-gray-700 list-disc pl-5">
              <li>A deployed service. This is a prototype that runs locally.</li>
              <li>Customers, published results or case studies.</li>
              <li>Any promise about rankings or traffic. Reports are suggestions, not forecasts.</li>
            </ul>
          </div>
        </div>

        <div className="bg-blue-600 rounded-2xl p-8 md:p-12 text-center text-white mt-16 max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold mb-4">Try the prototype</h2>
          <p className="text-xl mb-6 opacity-90">
            Create an account, add a website and keywords, and generate a report. Without DataForSEO credentials
            you will see sample data.
          </p>
          <Link to="/register">
            <Button size="lg" variant="secondary" className="text-lg px-8 py-4">
              Create an account
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
