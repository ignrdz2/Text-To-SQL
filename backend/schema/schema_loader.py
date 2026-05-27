"""
schema_loader.py
Extrae el schema de la DB (tablas, columnas, tipos, ejemplos de valores)
y lo devuelve cacheado en memoria.

Estructura del cache:
{
  "table_name": {
    "columns": [
      {
        "name": "column_name",
        "type": "varchar",
        "samples": ["val1", "val2", ...]   # hasta 5 valores distintos, no nulos
      },
      ...
    ]
  },
  ...
}
"""

import os
import logging
from typing import Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Cache en memoria ──────────────────────────────────────────────────────────
_schema_cache: dict[str, Any] | None = None


# ── Conexión ──────────────────────────────────────────────────────────────────
def _get_connection() -> psycopg2.extensions.connection:
    """Abre una conexión usando DATABASE_URL del entorno."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL no está definida en las variables de entorno.")
    return psycopg2.connect(database_url)


# ── Extracción del schema ─────────────────────────────────────────────────────
def _fetch_tables(cursor: psycopg2.extensions.cursor) -> list[str]:
    """Devuelve todas las tablas del schema public, ordenadas."""
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
    )
    return [row["table_name"] for row in cursor.fetchall()]


def _fetch_columns(
    cursor: psycopg2.extensions.cursor, table: str
) -> list[dict[str, str]]:
    """Devuelve nombre y tipo de cada columna de una tabla, en orden."""
    cursor.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
        ORDER BY ordinal_position;
        """,
        (table,),
    )
    return [{"name": row["column_name"], "type": row["data_type"]} for row in cursor.fetchall()]


def _fetch_samples(
    cursor: psycopg2.extensions.cursor, table: str, column: str
) -> list[str]:
    """
    Devuelve hasta 5 valores distintos y no nulos de una columna.
    Usa comillas dobles para nombres de tabla/columna (evita conflictos
    con palabras reservadas). Solo genera SELECT → cumple la regla de seguridad.
    """
    try:
        cursor.execute(
            f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL LIMIT 5;'
        )
        return [str(row[column]) for row in cursor.fetchall()]
    except Exception as exc:  # columna con tipo no soportado por DISTINCT, etc.
        logger.warning("No se pudieron obtener ejemplos para %s.%s: %s", table, column, exc)
        return []


# ── Función principal ─────────────────────────────────────────────────────────
def _build_schema() -> dict[str, Any]:
    """Conecta a la DB y construye el dict completo del schema."""
    schema: dict[str, Any] = {}

    conn = _get_connection()
    try:
        # RealDictCursor devuelve filas como dicts → acceso por nombre de columna
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            tables = _fetch_tables(cursor)
            logger.info("Tablas encontradas: %s", tables)

            for table in tables:
                columns_meta = _fetch_columns(cursor, table)
                columns: list[dict[str, Any]] = []

                for col in columns_meta:
                    samples = _fetch_samples(cursor, table, col["name"])
                    columns.append(
                        {
                            "name": col["name"],
                            "type": col["type"],
                            "samples": samples,
                        }
                    )

                schema[table] = {"columns": columns}
                logger.info("  ✓ %s (%d columnas)", table, len(columns))
    finally:
        conn.close()

    return schema


def get_schema() -> dict[str, Any]:
    """
    Devuelve el schema cacheado en memoria.
    La primera llamada conecta a la DB y construye el cache;
    las siguientes retornan el dict ya construido sin tocar la DB.
    """
    global _schema_cache

    if _schema_cache is None:
        logger.info("Schema cache vacío — extrayendo de la DB...")
        _schema_cache = _build_schema()
        logger.info("Schema cacheado: %d tablas.", len(_schema_cache))

    return _schema_cache


def invalidate_cache() -> None:
    """Limpia el cache para forzar una re-extracción en la próxima llamada."""
    global _schema_cache
    _schema_cache = None
    logger.info("Schema cache invalidado.")
