import React, { useState, useEffect } from 'react'
import { MessageCircle, Send } from 'lucide-react'

interface StartupQAProps {
  sessionId: string
  onComplete: () => void
}

const StartupQA: React.FC<StartupQAProps> = ({ sessionId, onComplete }) => {
  const [questions, setQuestions] = useState<string[]>([])
  const [answers, setAnswers] = useState<string[]>([])
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchQuestions()
  }, [sessionId])

  const fetchQuestions = async () => {
    try {
      const response = await fetch(`/startup/questions?session_id=${sessionId}`)
      if (response.ok) {
        const data = await response.json()
        setQuestions(data.questions)
      }
    } catch (error) {
      console.error('Failed to fetch questions:', error)
    }
  }

  const handleAnswerSubmit = () => {
    if (currentAnswer.trim()) {
      const newAnswers = [...answers, currentAnswer]
      setAnswers(newAnswers)
      setCurrentAnswer('')
      
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1)
      } else {
        submitAllAnswers(newAnswers)
      }
    }
  }

  const submitAllAnswers = async (allAnswers: string[]) => {
    setLoading(true)
    try {
      const response = await fetch('/startup/answers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          answers: allAnswers
        })
      })

      if (response.ok) {
        onComplete()
      }
    } catch (error) {
      console.error('Failed to submit answers:', error)
    } finally {
      setLoading(false)
    }
  }

  if (questions.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
          <span>Loading questions...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <MessageCircle className="h-8 w-8 text-primary-600" />
          <h2 className="text-2xl font-bold">Discovery Phase</h2>
        </div>

        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">
              Question {currentQuestionIndex + 1} of {questions.length}
            </span>
            <div className="w-48 bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
              />
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Previous answers */}
          {answers.map((answer, idx) => (
            <div key={idx} className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Q{idx + 1}: {questions[idx]}
              </p>
              <p className="text-gray-900">{answer}</p>
            </div>
          ))}

          {/* Current question */}
          {currentQuestionIndex < questions.length && (
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
              <p className="font-medium text-gray-900 mb-4">
                {questions[currentQuestionIndex]}
              </p>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={currentAnswer}
                  onChange={(e) => setCurrentAnswer(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAnswerSubmit()}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Type your answer..."
                  disabled={loading}
                />
                <button
                  onClick={handleAnswerSubmit}
                  disabled={loading || !currentAnswer.trim()}
                  className="btn-primary flex items-center space-x-2"
                >
                  <Send className="h-4 w-4" />
                  <span>Next</span>
                </button>
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Generating PRD...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default StartupQA