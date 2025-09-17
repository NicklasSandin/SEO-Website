import { Button } from '@/components/ui/button.jsx'
import { ArrowRight, TrendingUp, Target, Zap } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            We help you rank{' '}
            <span className="text-blue-600 relative">
              higher on Google
              <div className="absolute -bottom-2 left-0 right-0 h-1 bg-blue-600 rounded-full"></div>
            </span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Automated SEO reports, competitor analysis, and content suggestions 
            delivered monthly. No manual work required.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link to="/service">
              <Button size="lg" className="text-lg px-8 py-4 bg-blue-600 hover:bg-blue-700">
                Learn How It Works
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="text-lg px-8 py-4 border-blue-600 text-blue-600 hover:bg-blue-50">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto mt-16">
          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Track Rankings</h3>
            <p className="text-gray-600">
              Monitor your keyword positions and see exactly where you rank compared to competitors.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <Target className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Competitor Analysis</h3>
            <p className="text-gray-600">
              Discover what your competitors are doing right and get actionable insights to outrank them.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <Zap className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">AI-Powered Reports</h3>
            <p className="text-gray-600">
              Get detailed monthly reports with content suggestions and optimization recommendations.
            </p>
          </div>
        </div>

        {/* Social Proof */}
        <div className="text-center mt-16">
          <p className="text-gray-500 mb-8">Trusted by businesses across Europe</p>
          <div className="flex justify-center items-center space-x-8 opacity-60">
            <div className="text-2xl font-bold text-gray-400">COMPANY</div>
            <div className="text-2xl font-bold text-gray-400">BRAND</div>
            <div className="text-2xl font-bold text-gray-400">STARTUP</div>
            <div className="text-2xl font-bold text-gray-400">AGENCY</div>
          </div>
        </div>

        {/* Testimonials Section */}
        <div className="container mx-auto px-4 py-16">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-gray-900 mb-12">
            What Our Clients Say
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-xl shadow-lg">
              <p className="text-gray-700 italic mb-4">
                "SEO Pro transformed our online visibility. We saw a significant increase in organic traffic within the first month. Highly recommended!"
              </p>
              <p className="font-semibold text-gray-900">Anna Lindqvist, Marketing Director at IKEA</p>
            </div>
            <div className="bg-white p-8 rounded-xl shadow-lg">
              <p className="text-gray-700 italic mb-4">
                "The AI-powered reports are incredibly insightful and easy to understand. We finally have a clear roadmap for our SEO strategy."
              </p>
              <p className="font-semibold text-gray-900">Erik Johansson, CEO of Spotify Sweden</p>
            </div>
            <div className="bg-white p-8 rounded-xl shadow-lg">
              <p className="text-gray-700 italic mb-4">
                "We used to struggle with manual SEO tasks. SwedensAi automated everything, saving us countless hours and delivering fantastic results."
              </p>
              <p className="font-semibold text-gray-900">Sofia Karlsson, Digital Manager at H&M</p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-blue-600 rounded-2xl p-8 md:p-12 text-center text-white mt-16">
          <h2 className="text-3xl font-bold mb-4">Ready to dominate Google?</h2>
          <p className="text-xl mb-6 opacity-90">
            Join hundreds of businesses already ranking higher with our automated SEO service.
          </p>
          <Link to="/pricing">
            <Button size="lg" variant="secondary" className="text-lg px-8 py-4">
              Start Your SEO Journey
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

