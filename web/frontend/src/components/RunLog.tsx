import React, { useEffect, useState, useRef } from 'react'
import { Activity, CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'

interface RunLogProps {
  sessionId: string
  onComplete: (metrics: any) => void
}

interface LogEntry {
  timestamp: string
  event: string
  data: any
}

const RunLog: React.FC<RunLogProps> = ({ sessionId, onComplete }) => {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState({ completed: 0, total: 0 })
  const logEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    startExecution()
  }, [sessionId])

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const startExecution = async () => {
    try {
      // Start execution
      const response = await fetch('/run/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, parallel: true })
      })

      if (response.ok) {
        setIsRunning(true)
        connectToStream()
      }
    } catch (error) {
      console.error('Failed to start execution:', error)
    }
  }

  const connectToStream = () => {
    const eventSource = new EventSource(`/run/stream/${sessionId}`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.event === 'heartbeat') {
          return // Ignore heartbeats
        }

        const logEntry: LogEntry = {
          timestamp: new Date().toLocaleTimeString(),
          event: data.event,
          data: data.data
        }

        setLogs(prev => [...prev, logEntry])

        // Update progress
        if (data.event === 'task_complete') {
          setProgress(prev => ({ ...prev, completed: prev.completed + 1 }))
        } else if (data.event === 'task_start' && data.data.total) {
          setProgress(prev => ({ ...prev, total: data.data.total }))
        } else if (data.event === 'execution_complete') {
          setIsRunning(false)
          eventSource.close()
          onComplete(data.data)
        }
      } catch (error) {
        console.error('Failed to parse event:', error)
      }
    }

    eventSource.onerror = () => {
      setIsRunning(false)
      eventSource.close()
    }
  }

  const getEventIcon = (event: string) => {
    switch (event) {
      case 'task_complete':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'task_failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'budget_warning':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case 'task_start':
        return <Clock className="h-4 w-4 text-blue-500" />
      default:
        return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const formatEventName = (event: string) => {
    return event.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Activity className="h-6 w-6 text-primary-600" />
          <h3 className="text-lg font-semibold">Execution Log</h3>
        </div>
        {isRunning && (
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
            <span className="text-sm text-gray-600">Running...</span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {progress.total > 0 && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{progress.completed} / {progress.total} tasks</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(progress.completed / progress.total) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Log Entries */}
      <div className="bg-gray-50 rounded-lg p-3 h-96 overflow-y-auto">
        {logs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <Activity className="h-8 w-8 mx-auto mb-2 animate-pulse" />
            <p>Waiting for execution to start...</p>
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((log, idx) => (
              <div
                key={idx}
                className="flex items-start space-x-2 text-sm bg-white rounded p-2"
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getEventIcon(log.event)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">{log.timestamp}</span>
                    <span className="font-medium text-gray-700">
                      {formatEventName(log.event)}
                    </span>
                  </div>
                  {log.data && (
                    <div className="text-gray-600 mt-1">
                      {log.data.description || log.data.message || 
                       (log.data.task_id && `Task: ${log.data.task_id}`) ||
                       JSON.stringify(log.data).substring(0, 100)}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        )}
      </div>

      {/* Summary Stats */}
      {!isRunning && logs.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-lg font-semibold text-green-600">
                {logs.filter(l => l.event === 'task_complete').length}
              </p>
              <p className="text-sm text-gray-600">Completed</p>
            </div>
            <div>
              <p className="text-lg font-semibold text-red-600">
                {logs.filter(l => l.event === 'task_failed').length}
              </p>
              <p className="text-sm text-gray-600">Failed</p>
            </div>
            <div>
              <p className="text-lg font-semibold text-yellow-600">
                {logs.filter(l => l.event === 'budget_warning').length}
              </p>
              <p className="text-sm text-gray-600">Warnings</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RunLog