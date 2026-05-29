import { useQuery } from "./hooks/useQuery";
import QueryInput from "./components/QueryInput";
import QueryHistory from "./components/QueryHistory";
import SqlViewer from "./components/SqlViewer";
import ChartRenderer from "./components/ChartRenderer";
import ResultTable from "./components/ResultTable";

// Preguntas de ejemplo del SPEC #18 para el estado inicial
const EXAMPLE_QUESTIONS = [
  "¿Cuántas órdenes hay por estado de entrega?",
  "¿Cuál es el ticket promedio por estado de Brasil?",
  "Top 10 categorías de productos más vendidas",
  "¿Cómo evolucionaron las ventas mes a mes en 2018?",
];

export default function App() {
  const { question, setQuestion, result, isLoading, history, executeQuery } =
    useQuery();

  function handleSubmit(q) {
    executeQuery(q);
  }

  function handleSelectHistory(q) {
    setQuestion(q);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Columna izquierda: input + historial */}
          <div className="lg:col-span-1 space-y-4">
            <QueryInput
              value={question}
              onChange={setQuestion}
              onSubmit={handleSubmit}
              isLoading={isLoading}
            />
            <QueryHistory history={history} onSelect={handleSelectHistory} />
          </div>

          {/* Columna derecha: resultados */}
          <div className="lg:col-span-2 space-y-4">
            <ResultArea result={result} isLoading={isLoading} />
          </div>
        </div>
      </main>
    </div>
  );
}

function Header() {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm px-6 py-4">
      <h1 className="text-xl font-semibold text-gray-900">
        Text-to-SQL Dashboard
      </h1>
      <p className="text-sm text-gray-500 mt-0.5">
        Consultá tu base de datos en lenguaje natural
      </p>
    </header>
  );
}

function ResultArea({ result, isLoading }) {
  // Estado de carga
  if (isLoading) {
    return <ResultTable isLoading={true} />;
  }

  // Estado inicial: sin query todavía
  if (!result) {
    return <WelcomePanel />;
  }

  // Error del backend
  if (result.error) {
    return (
      <ErrorBanner type={result.error.type} message={result.error.message} />
    );
  }

  // El LLM pide clarificación
  if (result.clarification_needed) {
    return <ClarificationBanner question={result.clarification_question} />;
  }

  // Resultado con datos (o sin filas — ResultTable lo maneja)
  return (
    <>
      <SqlViewer sql={result.sql} />
      {result.chart_type && result.chart_type !== "table" && (
        <ChartRenderer
          chart_type={result.chart_type}
          chart_config={result.chart_config}
          data={result.data}
          columns={result.columns}
        />
      )}
      <ResultTable
        columns={result.columns}
        data={result.data}
        isLoading={false}
      />
    </>
  );
}

// Estado inicial
function WelcomePanel() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <h2 className="text-sm font-medium text-gray-700 mb-1">¿Cómo empezar?</h2>
      <p className="text-sm text-gray-500 mb-4">
        Escribí una pregunta sobre el dataset de e-commerce Olist. Por ejemplo:
      </p>
      <ul className="space-y-2">
        {EXAMPLE_QUESTIONS.map((q) => (
          <li key={q} className="flex items-start gap-2 text-sm text-gray-600">
            <span className="text-blue-400 mt-0.5 flex-shrink-0">›</span>
            <span className="italic">{q}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ErrorBanner({ type, message }) {
  const isTimeout = type === "DB_ERROR" && message.includes("10 segundos");

  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-red-500">
          <ErrorIcon />
        </span>
        <p className="text-sm font-medium text-red-800">
          {isTimeout ? "La consulta tardó demasiado" : "Ocurrió un error"}
        </p>
      </div>
      <p className="text-sm text-red-600 ml-6">{message}</p>
      {type === "LLM_ERROR" && (
        <p className="text-xs text-red-400 ml-6 mt-2">
          Intentá de nuevo en unos segundos.
        </p>
      )}
    </div>
  );
}

function ClarificationBanner({ question }) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-yellow-500">
          <InfoIcon />
        </span>
        <p className="text-sm font-medium text-yellow-800">
          Necesito más información
        </p>
      </div>
      <p className="text-sm text-yellow-700 ml-6">{question}</p>
      <p className="text-xs text-yellow-500 ml-6 mt-2">
        Reformulá tu pregunta con más detalle en el campo de arriba.
      </p>
    </div>
  );
}

function ErrorIcon() {
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
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

function InfoIcon() {
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
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  );
}
