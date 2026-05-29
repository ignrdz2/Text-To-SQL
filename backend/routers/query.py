"""
query.py
Router FastAPI para POST /api/query y GET /api/health.

Pipeline completo por request:
  pregunta → LLM → sanitizer → DB → (retry si falla) → respuesta
"""

import logging
import os
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from schema.schema_loader import get_schema
from services.db_service import DBError, execute_query
from services.llm_service import (
    RESPONSE_CLARIFICATION_PREFIX,
    RESPONSE_UNSAFE,
    LLMError,
    generate_sql,
)
from services.chart_service import decide as chart_decide
from services.sanitizer import sanitize

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


# Modelos Pydantic
class QueryRequest(BaseModel):
    question: str


class ErrorDetail(BaseModel):
    type: str
    message: str


class QueryResponse(BaseModel):
    sql: str | None = None
    columns: list[str] = []
    data: list[dict[str, Any]] = []
    chart_type: str | None = None
    chart_config: dict | None = None
    error: ErrorDetail | None = None
    clarification_needed: bool = False
    clarification_question: str | None = None
    retry_attempted: bool = False


# Helpers de respuesta
def _error(error_type: str, message: str) -> QueryResponse:
    return QueryResponse(error=ErrorDetail(type=error_type, message=message))


def _is_special_response(sql: str) -> bool:
    return sql == RESPONSE_UNSAFE or sql.startswith(RESPONSE_CLARIFICATION_PREFIX)


def _handle_special(sql: str, fallback_error: str | None = None) -> QueryResponse | None:
    """
    Interpreta respuestas especiales del LLM.
    Devuelve QueryResponse si es especial, None si es SQL normal.
    """
    if sql == RESPONSE_UNSAFE:
        return _error("UNSAFE_QUERY", "Esta consulta no está permitida.")

    if sql.startswith(RESPONSE_CLARIFICATION_PREFIX):
        clarification = sql[len(RESPONSE_CLARIFICATION_PREFIX):].strip()
        return QueryResponse(clarification_needed=True, clarification_question=clarification)

    return None


# Endpoint principal
@router.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest) -> QueryResponse:
    question = request.question.strip()

    if not question:
        return _error("INVALID_REQUEST", "La pregunta no puede estar vacía.")

    schema = get_schema()

    # Paso 1: primera llamada al LLM
    try:
        sql = generate_sql(question, schema)
    except LLMError as exc:
        logger.error("LLM error (primer intento): %s", exc)
        return _error("LLM_ERROR", str(exc))

    # Paso 2: respuestas especiales del LLM
    special = _handle_special(sql)
    if special:
        return special

    # Paso 3: sanitizer
    san = sanitize(sql)
    if not san["valid"]:
        logger.warning("Sanitizer rechazó SQL: %s", san["reason"])
        return _error("UNSAFE_QUERY", san["reason"])

    # Paso 4: ejecución
    try:
        result = execute_query(sql)
        chart = chart_decide(result["columns"], result["data"])
        return QueryResponse(
            sql=sql,
            columns=result["columns"],
            data=result["data"],
            chart_type=chart["chart_type"],
            chart_config=chart["chart_config"],
        )

    except DBError as first_error:
        logger.warning("[RETRY] SQL original falló: %s", first_error)

        # Paso 5: reintento único (SPEC §8-A)
        # Se pasa el SQL fallido y el error exacto de PostgreSQL al LLM para que corrija.
        retry_question = (
            f"{question}\n\n"
            f"[SQL anterior]:\n{sql}\n\n"
            f"[Error de PostgreSQL]:\n{first_error}\n\n"
            f"El SQL anterior falló con este error. Generá una versión corregida."
        )

        logger.info("[RETRY] Intentando con SQL corregido...")

        try:
            sql2 = generate_sql(retry_question, schema)
        except LLMError as exc:
            logger.error("LLM error (reintento): %s", exc)
            return _error("LLM_ERROR", str(exc))

        # Si el LLM devuelve respuesta especial, reportamos el error original
        if _is_special_response(sql2):
            return _error("DB_ERROR", str(first_error))

        san2 = sanitize(sql2)
        if not san2["valid"]:
            return _error("UNSAFE_QUERY", san2["reason"])

        try:
            result2 = execute_query(sql2)
            logger.info("[RETRY] Segundo intento exitoso.")
            chart2 = chart_decide(result2["columns"], result2["data"])
            return QueryResponse(
                sql=sql2,
                columns=result2["columns"],
                data=result2["data"],
                chart_type=chart2["chart_type"],
                chart_config=chart2["chart_config"],
                retry_attempted=True,
            )

        except DBError as second_error:
            logger.error("[RETRY] Falló también: %s", second_error)
            return _error("DB_ERROR", str(second_error))


# Health check
@router.get("/health")
def health() -> dict:
    db_status = "connected"
    try:
        execute_query("SELECT 1 AS ok")
    except DBError:
        db_status = "error"

    llm_status = "available" if os.getenv("GEMINI_API_KEY") else "missing_key"

    return {"status": "ok", "db": db_status, "llm": llm_status}
