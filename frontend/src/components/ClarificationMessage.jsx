import { useState } from "react";

/**
 * ClarificationMessage
 * Props:
 *   question: string  — pregunta de clarificación del backend
 *   onAnswer(q)       — ejecuta la respuesta como nueva consulta
 *   onCancel()        — vuelve al estado inicial (limpia el resultado)
 */
export default function ClarificationMessage({ question, onAnswer, onCancel }) {
  const [answer, setAnswer] = useState("");

  const puedeResponder = answer.trim().length > 0;

  function handleResponder() {
    if (!puedeResponder) return;
    onAnswer(answer.trim());
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") handleResponder();
  }

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
      {/* Encabezado */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-amber-500">
          <IconoPregunta />
        </span>
        <p className="text-sm font-medium text-amber-800">
          Necesito más información
        </p>
      </div>

      {/* Pregunta del backend*/}
      <p className="text-sm font-semibold text-amber-800 ml-6 mb-4">
        {question}
      </p>

      {/* Input de respuesta */}
      <div className="ml-6 space-y-3">
        <input
          type="text"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribí tu respuesta..."
          autoFocus
          className={[
            "w-full rounded-lg border px-3 py-2 text-sm text-gray-900",
            "placeholder-gray-400 bg-white transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent",
            "border-amber-300",
          ].join(" ")}
        />

        <div className="flex items-center gap-2">
          <button
            onClick={handleResponder}
            disabled={!puedeResponder}
            className={[
              "px-4 py-1.5 rounded-lg text-sm font-medium transition-colors",
              puedeResponder
                ? "bg-amber-500 text-white hover:bg-amber-600 active:bg-amber-700"
                : "bg-amber-100 text-amber-300 cursor-not-allowed",
            ].join(" ")}
          >
            Responder
          </button>

          <button
            onClick={onCancel}
            className="px-4 py-1.5 rounded-lg text-sm font-medium text-amber-700 hover:bg-amber-100 active:bg-amber-200 transition-colors"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}

function IconoPregunta() {
  return (
    <svg
      className="w-4 h-4"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"
      />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}
