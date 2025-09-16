import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Check, ArrowRight, Star } from 'lucide-react'

export default function PricingPage() {
  const [selectedPlan, setSelectedPlan] = useState('professional')
  const [formData, setFormData] = useState({
    website: '',
    keywords: '',
    email: '',
    name: '',
    plan: 'professional'
  })

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      const response = await fetch('/api/seo/customers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          website_url: formData.website,
          target_keywords: formData.keywords,
          subscription_plan: formData.plan
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        alert('Thank you! Your SEO service has been set up successfully. We will contact you shortly with your login details.')
        // In a real app, redirect to dashboard or login page
        window.location.href = '/dashboard'
      } else {
        const error = await response.json()
        alert('Error: ' + (error.error || 'Failed to create account'))
      }
    } catch (error) {
      console.error('Signup error:', error)
      alert('Thank you! We will contact you shortly to set up your SEO service.')
    }
  }

  const getKeywordPlaceholder = (planId) => {
    switch (planId) {
      case 'starter':
        return 'e.g., restaurant Stockholm (up to 10 keywords)';
      case 'professional':
        return 'e.g., plumber Malmö, emergency plumbing (up to 25 keywords)';
      case 'enterprise':
        return 'e.g., enterprise software solutions, B2B marketing strategy (up to 50 keywords)';
      default:
        return 'e.g., your keywords separated by commas';
    }
  };

  const plans = [
    {
      id: 'starter',
      name: 'Starter',
      price: '€199',
      description: 'Perfect for small businesses',
      features: [
        'Up to 10 keywords tracking',
        'Monthly SEO reports',
        'Basic competitor analysis',
        '3 content ideas per month',
        'Email support'
      ]
    },
    {
      id: 'professional',
      name: 'Professional',
      price: '€349',
      description: 'Most popular for growing businesses',
      features: [
        'Up to 25 keywords tracking',
        'Detailed monthly SEO reports',
        'Advanced competitor analysis',
        '10 content ideas per month',
        'Technical SEO recommendations',
        'Priority email support',
        'Monthly strategy call'
      ],
      popular: true
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: '€499',
      description: 'For established businesses',
      features: [
        'Up to 50 keywords tracking',
        'Comprehensive monthly reports',
        'Full competitor intelligence',
        'Unlimited content ideas',
        'Technical SEO audit',
        'Dedicated account manager',
        'Weekly strategy calls',
        'Custom reporting'
      ]
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white py-16">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            You get monthly reports + content ideas
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Choose the plan that fits your business. All plans include AI-powered SEO analysis, 
            competitor tracking, and actionable recommendations delivered monthly.
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        {/* Pricing Plans */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl p-8 relative ${
                plan.popular 
                  ? 'border-2 border-blue-600 shadow-xl scale-105' 
                  : 'border border-gray-200 shadow-lg'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <div className="bg-blue-600 text-white px-4 py-2 rounded-full text-sm font-semibold flex items-center">
                    <Star className="h-4 w-4 mr-1" />
                    Most Popular
                  </div>
                </div>
              )}
              
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <p className="text-gray-600 mb-4">{plan.description}</p>
                <div className="text-4xl font-bold text-gray-900 mb-2">
                  {plan.price}
                  <span className="text-lg font-normal text-gray-600">/month</span>
                </div>
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <Check className="h-5 w-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                className={`w-full ${
                  plan.popular 
                    ? 'bg-blue-600 hover:bg-blue-700' 
                    : 'bg-gray-900 hover:bg-gray-800'
                }`}
                onClick={() => {
                  setSelectedPlan(plan.id)
                  setFormData({ ...formData, plan: plan.id })
                  document.getElementById('signup-form').scrollIntoView({ behavior: 'smooth' })
                }}
              >
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>

        {/* What's Included */}
        <div className="bg-white rounded-2xl p-8 md:p-12 mb-16">
          <h2 className="text-3xl font-bold text-center mb-12">What's Included in Every Plan</h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📊</span>
              </div>
              <h3 className="font-semibold mb-2">Monthly SEO Reports</h3>
              <p className="text-sm text-gray-600">Detailed analysis of your rankings, traffic, and performance</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="font-semibold mb-2">Competitor Tracking</h3>
              <p className="text-sm text-gray-600">Monitor what your competitors are doing and how to beat them</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">✍️</span>
              </div>
              <h3 className="font-semibold mb-2">Content Ideas</h3>
              <p className="text-sm text-gray-600">Ready-to-publish blog posts and page content suggestions</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔧</span>
              </div>
              <h3 className="font-semibold mb-2">Action Plans</h3>
              <p className="text-sm text-gray-600">Clear, step-by-step instructions to improve your rankings</p>
            </div>
          </div>
        </div>

        {/* Signup Form */}
        <div id="signup-form" className="bg-white rounded-2xl p-8 md:p-12 max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8">Start Your SEO Journey Today</h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Website URL *
              </label>
              <input
                type="url"
                name="website"
                value={formData.website}
                onChange={handleInputChange}
                placeholder="https://yourwebsite.com"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Keywords *
              </label>
              <textarea
                name="keywords"
                value={formData.keywords}
                onChange={handleInputChange}
                placeholder={getKeywordPlaceholder(selectedPlan)}
                rows="3"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                Separate keywords with commas. Include your location for local businesses.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Name *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="John Doe"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="john@company.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selected Plan
              </label>
              <select
                name="plan"
                value={formData.plan}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              >
                <option value="starter">Starter - €199/month</option>
                <option value="professional">Professional - €349/month</option>
                <option value="enterprise">Enterprise - €499/month</option>
              </select>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                <strong>Next steps:</strong> After submitting this form, we'll contact you within 24 hours to:
              </p>
              <ul className="text-sm text-gray-600 mt-2 space-y-1">
                <li>• Set up your account and payment</li>
                <li>• Configure your keyword tracking</li>
                <li>• Schedule your first SEO analysis</li>
                <li>• Deliver your first report within 7 days</li>
              </ul>
            </div>

            <Button type="submit" size="lg" className="w-full bg-blue-600 hover:bg-blue-700">
              Start My SEO Service
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            No setup fees. Cancel anytime. 30-day money-back guarantee.
          </p>
        </div>
      </div>
    </div>
  )
}

