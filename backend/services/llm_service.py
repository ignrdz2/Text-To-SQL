"""
llm_service.py
Llama a Gemini 1.5 Flash y devuelve el SQL generado.
El template del prompt vive en prompts/sql_prompt.py.

Contratos de retorno de generate_sql():
  - SQL string limpio si la generación fue exitosa.
  - "ERROR_UNSAFE_QUERY"          si el LLM indica que la query es insegura.
  - "CLARIFICATION_NEEDED: ..."   si el LLM pide clarificación.
  Lanza LLMError para fallos de red / API.
"""

import os
import logging

import google.generativeai as genai
from dotenv import load_dotenv

from prompts.sql_prompt import build_prompt

load_dotenv()

logger = logging.getLogger(__name__)

RESPONSE_UNSAFE = "ERROR_UNSAFE_QUERY"
RESPONSE_CLARIFICATION_PREFIX = "CLARIFICATION_NEEDED:"


class LLMError(Exception):
    """Fallo al comunicarse con la API de Gemini."""


def _format_schema(schema: dict) -> str:
    """
    Convierte el dict del schema_loader en texto legible para el prompt.

    Formato:
      Table: orders
        - order_id (character varying) | examples: abc123, def456
    """
    lines: list[str] = []
    for table_name, table_info in schema.items():
        lines.append(f"Table: {table_name}")
        for col in table_info["columns"]:
            samples_str = (
                ", ".join(str(s) for s in col["samples"])
                if col["samples"]
                else "no samples"
            )
            lines.append(f"  - {col['name']} ({col['type']}) | examples: {samples_str}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _clean_response(text: str) -> str:
    """Elimina bloques markdown que el modelo agregue a pesar de las instrucciones."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def generate_sql(question: str, schema: dict) -> str:
    """
    Genera SQL a partir de una pregunta en lenguaje natural.

    Args:
        question: Pregunta del usuario en español o inglés.
        schema:   Dict retornado por schema_loader.get_schema().

    Returns:
        SQL string limpio, "ERROR_UNSAFE_QUERY", o "CLARIFICATION_NEEDED: ...".

    Raises:
        LLMError: Si la API de Gemini no responde o falla.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("GEMINI_API_KEY no está definida en las variables de entorno.")

    genai.configure(api_key=api_key)

    prompt = build_prompt(question, _format_schema(schema))
    logger.debug("Prompt enviado a Gemini (%d chars)", len(prompt))

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0,
                max_output_tokens=512,
            ),
        )
        raw = response.text
    except Exception as exc:
        logger.error("Error al llamar a Gemini: %s", exc)
        raise LLMError(f"Hubo un problema al procesar la pregunta: {exc}") from exc

    result = _clean_response(raw)
    logger.info("Respuesta Gemini: %r", result[:120])
    return result
