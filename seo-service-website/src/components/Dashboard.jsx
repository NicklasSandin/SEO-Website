import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { TrendingUp, TrendingDown, Users, FileText, BarChart3, Target, Zap, Download } from 'lucide-react'

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Mock customer ID for demo - in real app this would come from authentication
  const customerId = 1

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/seo/customers/${customerId}/dashboard`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data')
      }
      
      const data = await response.json()
      setDashboardData(data)
    } catch (err) {
      setError(err.message)
      // Use mock data for demo
      setDashboardData(getMockDashboardData())
    } finally {
      setLoading(false)
    }
  }

  const generateReport = async () => {
    try {
      const response = await fetch(`/api/seo/customers/${customerId}/generate-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ generate_pdf: true })
      })
      
      if (response.ok) {
        alert('Report generated successfully! Check your reports section.')
        fetchDashboardData() // Refresh data
      } else {
        alert('Failed to generate report. Please try again.')
      }
    } catch (err) {
      alert('Error generating report: ' + err.message)
    }
  }

  const getMockDashboardData = () => ({
    customer: {
      name: 'Demo Customer',
      email: 'demo@example.com',
      website_url: 'https://example.com',
      target_keywords: ['SEO services', 'digital marketing', 'website optimization'],
      subscription_plan: 'professional'
    },
    stats: {
      total_keywords: 15,
      ranking_improvements: 8,
      avg_search_volume: 2500,
      total_competitors: 12
    },
    keywords: [
      { keyword: 'SEO services', current_rank: 3, previous_rank: 5, search_volume: 5000, difficulty: 65 },
      { keyword: 'digital marketing', current_rank: 7, previous_rank: 9, search_volume: 8000, difficulty: 70 },
      { keyword: 'website optimization', current_rank: 12, previous_rank: 15, search_volume: 1200, difficulty: 45 }
    ],
    competitors: [
      { competitor_url: 'competitor1.com', competitor_rank: 2 },
      { competitor_url: 'competitor2.com', competitor_rank: 4 },
      { competitor_url: 'competitor3.com', competitor_rank: 6 }
    ],
    recent_reports: [
      { id: 1, report_date: '2025-09-01T00:00:00', ai_analysis: 'Recent analysis shows improvement' }
    ]
  })

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your SEO dashboard...</p>
        </div>
      </div>
    )
  }

  if (error && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error loading dashboard: {error}</p>
          <Button onClick={fetchDashboardData}>Retry</Button>
        </div>
      </div>
    )
  }

  const { customer, stats, keywords, competitors, recent_reports } = dashboardData

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">SEO Dashboard</h1>
              <p className="text-gray-600">{customer.website_url}</p>
            </div>
            <Button onClick={generateReport} className="bg-blue-600 hover:bg-blue-700">
              <FileText className="h-4 w-4 mr-2" />
              Generate Report
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Target className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Keywords</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_keywords}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Improvements</p>
                <p className="text-2xl font-bold text-gray-900">{stats.ranking_improvements}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg. Search Volume</p>
                <p className="text-2xl font-bold text-gray-900">{stats.avg_search_volume.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <Users className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Competitors</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_competitors}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Keywords Performance */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-6">Keyword Rankings</h2>
            <div className="space-y-4">
              {keywords.map((keyword, index) => {
                const isImproved = keyword.current_rank < keyword.previous_rank
                const rankChange = keyword.previous_rank - keyword.current_rank
                
                return (
                  <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{keyword.keyword}</h3>
                      <p className="text-sm text-gray-600">
                        {keyword.search_volume?.toLocaleString()} searches/month • {keyword.difficulty}% difficulty
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center">
                        <span className="text-2xl font-bold text-gray-900">#{keyword.current_rank}</span>
                        {keyword.previous_rank && (
                          <div className={`ml-2 flex items-center ${isImproved ? 'text-green-600' : 'text-red-600'}`}>
                            {isImproved ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                            <span className="text-sm ml-1">
                              {Math.abs(rankChange)}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Competitors */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-6">Top Competitors</h2>
            <div className="space-y-4">
              {competitors.map((competitor, index) => (
                <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div>
                    <h3 className="font-medium text-gray-900">{competitor.competitor_url}</h3>
                    <p className="text-sm text-gray-600">Average ranking position</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xl font-bold text-gray-900">#{competitor.competitor_rank}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Reports */}
        <div className="bg-white rounded-lg shadow-sm p-6 mt-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Recent Reports</h2>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Download Latest
            </Button>
          </div>
          
          {recent_reports.length > 0 ? (
            <div className="space-y-4">
              {recent_reports.map((report, index) => (
                <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div>
                    <h3 className="font-medium text-gray-900">
                      SEO Report - {new Date(report.report_date).toLocaleDateString()}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {report.ai_analysis ? 'AI analysis completed' : 'Processing...'}
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    View Report
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No reports generated yet</p>
              <Button onClick={generateReport} className="mt-4">
                Generate Your First Report
              </Button>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-blue-50 rounded-lg p-6 mt-8">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="justify-start">
              <Zap className="h-4 w-4 mr-2" />
              Run SEO Analysis
            </Button>
            <Button variant="outline" className="justify-start">
              <FileText className="h-4 w-4 mr-2" />
              View Content Ideas
            </Button>
            <Button variant="outline" className="justify-start">
              <BarChart3 className="h-4 w-4 mr-2" />
              Competitor Research
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

