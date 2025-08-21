import React, { useEffect, useState } from 'react'
import { DollarSign, AlertTriangle } from 'lucide-react'

interface BudgetPanelProps {
  sessionId: string
}

const BudgetPanel: React.FC<BudgetPanelProps> = ({ sessionId }) => {
  const [budgetData, setBudgetData] = useState<any>(null)

  useEffect(() => {
    const fetchBudget = async () => {
      try {
        const response = await fetch(`/status/summary/${sessionId}`)
        if (response.ok) {
          const data = await response.json()
          setBudgetData(data.budget)
        }
      } catch (error) {
        console.error('Failed to fetch budget:', error)
      }
    }

    fetchBudget()
    const interval = setInterval(fetchBudget, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [sessionId])

  if (!budgetData) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    )
  }

  const spentPercentage = (budgetData.spent / (budgetData.spent + budgetData.remaining)) * 100
  const alertLevel = budgetData.alert_level || 'normal'

  const getAlertColor = () => {
    switch (alertLevel) {
      case 'emergency':
        return 'bg-red-600'
      case 'exceeded_soft':
        return 'bg-orange-600'
      case 'critical':
        return 'bg-yellow-600'
      case 'warning':
        return 'bg-yellow-500'
      default:
        return 'bg-green-600'
    }
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <DollarSign className="h-6 w-6 text-primary-600" />
          <h3 className="text-lg font-semibold">Budget Status</h3>
        </div>
        {alertLevel !== 'normal' && (
          <div className="flex items-center space-x-1 text-orange-600">
            <AlertTriangle className="h-5 w-5" />
            <span className="text-sm font-medium">{alertLevel}</span>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {/* Progress Bar */}
        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Spent</span>
            <span>${budgetData.spent.toFixed(2)}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${getAlertColor()}`}
              style={{ width: `${Math.min(spentPercentage, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-sm text-gray-600 mt-1">
            <span>0%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Spent</p>
            <p className="text-lg font-semibold text-red-600">
              ${budgetData.spent.toFixed(2)}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Remaining</p>
            <p className="text-lg font-semibold text-green-600">
              ${budgetData.remaining.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Alert Messages */}
        {alertLevel !== 'normal' && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
            <p className="text-sm text-orange-800">
              {alertLevel === 'emergency' && 'Emergency: Near hard cap limit!'}
              {alertLevel === 'exceeded_soft' && 'Soft cap exceeded, implement cost controls'}
              {alertLevel === 'critical' && 'Approaching soft cap, review spending'}
              {alertLevel === 'warning' && 'Monitor spending closely'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default BudgetPanel