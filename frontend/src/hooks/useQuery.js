import { useState } from 'react'

/**
 * useQuery
 * Centraliza todo el estado de la aplicación:
 *   question      — valor actual del textarea (controlado desde aquí)
 *   setQuestion   — para rellenar el textarea desde el historial
 *   result        — última respuesta del backend (o null)
 *   isLoading     — true mientras espera la respuesta
 *   history       — últimas 10 consultas [ { question, result, timestamp } ]
 *   executeQuery  — lanza el fetch y actualiza result + history
 */

const MAX_HISTORY = 10

export function useQuery() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState([])

  async function executeQuery(q) {
    setIsLoading(true)

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      setResult(data)

      // Agregar al historial (más reciente primero, máximo MAX_HISTORY)
      const entry = { question: q, result: data, timestamp: Date.now() }
      setHistory((prev) => [entry, ...prev].slice(0, MAX_HISTORY))

    } catch {
      const networkError = {
        sql: null,
        columns: [],
        data: [],
        chart_type: null,
        chart_config: null,
        error: {
          type: 'NETWORK_ERROR',
          message: 'No se pudo conectar con el servidor. Verificá tu conexión.',
        },
        clarification_needed: false,
        clarification_question: null,
      }
      setResult(networkError)

      // Los errores de red también se agregan al historial para trazabilidad
      const entry = { question: q, result: networkError, timestamp: Date.now() }
      setHistory((prev) => [entry, ...prev].slice(0, MAX_HISTORY))

    } finally {
      setIsLoading(false)
    }
  }

  function clearResult() {
    setResult(null)
  }

  return { question, setQuestion, result, isLoading, history, executeQuery, clearResult }
}
