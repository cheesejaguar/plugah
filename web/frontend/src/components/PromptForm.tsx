import React, { useState } from 'react'
import { Rocket } from 'lucide-react'

interface PromptFormProps {
  onSubmit: (data: { sessionId: string; title: string; budget: number }) => void
}

const PromptForm: React.FC<PromptFormProps> = ({ onSubmit }) => {
  const [title, setTitle] = useState('')
  const [prompt, setPrompt] = useState('')
  const [budget, setBudget] = useState(100)
  const [domain, setDomain] = useState('general')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch('/startup/begin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_title: title,
          prompt,
          budget_usd: budget,
          domain
        })
      })

      if (response.ok) {
        const data = await response.json()
        onSubmit({
          sessionId: data.session_id,
          title,
          budget
        })
      }
    } catch (error) {
      console.error('Failed to start project:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <Rocket className="h-8 w-8 text-primary-600" />
          <h2 className="text-2xl font-bold">Start Your Project</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Project Title
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="My Amazing Project"
              required
            />
          </div>

          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
              Project Description
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows={4}
              placeholder="Build a Slack bot that summarizes conversations..."
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-2">
                Budget (USD)
              </label>
              <input
                type="number"
                id="budget"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                min={10}
                max={10000}
                required
              />
              <p className="text-xs text-gray-500 mt-1">Min: $10, Max: $10,000</p>
            </div>

            <div>
              <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-2">
                Domain
              </label>
              <select
                id="domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="general">General</option>
                <option value="web">Web</option>
                <option value="data">Data/AI</option>
                <option value="api">API/Backend</option>
                <option value="mobile">Mobile</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary flex items-center justify-center space-x-2"
          >
            {loading ? (
              <span>Starting...</span>
            ) : (
              <>
                <Rocket className="h-5 w-5" />
                <span>Launch Project</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

export default PromptForm