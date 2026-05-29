import { useState } from "react";

/**
 * SqlViewer
 * Props:
 *   sql: string | null — query SQL generada por el backend
 *
 * Bloque colapsable (por defecto cerrado) con el SQL y botón de copia.
 */
export default function SqlViewer({ sql }) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!sql) return null;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // navigator.clipboard puede fallar en contextos sin HTTPS
    }
  }

  return (
    <div className="rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      {/* Botón de colapsar*/}
      <button
        onClick={() => setIsOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-white hover:bg-gray-50 transition-colors text-sm text-gray-600 font-medium"
      >
        <span className="flex items-center gap-2">
          <SqlIcon />
          SQL generado
        </span>
        <span className="text-gray-400 text-xs">
          {isOpen ? "▲ Ocultar" : "▼ Ver"}
        </span>
      </button>

      {isOpen && (
        <div className="border-t border-gray-200">
          {/* Barra superior del bloque de código */}
          <div className="flex items-center justify-between px-4 py-2 bg-[#0f172a]">
            <span className="text-xs text-gray-500 font-mono">SQL</span>
            <button
              onClick={handleCopy}
              className={[
                "text-xs px-3 py-1 rounded border transition-all font-medium",
                copied
                  ? "border-green-500 text-green-400 bg-green-500/10"
                  : "border-gray-600 text-gray-400 hover:border-gray-400 hover:text-gray-200",
              ].join(" ")}
            >
              {copied ? "¡Copiado!" : "Copiar"}
            </button>
          </div>

          {/* Bloque de código */}
          <pre
            className="bg-[#1e293b] text-gray-100 px-4 py-4 overflow-x-auto text-sm leading-relaxed"
            style={{ fontFamily: "'Courier New', Courier, monospace" }}
          >
            <code>{sql}</code>
          </pre>
        </div>
      )}
    </div>
  );
}

function SqlIcon() {
  return (
    <svg
      className="w-4 h-4 text-gray-400"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"
      />
    </svg>
  );
}
