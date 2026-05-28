"""
db_service.py
Ejecuta queries SELECT validadas contra PostgreSQL con timeout de 10 segundos.

Devuelve: { "columns": list[str], "data": list[dict] }
Lanza DBError para fallos de conexión o ejecución.
"""

import os
import logging
from decimal import Decimal
from datetime import datetime, date
from typing import Any, TypedDict

import psycopg2
import psycopg2.extras
import psycopg2.extensions
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Timeout en milisegundos (SPEC #15: máximo 10s por query)
_TIMEOUT_MS = 10_000


class QueryResult(TypedDict):
    columns: list[str]
    data: list[dict]


class DBError(Exception):
    """Error al ejecutar una query contra PostgreSQL."""


# Conexión
def _get_connection() -> psycopg2.extensions.connection:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise DBError("DATABASE_URL no está definida en las variables de entorno.")
    try:
        return psycopg2.connect(database_url)
    except psycopg2.OperationalError as exc:
        raise DBError(f"No se pudo conectar a la base de datos: {exc}") from exc


# Serialización de tipos no-JSON
def _serialize(value: Any) -> Any:
    """
    Convierte tipos de PostgreSQL que no son JSON-serializables por defecto.
    Decimal → float para que Recharts pueda graficarlos.
    datetime/date → ISO string.
    """
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


# Función principal
def execute_query(sql: str) -> QueryResult:
    """
    Ejecuta un SQL ya validado por el sanitizer.

    Args:
        sql: Query SELECT validada.

    Returns:
        { "columns": [...], "data": [...] }
        Si no hay filas, data es [] — no es un error (SPEC §8-D).

    Raises:
        DBError: Timeout superado, SQL inválido u otro fallo de DB.
    """
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Timeout a nivel de sesión: si la query tarda más de 10s,
            # PostgreSQL la cancela y lanza QueryCanceledError
            cursor.execute(f"SET statement_timeout = {_TIMEOUT_MS};")

            cursor.execute(sql)
            rows = cursor.fetchall()

            # cursor.description existe incluso cuando rows está vacío
            columns = (
                [desc[0] for desc in cursor.description]
                if cursor.description
                else []
            )

            if not rows:
                logger.info("Query ejecutada sin resultados.")
                return {"columns": columns, "data": []}

            data = [
                {k: _serialize(v) for k, v in dict(row).items()}
                for row in rows
            ]

            logger.info("Query ejecutada: %d filas, %d columnas.", len(data), len(columns))
            return {"columns": columns, "data": data}

    except psycopg2.extensions.QueryCanceledError as exc:
        raise DBError(
            "La consulta superó el tiempo máximo permitido (10 segundos)."
        ) from exc
    except psycopg2.ProgrammingError as exc:
        raise DBError(f"Error de SQL: {exc.pgerror or str(exc)}") from exc
    except psycopg2.Error as exc:
        raise DBError(f"Error de base de datos: {exc.pgerror or str(exc)}") from exc
    finally:
        conn.close()
