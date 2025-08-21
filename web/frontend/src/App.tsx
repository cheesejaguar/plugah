import React, { useState } from 'react'
import PromptForm from './components/PromptForm'
import StartupQA from './components/StartupQA'
import OrgChart from './components/OrgChart'
import BudgetPanel from './components/BudgetPanel'
import OKRPanel from './components/OKRPanel'
import RunLog from './components/RunLog'
import { Briefcase, Brain, DollarSign, Target, Activity } from 'lucide-react'

type Phase = 'prompt' | 'discovery' | 'planning' | 'execution' | 'complete'

function App() {
  const [phase, setPhase] = useState<Phase>('prompt')
  const [sessionId, setSessionId] = useState<string>('')
  const [, setProjectTitle] = useState<string>('')
  const [budget, setBudget] = useState<number>(0)
  const [oag, setOag] = useState<any>(null)
  const [metrics, setMetrics] = useState<any>(null)

  const handlePromptSubmit = (data: { sessionId: string; title: string; budget: number }) => {
    setSessionId(data.sessionId)
    setProjectTitle(data.title)
    setBudget(data.budget)
    setPhase('discovery')
  }

  const handleDiscoveryComplete = () => {
    setPhase('planning')
  }

  const handlePlanningComplete = (oagData: any) => {
    setOag(oagData)
    setPhase('execution')
  }

  const handleExecutionComplete = (metricsData: any) => {
    setMetrics(metricsData)
    setPhase('complete')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Brain className="h-8 w-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">Plugah.ai</h1>
            </div>
            <div className="flex items-center space-x-6">
              <PhaseIndicator phase={phase} />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {phase === 'prompt' && (
          <PromptForm onSubmit={handlePromptSubmit} />
        )}

        {phase === 'discovery' && sessionId && (
          <StartupQA 
            sessionId={sessionId}
            onComplete={handleDiscoveryComplete}
          />
        )}

        {phase === 'planning' && sessionId && (
          <PlanningView
            sessionId={sessionId}
            onComplete={handlePlanningComplete}
          />
        )}

        {phase === 'execution' && sessionId && (
          <ExecutionView
            sessionId={sessionId}
            oag={oag}
            onComplete={handleExecutionComplete}
          />
        )}

        {phase === 'complete' && (
          <CompleteView
            sessionId={sessionId}
            metrics={metrics}
            budget={budget}
          />
        )}
      </main>
    </div>
  )
}

function PhaseIndicator({ phase }: { phase: Phase }) {
  const phases = [
    { key: 'prompt', label: 'Setup', icon: Briefcase },
    { key: 'discovery', label: 'Discovery', icon: Brain },
    { key: 'planning', label: 'Planning', icon: Target },
    { key: 'execution', label: 'Execution', icon: Activity },
    { key: 'complete', label: 'Complete', icon: DollarSign },
  ]

  return (
    <div className="flex items-center space-x-2">
      {phases.map((p, idx) => {
        const Icon = p.icon
        const isActive = p.key === phase
        const isPast = phases.findIndex(ph => ph.key === phase) > idx

        return (
          <React.Fragment key={p.key}>
            <div className="flex items-center">
              <div
                className={`
                  flex items-center justify-center w-8 h-8 rounded-full
                  ${isActive ? 'bg-primary-600 text-white' : isPast ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}
                `}
              >
                <Icon className="h-4 w-4" />
              </div>
              <span className={`ml-2 text-sm ${isActive ? 'font-semibold' : ''}`}>
                {p.label}
              </span>
            </div>
            {idx < phases.length - 1 && (
              <div className={`w-12 h-0.5 ${isPast ? 'bg-green-500' : 'bg-gray-300'}`} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}

function PlanningView({ sessionId, onComplete }: any) {
  const [loading, setLoading] = useState(false)

  const handlePlan = async () => {
    setLoading(true)
    try {
      const response = await fetch('/run/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      })
      
      if (response.ok) {
        await response.json()
        
        // Fetch the OAG
        const oagResponse = await fetch(`/status/oag/${sessionId}`)
        const oagData = await oagResponse.json()
        
        onComplete(oagData.oag)
      }
    } catch (error) {
      console.error('Planning failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">Planning Organization</h2>
      <p className="text-gray-600 mb-6">
        The system will now plan the organizational structure and task dependencies.
      </p>
      <button
        onClick={handlePlan}
        disabled={loading}
        className="btn-primary"
      >
        {loading ? 'Planning...' : 'Start Planning'}
      </button>
    </div>
  )
}

function ExecutionView({ sessionId, oag, onComplete }: any) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <OrgChart oag={oag} />
        <RunLog sessionId={sessionId} onComplete={onComplete} />
      </div>
      <div className="space-y-6">
        <BudgetPanel sessionId={sessionId} />
        <OKRPanel sessionId={sessionId} />
      </div>
    </div>
  )
}

function CompleteView({ sessionId, metrics }: any) {
  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-green-600 mb-4">Project Complete!</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">Total Cost</p>
          <p className="text-xl font-semibold">${metrics?.total_cost || 0}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Budget Remaining</p>
          <p className="text-xl font-semibold">${metrics?.budget_remaining || 0}</p>
        </div>
      </div>
      <div className="mt-6">
        <a
          href={`/.runs/${sessionId}/artifacts/summary_report.json`}
          className="btn-primary"
          download
        >
          Download Report
        </a>
      </div>
    </div>
  )
}

export default App