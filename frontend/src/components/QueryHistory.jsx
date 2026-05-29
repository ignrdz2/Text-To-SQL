/**
 * QueryHistory
 * Props:
 *   history:  { question, result, timestamp }[] — del hook useQuery
 *   onSelect: (question: string) => void         — rellena el textarea
 */

function getRelativeTime(timestamp) {
  const diffSec = Math.floor((Date.now() - timestamp) / 1000)
  if (diffSec < 60) return 'ahora mismo'
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `hace ${diffMin} min`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `hace ${diffHour} hora${diffHour !== 1 ? 's' : ''}`
  const diffDay = Math.floor(diffHour / 24)
  return `hace ${diffDay} día${diffDay !== 1 ? 's' : ''}`
}

function truncate(text, maxLen = 60) {
  return text.length > maxLen ? text.slice(0, maxLen).trimEnd() + '…' : text
}

function StatusDot({ result }) {
  if (!result) return null
  if (result.error) return <span className="w-2 h-2 rounded-full bg-red-400 flex-shrink-0 mt-1" />
  if (result.clarification_needed) return <span className="w-2 h-2 rounded-full bg-yellow-400 flex-shrink-0 mt-1" />
  return <span className="w-2 h-2 rounded-full bg-green-400 flex-shrink-0 mt-1" />
}

export default function QueryHistory({ history, onSelect }) {
  if (history.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <h2 className="text-sm font-medium text-gray-700 mb-3">Historial</h2>
        <p className="text-xs text-gray-400 text-center py-4">
          Tus consultas anteriores aparecerán aquí.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <h2 className="text-sm font-medium text-gray-700 mb-3">
        Historial
        <span className="ml-2 text-xs font-normal text-gray-400">
          ({history.length})
        </span>
      </h2>

      <ul className="space-y-1">
        {history.map((entry, idx) => (
          <li key={idx}>
            <button
              onClick={() => onSelect(entry.question)}
              className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-gray-50 active:bg-gray-100 transition-colors group"
            >
              <div className="flex items-start gap-2">
                <StatusDot result={entry.result} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-700 group-hover:text-gray-900 leading-snug break-words">
                    {truncate(entry.question)}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {getRelativeTime(entry.timestamp)}
                  </p>
                </div>
              </div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
