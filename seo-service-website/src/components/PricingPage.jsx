import { Check, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'

// Keyword limits are enforced by the backend (src/config.py PLANS). Prices are a draft; nothing can be bought.
const plans = [
  { id: 'starter', name: 'Starter', price: '€199', limit: 10, description: 'Draft plan for small sites' },
  { id: 'professional', name: 'Professional', price: '€349', limit: 25, description: 'Draft plan for larger keyword lists' },
  { id: 'enterprise', name: 'Enterprise', price: '€499', limit: 50, description: 'Draft plan for the biggest lists' },
]

const included = [
  'Position, search volume and difficulty per keyword',
  'Competitor list from the top 10 results',
  'On-page technical check of one page',
  'Drafted report with six sections',
  'Reports marked as sample data, template or AI-written',
]

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white py-16">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">Draft plans</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            These plans are a draft. Nothing can be bought: there is no payment, no billing and no customers. In
            the prototype, the plan only sets how many keywords one project can track.
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {plans.map((plan) => (
            <div key={plan.id} className="bg-white rounded-2xl p-8 border border-gray-200 shadow-lg">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <p className="text-gray-600 mb-4">{plan.description}</p>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  {plan.price}
                  <span className="text-lg font-normal text-gray-600">/month</span>
                </div>
                <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
                  Draft price. Not offered yet.
                </p>
              </div>

              <ul className="space-y-4 mb-8">
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700 font-medium">Up to {plan.limit} keywords per project</span>
                </li>
                {included.map((feature) => (
                  <li key={feature} className="flex items-start">
                    <Check className="h-5 w-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link to={`/register?plan=${plan.id}`}>
                <Button className="w-full bg-gray-900 hover:bg-gray-800">
                  Try the prototype with this limit
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-gray-500 max-w-2xl mx-auto">
          The prototype has no support contract, strategy calls or account managers.
          Reports are suggestions that a person must review, and they do not promise any result.
        </p>
      </div>
    </div>
  )
}
