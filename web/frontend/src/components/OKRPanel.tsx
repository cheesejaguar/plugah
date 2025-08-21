import React, { useEffect, useState } from 'react'
import { Target, TrendingUp, Award, AlertTriangle } from 'lucide-react'

interface OKRPanelProps {
  sessionId: string
}

const OKRPanel: React.FC<OKRPanelProps> = ({ sessionId }) => {
  const [metricsData, setMetricsData] = useState<any>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`/status/metrics/${sessionId}`)
        if (response.ok) {
          const data = await response.json()
          setMetricsData(data.metrics)
        }
      } catch (error) {
        console.error('Failed to fetch metrics:', error)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000)

    return () => clearInterval(interval)
  }, [sessionId])

  if (!metricsData) {
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

  const health = metricsData.health || {}
  const critical = metricsData.critical || []

  return (
    <div className="card">
      <div className="flex items-center space-x-2 mb-4">
        <Target className="h-6 w-6 text-primary-600" />
        <h3 className="text-lg font-semibold">OKRs & KPIs</h3>
      </div>

      <div className="space-y-4">
        {/* Health Scores */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Health Scores</h4>
          <div className="space-y-2">
            {Object.entries(health).map(([key, value]: [string, any]) => (
              <div key={key}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  <span className="font-medium">{value.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      value > 80 ? 'bg-green-500' : value > 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Critical Metrics */}
        {critical.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center space-x-1">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              <span>Needs Attention</span>
            </h4>
            <div className="space-y-2">
              {critical.slice(0, 3).map((item: any, idx: number) => (
                <div key={idx} className="bg-orange-50 rounded-lg p-2 text-sm">
                  <div className="font-medium text-orange-900">{item.metric || item.objective}</div>
                  <div className="text-orange-700">
                    {item.attainment.toFixed(1)}% achieved
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Performers */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center space-x-1">
            <Award className="h-4 w-4 text-green-500" />
            <span>Top Performers</span>
          </h4>
          <div className="space-y-1">
            {metricsData.okrs && Object.entries(metricsData.okrs)
              .filter(([_, okr]: [string, any]) => okr.attainment > 80)
              .slice(0, 3)
              .map(([id, okr]: [string, any]) => (
                <div key={id} className="bg-green-50 rounded-lg p-2 text-sm">
                  <div className="font-medium text-green-900">{okr.title}</div>
                  <div className="text-green-700">{okr.owner}</div>
                </div>
              ))
            }
          </div>
        </div>
      </div>
    </div>
  )
}

export default OKRPanel