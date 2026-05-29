# Text-to-SQL Dashboard — Project Spec

> **Fuente de verdad del proyecto. Leer antes de cualquier tarea.**

---

## 1. Descripción General

Sistema que traduce preguntas en lenguaje natural a consultas SQL válidas, las ejecuta contra una base de datos PostgreSQL, y presenta los resultados en visualizaciones automáticas (tablas y gráficos).

**Problema que resuelve:** Las bases de datos relacionales contienen información valiosa pero acceder a ella requiere conocer SQL. Este sistema permite a cualquier usuario hacer preguntas en español o inglés y obtener respuestas visuales sin escribir una sola línea de código.

**Entorno:** Local con Docker. No hay deploy por ahora.

---

## 2. Usuarios Objetivo

- Analistas de negocio sin conocimiento técnico
- Product managers que quieren explorar datos sin depender de un dev
- Cualquier equipo con una base de datos y preguntas frecuentes sobre sus datos

---

## 3. Scope

### Dentro del MVP

- Traducir preguntas en lenguaje natural (español e inglés) a SQL válido
- Ejecutar queries de forma segura contra PostgreSQL (solo SELECT)
- Mostrar resultados en tabla + gráfico automático según el tipo de dato
- Historial de consultas de la sesión (en memoria, no persistido)
- Manejo de errores con feedback claro al usuario
- SQL generado siempre visible y copiable

### Fuera del MVP (mejoras futuras documentadas)

- Autenticación de usuarios
- Multi-tenant (cada usuario conecta su propia DB)
- Queries de escritura (INSERT, UPDATE, DELETE)
- Fine-tuning del modelo
- Deploy en la nube

---

## 4. Stack Tecnológico

| Capa          | Tecnología       | Versión / Notas                          |
| ------------- | ---------------- | ---------------------------------------- |
| Frontend      | React + Vite     | Con Recharts para visualizaciones        |
| Backend       | FastAPI          | Python 3.11+                             |
| LLM           | Gemini 1.5 Flash | Via `google-generativeai` SDK            |
| Base de datos | PostgreSQL       | 15, contenedor Docker                    |
| Orquestación  | Docker Compose   | Un solo `docker compose up` levanta todo |
| Estilos       | Tailwind CSS     |                                          |

### Puertos locales

- Frontend: `localhost:5173`
- Backend: `localhost:8000`
- PostgreSQL: `localhost:5432`

---

## 5. Dataset

**Olist Brazilian E-Commerce** (Kaggle, público y gratuito)

9 tablas con más de 100.000 filas. Dominio de e-commerce: órdenes, productos, clientes, vendedores, pagos, reseñas y geolocalización.

### Tablas principales

```
orders          (order_id, customer_id, order_status, order_purchase_timestamp,
                 order_delivered_customer_date, order_estimated_delivery_date)

customers       (customer_id, customer_unique_id, customer_zip_code_prefix,
                 customer_city, customer_state)

order_items     (order_id, order_item_id, product_id, seller_id,
                 shipping_limit_date, price, freight_value)

products        (product_id, product_category_name, product_name_lenght,
                 product_description_lenght, product_photos_qty,
                 product_weight_g, product_length_cm, product_height_cm,
                 product_width_cm)

sellers         (seller_id, seller_zip_code_prefix, seller_city, seller_state)

order_payments  (order_id, payment_sequential, payment_type,
                 payment_installments, payment_value)

order_reviews   (review_id, order_id, review_score, review_comment_title,
                 review_comment_message, review_creation_date,
                 review_answer_timestamp)

product_category_name_translation
                (product_category_name, product_category_name_english)

geolocation     (geolocation_zip_code_prefix, geolocation_lat, geolocation_lng,
                 geolocation_city, geolocation_state)
```

### Relaciones clave

- `orders.customer_id` → `customers.customer_id`
- `order_items.order_id` → `orders.order_id`
- `order_items.product_id` → `products.product_id`
- `order_items.seller_id` → `sellers.seller_id`
- `order_payments.order_id` → `orders.order_id`
- `order_reviews.order_id` → `orders.order_id`
- `products.product_category_name` → `product_category_name_translation.product_category_name`

---

## 6. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│                  FRONTEND (React)                    │
│                                                      │
│  [Input lenguaje natural]   [Historial de queries]  │
│  [Tabla de resultados]      [Visualización auto]    │
│  [SQL generado visible]     [Feedback de error]     │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / REST
┌────────────────────▼────────────────────────────────┐
│                 BACKEND (FastAPI)                    │
│                                                      │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │Query Router │ │ SQL Executor │ │  Sanitizer   │  │
│  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘  │
│  ┌──────▼──────┐ ┌──────▼───────┐        │          │
│  │ LLM Service │ │  DB Service  │◄───────┘          │
│  │  (Gemini)   │ │ (PostgreSQL) │                   │
│  └──────┬──────┘ └──────┬───────┘                   │
│  ┌──────▼──────┐ ┌──────▼───────┐                   │
│  │Schema Cache │ │Result Format.│                   │
│  └─────────────┘ └──────────────┘                   │
└─────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│            PostgreSQL (contenedor Docker)            │
│              Dataset Olist cargado                   │
└─────────────────────────────────────────────────────┘
```

---

## 7. Flujo de una Consulta — Happy Path

```
1. Usuario escribe pregunta en lenguaje natural
2. Frontend → POST /api/query { "question": "..." }
3. Backend extrae schema cacheado (tablas + columnas + ejemplos de valores)
4. LLM Service construye el prompt y llama a Gemini
5. Gemini devuelve SQL
6. Sanitizer valida que sea un SELECT seguro
7. DB Service ejecuta la query con timeout de 10s
8. Chart Service analiza el resultado y decide el tipo de gráfico
9. Backend devuelve { sql, columns, data, chart_type, chart_config }
10. Frontend renderiza tabla + gráfico + SQL expandible
```

---

## 8. Flujo de Error — Casos No Felices

### A. SQL inválido (falla en ejecución)

- Reintentar **una sola vez** pasando el error de PostgreSQL de vuelta al LLM
- Si el segundo intento también falla → devolver error al usuario
- Nunca más de un reintento (costo + latencia)

### B. Query peligrosa (sanitizer la rechaza)

- No llega a la DB nunca
- Respuesta inmediata: `{ error: "UNSAFE_QUERY", message: "..." }`

### C. Query ambigua (LLM no puede generar SQL confiable)

- El LLM devuelve `CLARIFICATION_NEEDED: <pregunta>`
- El backend lo detecta y devuelve `{ clarification_needed: true, question: "..." }`
- El frontend lo muestra como sugerencia, no como error

### D. Sin resultados

- La query fue válida y ejecutó, pero devolvió 0 filas
- No es un error: devolver `{ columns, data: [], message: "La consulta no devolvió resultados" }`

### E. Error de red / LLM no disponible

- Timeout o fallo de la API de Gemini
- Devolver `{ error: "LLM_ERROR", message: "Hubo un problema al procesar la pregunta, intentá de nuevo" }`

---

## 9. API Contract

### POST /api/query

**Request:**

```json
{
  "question": "¿Cuáles fueron los 5 productos más vendidos en 2018?"
}
```

**Response (éxito):**

```json
{
  "sql": "SELECT p.product_category_name, COUNT(*) as total ...",
  "columns": ["product_category_name", "total"],
  "data": [{ "product_category_name": "cama_mesa_banho", "total": 11115 }],
  "chart_type": "bar",
  "chart_config": {
    "x_key": "product_category_name",
    "y_key": "total"
  },
  "error": null
}
```

**Response (error):**

```json
{
  "sql": null,
  "columns": [],
  "data": [],
  "chart_type": null,
  "chart_config": null,
  "error": {
    "type": "UNSAFE_QUERY",
    "message": "Esta consulta no está permitida."
  }
}
```

**Response (clarificación):**

```json
{
  "sql": null,
  "columns": [],
  "data": [],
  "chart_type": null,
  "chart_config": null,
  "clarification_needed": true,
  "clarification_question": "¿Te referís a ventas por cantidad de órdenes o por monto total en reales?"
}
```

### GET /api/health

```json
{ "status": "ok", "db": "connected", "llm": "available" }
```

---

## 10. Diseño del Prompt

El prompt es la pieza más crítica del sistema. Estructura obligatoria:

```
[SYSTEM]
Eres un experto en SQL y en la base de datos Olist de e-commerce brasileño.
Tu única tarea es generar consultas SQL válidas para PostgreSQL.
Responde ÚNICAMENTE con la query SQL, sin explicaciones, sin bloques markdown, sin backticks.
NUNCA generes INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, EXEC
ni ninguna operación que no sea SELECT.
Si la pregunta requiere modificar datos, responde exactamente: ERROR_UNSAFE_QUERY
Si la pregunta es ambigua o no podés generar SQL confiable, responde exactamente:
CLARIFICATION_NEEDED: <tu pregunta de clarificación en el mismo idioma del usuario>

[SCHEMA]
{schema_completo_con_ejemplos_de_valores}

[EXAMPLES]
Q: ¿Cuántas órdenes hay por estado?
A: SELECT order_status, COUNT(*) as total FROM orders GROUP BY order_status ORDER BY total DESC

Q: Total facturado por mes en 2018
A: SELECT DATE_TRUNC('month', order_purchase_timestamp) as mes, SUM(payment_value) as total
   FROM orders o JOIN order_payments op ON o.order_id = op.order_id
   WHERE EXTRACT(YEAR FROM order_purchase_timestamp) = 2018
   GROUP BY mes ORDER BY mes

Q: Top 5 categorías con mejor puntaje promedio de reseñas
A: SELECT pct.product_category_name_english, AVG(r.review_score) as avg_score
   FROM order_reviews r
   JOIN order_items oi ON r.order_id = oi.order_id
   JOIN products p ON oi.product_id = p.product_id
   JOIN product_category_name_translation pct ON p.product_category_name = pct.product_category_name
   GROUP BY pct.product_category_name_english
   ORDER BY avg_score DESC LIMIT 5

[QUESTION]
{pregunta_del_usuario}
```

---

## 11. Lógica de Visualización Automática

El Chart Service en el backend decide el tipo de gráfico según la estructura del resultado:

| Estructura del resultado                  | Tipo de gráfico | chart_config              |
| ----------------------------------------- | --------------- | ------------------------- |
| 1 columna numérica, 1 fila                | `kpi`           | `{ value_key }`           |
| 1 col. texto + 1 col. numérica            | `bar`           | `{ x_key, y_key }`        |
| 1 col. fecha/timestamp + 1 col. numérica  | `line`          | `{ x_key, y_key }`        |
| 1 col. texto + 1 col. numérica (≤6 filas) | `pie`           | `{ name_key, value_key }` |
| 2+ columnas numéricas + 1 texto           | `multibar`      | `{ x_key, y_keys: [] }`   |
| Cualquier otra combinación                | `table`         | `null`                    |

**Regla de pie chart:** solo si tiene 6 o menos categorías. Más de 6 → bar chart.

---

## 12. Estructura del Repositorio

```
text-to-sql/
├── SPEC.md                          ← este archivo
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                      ← entry point FastAPI, CORS config
│   ├── routers/
│   │   └── query.py                 ← POST /api/query, GET /api/health
│   ├── services/
│   │   ├── llm_service.py           ← prompt builder + llamada a Gemini
│   │   ├── db_service.py            ← ejecución de queries + timeout
│   │   ├── sanitizer.py             ← validación de seguridad SQL
│   │   └── chart_service.py         ← lógica de decisión de visualización
│   ├── prompts/
│   │   └── sql_prompt.py            ← templates del prompt
│   └── schema/
│       └── schema_loader.py         ← extracción y cache del schema
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js               ← proxy a backend en /api
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── QueryInput.jsx        ← textarea + botón + loading state
│       │   ├── ResultTable.jsx       ← tabla paginada de resultados
│       │   ├── ChartRenderer.jsx     ← switch de chart_type → componente Recharts
│       │   ├── SqlViewer.jsx         ← bloque colapsable con syntax highlight
│       │   ├── QueryHistory.jsx      ← lista de preguntas anteriores
│       │   └── ErrorMessage.jsx      ← feedback de errores y clarificaciones
│       └── hooks/
│           └── useQuery.js           ← lógica de fetch + estado
│
└── scripts/
    └── load_olist.py                 ← script one-time para cargar el dataset
```

---

## 13. Variables de Entorno

```env
# .env.example

# Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# PostgreSQL
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=olist
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Construida automáticamente en el backend
DATABASE_URL=postgresql://postgres:postgres@db:5432/olist
```

---

## 14. Docker Compose

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: olist
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
```

---

## 15. Requisitos No Funcionales

| Atributo       | Requisito                                            |
| -------------- | ---------------------------------------------------- |
| Latencia       | Respuesta end-to-end en menos de 8 segundos          |
| Seguridad      | Ninguna query que no sea SELECT llega a la DB, nunca |
| Timeout DB     | Máximo 10 segundos por query                         |
| Reintentos LLM | Máximo 1 reintento por request                       |
| Transparencia  | El SQL generado siempre es visible y copiable        |
| Resiliencia    | Si el LLM falla, mensaje claro — no pantalla rota    |
| Sin estado     | Cada request es independiente                        |
| CORS           | Backend acepta requests desde `localhost:5173`       |

---

## 16. Reglas de Seguridad — Sanitizer

El sanitizer debe rechazar cualquier query que:

1. No empiece con `SELECT` (ignorando whitespace y case)
2. Contenga como palabra entera (no substring): `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `EXEC`, `EXECUTE`
3. Contenga `--` seguido de contenido que modifique el comportamiento (comentarios de bypass)
4. Contenga múltiples statements separados por `;`

**Edge cases a testear:**

- `select * from orders` → ✅ válido
- `  SELECT * FROM orders  ` → ✅ válido (whitespace)
- `SELECT * FROM orders; DROP TABLE orders` → ❌ múltiples statements
- `SELECT 'DROP TABLE' FROM orders` → ✅ válido (string literal)
- `drop table orders` → ❌ peligroso
- `SELECT * FROM orders -- DROP TABLE` → analizar con cuidado

---

## 17. Plan de Implementación

### Fase 1 — Core Backend (~1 semana)

- [x] 1.1 Setup: estructura de carpetas, docker-compose, .env.example
- [x] 1.2 Schema Loader: extracción automática + cache + ejemplos de valores
- [x] 1.3 Sanitizer: validación de seguridad + tests inline
- [x] 1.4 LLM Service: integración Gemini + construcción del prompt
- [x] 1.5 DB Service: ejecución de queries + timeout
- [x] 1.6 Router /api/query: pipeline completo + retry logic

### Fase 2 — Frontend Base (~4-5 días)

- [x] 2.1 Setup React + Vite + proxy a backend
- [x] 2.2 QueryInput: textarea + botón + loading state
- [x] 2.3 ResultTable: tabla paginada + manejo de vacío
- [x] 2.4 SqlViewer: bloque colapsable + copy to clipboard
- [x] 2.5 QueryHistory: historial de sesión en memoria

### Fase 3 — Inteligencia (~4-5 días)

- [x] 3.1 Chart Service (backend): lógica de decisión de gráfico
- [x] 3.2 ChartRenderer (frontend): Bar, Line, Pie, KPI, fallback tabla
- [x] 3.3 Retry con autocorrección (ya definido en el router, pulir)
- [x] 3.4 Manejo de ambigüedad: clarification_needed en UI
- [x] 3.5 ErrorMessage: mensajes por tipo de error

### Fase 4 — Pulido Final (~2-3 días)

- [ ] 4.1 Docker Compose completo con health checks
- [ ] 4.2 UI polish con Tailwind + preguntas de ejemplo precargadas
- [ ] 4.3 README profesional con demo GIF y 3 pasos de instalación
- [ ] 4.4 Few-shot examples del prompt mejorados con preguntas reales testeadas

---

## 18. Preguntas de Ejemplo para Demo

Estas preguntas están validadas para funcionar bien con el dataset Olist:

```
- ¿Cuántas órdenes hay por estado de entrega?
- ¿Cuál es el ticket promedio por estado de Brasil?
- Top 10 categorías de productos más vendidas
- ¿Cómo evolucionaron las ventas mes a mes en 2018?
- ¿Cuál es el puntaje promedio de reseñas por categoría de producto?
- ¿Cuántos vendedores hay por estado?
- ¿Qué método de pago se usa más?
- ¿Cuál es el tiempo promedio de entrega en días?
```

---

_Última actualización: 26/5_
