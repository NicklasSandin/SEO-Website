import { Button } from '@/components/ui/button.jsx'
import { ArrowRight, Search, BarChart3, FileText, Cpu, Globe, Users } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function ServicePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-16">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            Our AI checks your website, competitors, and keywords
          </h1>
          <p className="text-xl opacity-90 max-w-3xl mx-auto">
            Advanced artificial intelligence analyzes your SEO performance 24/7, 
            delivering insights that would take hours of manual work.
          </p>
        </div>
      </div>

      {/* How It Works */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">How Our AI-Powered System Works</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Three simple steps to transform your SEO performance with cutting-edge technology
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {/* Step 1 */}
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Search className="h-8 w-8 text-blue-600" />
            </div>
            <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto mb-4 text-sm font-bold">1</div>
            <h3 className="text-xl font-semibold mb-3">AI Scans Your Website</h3>
            <p className="text-gray-600">
              Our advanced AI analyzes your website's technical SEO, content quality, 
              and current keyword rankings across all major search engines.
            </p>
          </div>

          {/* Step 2 */}
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Users className="h-8 w-8 text-green-600" />
            </div>
            <div className="bg-green-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto mb-4 text-sm font-bold">2</div>
            <h3 className="text-xl font-semibold mb-3">Competitor Intelligence</h3>
            <p className="text-gray-600">
              AI identifies your top competitors and analyzes their strategies, 
              content gaps, and ranking opportunities you can exploit.
            </p>
          </div>

          {/* Step 3 */}
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <FileText className="h-8 w-8 text-purple-600" />
            </div>
            <div className="bg-purple-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto mb-4 text-sm font-bold">3</div>
            <h3 className="text-xl font-semibold mb-3">Actionable Reports</h3>
            <p className="text-gray-600">
              Receive detailed monthly reports with specific recommendations, 
              content ideas, and a clear roadmap to improve your rankings.
            </p>
          </div>
        </div>

        {/* Technology Features */}
        <div className="bg-gray-50 rounded-2xl p-8 md:p-12 mb-16">
          <h2 className="text-3xl font-bold text-center mb-12">Powered by Advanced Technology</h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Cpu className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">AI-Powered Analysis</h3>
                <p className="text-gray-600">
                  Machine learning algorithms process millions of data points to identify 
                  ranking patterns and optimization opportunities.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Globe className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Real-Time Monitoring</h3>
                <p className="text-gray-600">
                  Continuous tracking of your rankings, competitor movements, 
                  and algorithm updates across all search engines.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <BarChart3 className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Predictive Insights</h3>
                <p className="text-gray-600">
                  Advanced forecasting models predict ranking changes and suggest 
                  proactive optimizations before competitors catch up.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <FileText className="h-6 w-6 text-orange-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Content Generation</h3>
                <p className="text-gray-600">
                  AI creates ready-to-publish content ideas, meta descriptions, 
                  and optimization suggestions tailored to your industry.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* What You Get */}
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-8">What You Get Every Month</h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="text-2xl font-bold text-blue-600 mb-2">📊</div>
              <h3 className="font-semibold mb-2">Ranking Reports</h3>
              <p className="text-sm text-gray-600">Detailed position tracking for all your keywords</p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="text-2xl font-bold text-green-600 mb-2">🔍</div>
              <h3 className="font-semibold mb-2">Competitor Analysis</h3>
              <p className="text-sm text-gray-600">What your competitors are doing to outrank you</p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="text-2xl font-bold text-purple-600 mb-2">✍️</div>
              <h3 className="font-semibold mb-2">Content Ideas</h3>
              <p className="text-sm text-gray-600">Ready-to-publish blog posts and page content</p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="text-2xl font-bold text-orange-600 mb-2">🛠️</div>
              <h3 className="font-semibold mb-2">Technical Fixes</h3>
              <p className="text-sm text-gray-600">Specific technical SEO improvements to implement</p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to see what AI can do for your SEO?</h2>
          <p className="text-lg text-gray-600 mb-8">
            Get your first AI-powered SEO report and start ranking higher today.
          </p>
          <Link to="/pricing">
            <Button size="lg" className="text-lg px-8 py-4 bg-blue-600 hover:bg-blue-700">
              Get Started Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

