import React, { useEffect, useState } from 'react'
import { Users, User, Briefcase, Code, Database, PenTool } from 'lucide-react'

interface OrgChartProps {
  oag: any
}

const OrgChart: React.FC<OrgChartProps> = ({ oag }) => {
  const [orgData, setOrgData] = useState<any>(null)

  useEffect(() => {
    if (oag) {
      processOrgData(oag)
    }
  }, [oag])

  const processOrgData = (data: any) => {
    const nodes = data.nodes || {}
    const byLevel: any = {
      C_SUITE: [],
      VP: [],
      DIRECTOR: [],
      MANAGER: [],
      IC: []
    }

    Object.values(nodes).forEach((node: any) => {
      if (node.node_type === 'agent') {
        const level = node.level || 'IC'
        byLevel[level].push(node)
      }
    })

    setOrgData(byLevel)
  }

  const getRoleIcon = (role: string) => {
    if (role.includes('CEO') || role.includes('CTO') || role.includes('CFO')) {
      return <Briefcase className="h-5 w-5" />
    }
    if (role.includes('Engineer') || role.includes('Developer')) {
      return <Code className="h-5 w-5" />
    }
    if (role.includes('Data') || role.includes('Analyst')) {
      return <Database className="h-5 w-5" />
    }
    if (role.includes('Designer') || role.includes('Product')) {
      return <PenTool className="h-5 w-5" />
    }
    return <User className="h-5 w-5" />
  }

  if (!orgData) {
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

  return (
    <div className="card">
      <div className="flex items-center space-x-3 mb-6">
        <Users className="h-8 w-8 text-primary-600" />
        <h2 className="text-2xl font-bold">Organization Structure</h2>
      </div>

      <div className="space-y-6">
        {/* C-Suite */}
        {orgData.C_SUITE.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-700 mb-3">Board Room</h3>
            <div className="grid grid-cols-3 gap-3">
              {orgData.C_SUITE.map((agent: any) => (
                <div
                  key={agent.id}
                  className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg p-3"
                >
                  <div className="flex items-center space-x-2">
                    {getRoleIcon(agent.role)}
                    <span className="font-medium">{agent.role}</span>
                  </div>
                  {agent.kpis?.length > 0 && (
                    <div className="text-xs mt-1 opacity-90">
                      {agent.kpis.length} KPIs
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* VPs */}
        {orgData.VP.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-700 mb-3">Vice Presidents</h3>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              {orgData.VP.map((agent: any) => (
                <div
                  key={agent.id}
                  className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg p-3"
                >
                  <div className="flex items-center space-x-2">
                    {getRoleIcon(agent.role)}
                    <span className="font-medium">{agent.role}</span>
                  </div>
                  {agent.specialization && (
                    <div className="text-xs mt-1 opacity-90">
                      {agent.specialization}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Directors */}
        {orgData.DIRECTOR.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-700 mb-3">Directors</h3>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
              {orgData.DIRECTOR.map((agent: any) => (
                <div
                  key={agent.id}
                  className="bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg p-2 text-sm"
                >
                  <div className="flex items-center space-x-1">
                    {getRoleIcon(agent.role)}
                    <span>{agent.role}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Managers */}
        {orgData.MANAGER.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-700 mb-3">Managers</h3>
            <div className="grid grid-cols-3 lg:grid-cols-5 gap-2">
              {orgData.MANAGER.map((agent: any) => (
                <div
                  key={agent.id}
                  className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white rounded-lg p-2 text-sm"
                >
                  <div className="flex items-center space-x-1">
                    <User className="h-4 w-4" />
                    <span>{agent.role}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ICs */}
        {orgData.IC.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-700 mb-3">
              Individual Contributors ({orgData.IC.length})
            </h3>
            <div className="grid grid-cols-4 lg:grid-cols-6 gap-2">
              {orgData.IC.slice(0, 12).map((agent: any) => (
                <div
                  key={agent.id}
                  className="bg-gray-500 text-white rounded-lg p-2 text-xs text-center"
                >
                  {getRoleIcon(agent.specialization || agent.role)}
                  <div className="mt-1 truncate">
                    {agent.specialization || agent.role}
                  </div>
                </div>
              ))}
              {orgData.IC.length > 12 && (
                <div className="bg-gray-400 text-white rounded-lg p-2 text-xs text-center flex items-center justify-center">
                  +{orgData.IC.length - 12} more
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-primary-600">
              {Object.values(oag.nodes || {}).filter((n: any) => n.node_type === 'agent').length}
            </p>
            <p className="text-sm text-gray-600">Total Agents</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">
              {Object.values(oag.nodes || {}).filter((n: any) => n.node_type === 'task').length}
            </p>
            <p className="text-sm text-gray-600">Total Tasks</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-purple-600">
              ${oag.budget?.forecast_cost_usd?.toFixed(2) || '0.00'}
            </p>
            <p className="text-sm text-gray-600">Forecast Cost</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OrgChart