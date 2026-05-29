import { useState, useEffect } from "react";

/**
 * ResultTable
 * Props:
 *   columns: string[]   — nombres de columnas del resultado
 *   data:    object[]   — filas como lista de objetos
 *   isLoading: bool     — muestra skeleton mientras espera
 */

const PAGE_SIZE = 10;
const SKELETON_COLS = 4;
const SKELETON_ROWS = 3;

// Formateo de celdas
function formatCell(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    const decimals = value.toString().split(".")[1] ?? "";
    if (decimals.length > 2) return value.toFixed(2);
  }
  return value;
}

// Skeleton mientras carga
function TableSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden animate-pulse">
      <div className="px-4 py-2.5 border-b border-gray-100">
        <div className="h-3.5 w-40 bg-gray-200 rounded" />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-800">
              {Array.from({ length: SKELETON_COLS }).map((_, i) => (
                <th key={i} className="px-4 py-3">
                  <div className="h-3.5 bg-gray-600 rounded w-20" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: SKELETON_ROWS }).map((_, row) => (
              <tr
                key={row}
                className={row % 2 === 0 ? "bg-white" : "bg-gray-50"}
              >
                {Array.from({ length: SKELETON_COLS }).map((_, col) => (
                  <td key={col} className="px-4 py-3">
                    <div className="h-3.5 bg-gray-200 rounded" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PaginationButton({ onClick, disabled, children }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={[
        "px-3 py-1.5 rounded text-xs border transition-colors",
        disabled
          ? "border-gray-200 text-gray-300 cursor-not-allowed"
          : "border-gray-300 text-gray-600 hover:bg-gray-50 active:bg-gray-100",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

export default function ResultTable({ columns = [], data = [], isLoading }) {
  const [page, setPage] = useState(0);

  // Volver a la primera página cuando llegan datos nuevos
  useEffect(() => {
    setPage(0);
  }, [data]);

  if (isLoading) return <TableSkeleton />;

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm px-6 py-10 text-center">
        <p className="text-gray-500 text-sm">
          La consulta no devolvió resultados. Intentá reformular la pregunta.
        </p>
      </div>
    );
  }

  const totalPages = Math.ceil(data.length / PAGE_SIZE);
  const startIdx = page * PAGE_SIZE;
  const endIdx = Math.min(startIdx + PAGE_SIZE, data.length);
  const pageRows = data.slice(startIdx, endIdx);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Contador */}
      <div className="px-4 py-2.5 border-b border-gray-100 text-xs text-gray-500">
        Mostrando {startIdx + 1}–{endIdx} de {data.length} resultado
        {data.length !== 1 ? "s" : ""}
      </div>

      {/* Tabla con scroll horizontal */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="bg-gray-800 text-white">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-3 font-medium whitespace-nowrap tracking-wide text-xs uppercase"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className={[
                  "border-b border-gray-100 last:border-0",
                  rowIdx % 2 === 0 ? "bg-white" : "bg-gray-50",
                ].join(" ")}
              >
                {columns.map((col) => (
                  <td
                    key={col}
                    className="px-4 py-3 text-gray-700 whitespace-nowrap"
                  >
                    {formatCell(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
          <PaginationButton
            onClick={() => setPage((p) => p - 1)}
            disabled={page === 0}
          >
            ← Anterior
          </PaginationButton>

          <span className="text-xs text-gray-400">
            Página {page + 1} de {totalPages}
          </span>

          <PaginationButton
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= totalPages - 1}
          >
            Siguiente →
          </PaginationButton>
        </div>
      )}
    </div>
  );
}
