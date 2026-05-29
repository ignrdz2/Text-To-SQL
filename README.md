# Text-to-SQL Dashboard

Consultá una base de datos en lenguaje natural y recibí los resultados en tabla y gráfico automático, sin escribir SQL.

---

Las bases de datos relacionales contienen información valiosa, pero acceder a ella requiere conocer SQL. Este proyecto elimina esa barrera: analistas, product managers o cualquier persona con preguntas sobre sus datos puede obtener respuestas visuales escribiendo en español o inglés. Está construido sobre el dataset público de e-commerce Olist (100k+ órdenes) y corre completamente en local con Docker.

---

## Stack

| Capa          | Tecnología       | Notas                         |
| ------------- | ---------------- | ----------------------------- |
| Frontend      | React + Vite     | Recharts para visualizaciones |
| Backend       | FastAPI          | Python 3.11+                  |
| LLM           | Gemini 2.5 Flash | Via `google-genai` SDK        |
| Base de datos | PostgreSQL 15    | Contenedor Docker             |
| Orquestación  | Docker Compose   | Un solo comando levanta todo  |
| Estilos       | Tailwind CSS     |                               |

---

## Cómo correr el proyecto

**Paso 1 — Clonar el repo y copiar el entorno**

```bash
git clone https://github.com/ignrdz2/Text-To-SQL.git
cd text-to-sql
cp .env.example .env
```

**Paso 2 — Agregar la API key de Gemini al `.env`**

Obtener una key gratuita en [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) y reemplazar el valor en el `.env`:

```
GEMINI_API_KEY=tu_api_key_aquí
```

**Paso 3 — Levantar todo**

```bash
docker compose up --build
```

La primera vez tarda unos minutos en construir las imágenes. Cuando esté listo, abrir [localhost:5173](http://localhost:5173).

> **Primera vez:** la base de datos arranca vacía. Para cargar el dataset Olist, con Docker corriendo, ejecutar una vez:
>
> ```bash
> pip install psycopg2-binary python-dotenv
> python scripts/load_olist.py
> ```

---

## Ejemplos de consultas

```
¿Cuántas órdenes hay por estado de entrega?
¿Cuál es el ticket promedio por estado de Brasil?
Top 10 categorías de productos más vendidas
¿Cómo evolucionaron las ventas mes a mes en 2018?
¿Cuál es el puntaje promedio de reseñas por categoría de producto?
¿Cuántos vendedores hay por estado?
¿Qué método de pago se usa más?
¿Cuál es el tiempo promedio de entrega en días?
```

---

## Arquitectura

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

El pipeline por request: pregunta → LLM → sanitizer → PostgreSQL → chart service → respuesta. Ninguna query que no sea `SELECT` llega a la base de datos. Si la ejecución falla, el backend hace un reintento automático pasando el error de PostgreSQL de vuelta al LLM para que corrija el SQL.

---

## Próximos pasos

- **Autenticación de usuarios** — sesiones persistentes con historial guardado
- **Multi-tenant** — cada usuario conecta y consulta su propia base de datos
- **Operaciones de escritura** — soporte controlado para INSERT y UPDATE con confirmación explícita
- **Fine-tuning del modelo** — ajuste con consultas validadas del dominio para mayor precisión
- **Deploy en la nube** — configuración lista para producción en GCP o AWS

---

Juan Rodriguez
