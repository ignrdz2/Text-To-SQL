import { useState } from 'react'

/**
 * QueryInput
 * Props:
 *   onSubmit(question: string) — llamado al enviar una pregunta no vacía
 *   isLoading: bool            — bloquea textarea y botón mientras espera respuesta
 *   value?: string             — modo controlado (ej: para rellenar desde el historial)
 *   onChange?: (v: string) => void — callback de cambio en modo controlado
 */
export default function QueryInput({ onSubmit, isLoading, value: controlledValue, onChange: controlledOnChange }) {
  const [internalQuestion, setInternalQuestion] = useState('')

  // Modo controlado si se pasan value/onChange; de lo contrario usa estado interno
  const question = controlledValue !== undefined ? controlledValue : internalQuestion
  const setQuestion = controlledOnChange !== undefined ? controlledOnChange : setInternalQuestion

  const canSubmit = question.trim().length > 0 && !isLoading

  function handleSubmit() {
    if (!canSubmit) return
    onSubmit(question.trim())
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit()
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <label htmlFor="query-input" className="block text-sm font-medium text-gray-700 mb-2">
        Hacé tu pregunta
      </label>

      <textarea
        id="query-input"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
        rows={3}
        placeholder="Ej: ¿Cuáles fueron las 5 categorías más vendidas en 2018?"
        className={[
          'w-full resize-none rounded-lg border px-3 py-2.5 text-sm text-gray-900',
          'placeholder-gray-400 transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          isLoading
            ? 'bg-gray-50 border-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-white border-gray-300',
        ].join(' ')}
      />

      <div className="flex items-center justify-between mt-3">
        <span className="text-xs text-gray-400">
          Ctrl + Enter para enviar
        </span>

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className={[
            'px-5 py-2 rounded-lg text-sm font-medium transition-colors',
            canSubmit
              ? 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed',
          ].join(' ')}
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <Spinner />
              Consultando...
            </span>
          ) : (
            'Consultar'
          )}
        </button>
      </div>
    </div>
  )
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4 text-gray-400"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12" cy="12" r="10"
        stroke="currentColor" strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}
