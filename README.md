# Text-to-SQL Dashboard

Sistema que traduce preguntas en lenguaje natural a consultas SQL, las ejecuta contra una base de datos PostgreSQL con el dataset de e-commerce brasileño Olist, y presenta los resultados en visualizaciones automáticas.

---

## Stack

| Capa          | Tecnología                             |
| ------------- | -------------------------------------- |
| Frontend      | React + Vite + Recharts + Tailwind CSS |
| Backend       | FastAPI (Python 3.11)                  |
| LLM           | Gemini 1.5 Flash                       |
| Base de datos | PostgreSQL 15 con dataset Olist        |
| Orquestación  | Docker Compose                         |

---

## Inicio rápido

### Pre-requisitos

- Docker y Docker Compose
- API key de Gemini ([obtener aquí](https://aistudio.google.com/))

### 1. Clonar y configurar variables de entorno

```bash
git clone <repo-url>
cd text-to-sql
cp .env.example .env
```

Editar `.env` y completar `GEMINI_API_KEY`.

### 2. Levantar todo

```bash
docker compose up --build
```

### 3. Abrir

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

---

## API

### POST /api/query

Traduce una pregunta en lenguaje natural a SQL y devuelve los resultados.

**Request**

```json
{ "question": "¿Cuáles fueron las 10 categorías más vendidas en 2018?" }
```

**Response (éxito)**

```json
{
  "sql": "SELECT p.product_category_name, COUNT(*) as total ...",
  "columns": ["product_category_name", "total"],
  "data": [{ "product_category_name": "cama_mesa_banho", "total": 11115 }],
  "chart_type": "bar",
  "chart_config": { "x_key": "product_category_name", "y_key": "total" },
  "error": null
}
```

**Response (error)**

```json
{
  "sql": null,
  "columns": [],
  "data": [],
  "error": {
    "type": "UNSAFE_QUERY",
    "message": "Esta consulta no está permitida."
  }
}
```

**Response (clarificación)**

```json
{
  "clarification_needed": true,
  "clarification_question": "¿Te referís a ventas por cantidad de órdenes o por monto total?"
}
```

### GET /api/health

```json
{ "status": "ok", "db": "connected", "llm": "available" }
```

---

## Seguridad

Ninguna query que no sea `SELECT` llega a la base de datos:

1. El prompt instruye al LLM a responder `ERROR_UNSAFE_QUERY` si detecta intención de escritura.
2. El sanitizer valida que el SQL recibido empiece con `SELECT` y no contenga keywords peligrosas (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `EXEC`).
3. Las queries se ejecutan con timeout de 10 segundos (enforced en PostgreSQL).

---

## Dataset

**Olist Brazilian E-Commerce** — 9 tablas, ~100.000 filas.

```
orders · customers · order_items · products · sellers
order_payments · order_reviews · product_category_name_translation · geolocation
```

El schema se extrae automáticamente al iniciar el backend y se cachea en memoria con ejemplos de valores reales por columna.

---

## Preguntas de ejemplo

```
¿Cuántas órdenes hay por estado de entrega?
¿Cuál es el ticket promedio por estado de Brasil?
Top 10 categorías de productos más vendidas
¿Cómo evolucionaron las ventas mes a mes en 2018?
¿Cuál es el puntaje promedio de reseñas por categoría?
¿Cuántos vendedores hay por estado?
¿Qué método de pago se usa más?
¿Cuál es el tiempo promedio de entrega en días?
```

---

## Estado de implementación

### Fase 1 — Backend (Hecho)

- [x] Estructura de carpetas y Docker Compose
- [x] Schema Loader: extracción automática + cache con ejemplos de valores
- [x] Sanitizer: validación de seguridad con 13 casos de test
- [x] LLM Service: integración Gemini 1.5 Flash + prompt con few-shot examples
- [x] DB Service: ejecución con timeout de 10s + serialización de tipos
- [x] Router `/api/query`: pipeline completo con reintento automático
- [x] Router `/api/health`: estado de DB y LLM

### Fase 2 — Frontend (en desarrollo)

- [x] Setup React + Vite
- [x] QueryInput: textarea + botón + loading state
- [x] ResultTable: tabla paginada
- [x] SqlViewer: SQL expandible y copiable
- [x] QueryHistory: historial de sesión

### Fase 3 — Visualizaciones (en desarrollo)

- [x] Chart Service: decisión automática de tipo de gráfico
- [x] ChartRenderer: Bar, Line, Pie, KPI con Recharts
- [x] ErrorMessage: mensajes por tipo de error
- [x] Manejo de clarificaciones en UI

### Fase 4 — Pulido (en desarrollo)

- [ ] UI polish + preguntas de ejemplo precargadas
- [ ] README con demo GIF
- [ ] Few-shot examples mejorados con preguntas reales testeadas

---

## Estructura del repositorio

```
text-to-sql/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── main.py                  ← FastAPI app + CORS
│   ├── routers/
│   │   └── query.py             ← POST /api/query, GET /api/health
│   ├── services/
│   │   ├── llm_service.py       ← llamada a Gemini + limpieza de respuesta
│   │   ├── db_service.py        ← ejecución con timeout + serialización
│   │   └── sanitizer.py        ← validación de seguridad SQL
│   ├── prompts/
│   │   └── sql_prompt.py        ← template del prompt (separado de la lógica)
│   └── schema/
│       └── schema_loader.py     ← extracción y cache del schema
└── frontend/
    └── src/
        ├── components/          ← (pendiente Fase 2)
        └── hooks/               ← (pendiente Fase 2)
```
