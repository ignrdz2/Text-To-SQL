/**
 * ErrorMessage
 * Props:
 *   error: { type: string, message: string } | null
 *
 * Devuelve null si error es null.
 * Mapea tipos conocidos a mensajes amigables; tipos desconocidos muestran
 * el error.message del backend directamente.
 */

// Mensajes por tipo de error
const MENSAJES = {
  UNSAFE_QUERY: {
    titulo: "Consulta no permitida",
    mensaje:
      "Esta pregunta implicaría modificar datos, lo cual no está habilitado. " +
      "Intentá reformular tu pregunta para obtener información.",
  },
  LLM_ERROR: {
    titulo: "Error al procesar la pregunta",
    mensaje:
      "Hubo un problema al interpretar tu pregunta. " +
      "Intentá de nuevo o reformulá con más detalle.",
  },
  DB_ERROR: {
    titulo: "Error al ejecutar la consulta",
    mensaje:
      "La consulta generada no pudo ejecutarse. " +
      "Si el problema persiste, intentá hacer la pregunta de otra forma.",
  },
};

export default function ErrorMessage({ error }) {
  if (!error) return null;

  const config = MENSAJES[error.type];
  const titulo = config ? config.titulo : "Algo salió mal";
  const mensaje = config ? config.mensaje : error.message;

  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-red-500">
          <IconoError />
        </span>
        <p className="text-sm font-semibold text-red-800">{titulo}</p>
      </div>
      <p className="text-sm text-red-700 ml-6">{mensaje}</p>
    </div>
  );
}

function IconoError() {
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
