"""
sanitizer.py
Valida que un string SQL sea un SELECT seguro antes de ejecutarlo en la DB.

Devuelve: { "valid": bool, "reason": str }

Reglas:
  1. Debe comenzar con SELECT (ignorando whitespace y case).
  2. No debe contener múltiples statements (detectados por ';' fuera de literals/comentarios).
  3. No debe contener keywords peligrosas como *palabras completas*
     (evaluado sobre el SQL con string literals y comentarios removidos).
"""

import re
from typing import TypedDict


class SanitizeResult(TypedDict):
    valid: bool
    reason: str


# Keywords que como palabra completa invalidan la query
_DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "CREATE", "TRUNCATE", "EXEC", "EXECUTE",
]

_DANGEROUS_PATTERN = re.compile(
    r"\b(" + "|".join(_DANGEROUS_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def _strip_literals_and_comments(sql: str) -> str:
    """
    Elimina string literals y comentarios antes de buscar keywords peligrosas.
    Esto evita falsos positivos como SELECT 'DROP TABLE' FROM orders.
    """
    # String literals entre comillas simples → placeholder vacío
    result = re.sub(r"'[^']*'", "''", sql)
    # Comentarios inline  -- ...
    result = re.sub(r"--[^\n]*", " ", result)
    # Comentarios de bloque  /* ... */
    result = re.sub(r"/\*.*?\*/", " ", result, flags=re.DOTALL)
    return result


def sanitize(sql: str) -> SanitizeResult:
    """
    Valida que el SQL sea un SELECT seguro.
    Nunca permite que queries peligrosas lleguen a la DB.
    """
    if not sql or not sql.strip():
        return {"valid": False, "reason": "La consulta está vacía."}

    stripped = sql.strip()

    # Regla 1: debe empezar con SELECT (palabra completa, no SELECTALL etc.)
    if not re.match(r"^SELECT\b", stripped, re.IGNORECASE):
        return {
            "valid": False,
            "reason": (
                "La consulta debe comenzar con SELECT. "
                "No se permiten operaciones de escritura ni DDL."
            ),
        }

    # Normalizar para los chequeos 2 y 3
    normalized = _strip_literals_and_comments(stripped)

    # Regla 2: múltiples statements
    if ";" in normalized:
        return {
            "valid": False,
            "reason": "No se permiten múltiples statements separados por ';'.",
        }

    # Regla 3: keywords peligrosas como palabras completas
    match = _DANGEROUS_PATTERN.search(normalized)
    if match:
        keyword = match.group(0).upper()
        return {
            "valid": False,
            "reason": (
                f"Keyword peligrosa detectada: {keyword}. "
                "Solo se permiten consultas SELECT."
            ),
        }

    return {"valid": True, "reason": "OK"}


# Tests 
if __name__ == "__main__":
    TESTS = [
        # (descripción, sql, esperado valid)

        # Casos válidos
        ("SELECT básico en minúsculas",
         "select * from orders",
         True),

        ("SELECT con whitespace al inicio y al final",
         "  SELECT * FROM orders  ",
         True),

        ("SELECT con string literal que contiene keyword peligrosa",
         "SELECT 'DROP TABLE' FROM orders",
         True),

        ("SELECT con comentario inline al final",
         "SELECT * FROM orders -- esto es un comentario",
         True),

        ("SELECT con subconsulta legítima",
         "SELECT order_id FROM orders WHERE customer_id IN (SELECT customer_id FROM customers WHERE customer_state = 'SP')",
         True),

        # Casos peligrosos
        ("No empieza con SELECT — DROP directo",
         "drop table orders",
         False),

        ("UPDATE — operación de escritura",
         "UPDATE orders SET order_status = 'canceled'",
         False),

        ("Múltiples statements con DROP al final",
         "SELECT * FROM orders; DROP TABLE orders",
         False),

        ("DELETE disfrazado con SELECT al inicio",
         "SELECT * FROM orders; DELETE FROM orders WHERE 1=1",
         False),

        ("INSERT dentro de la query",
         "SELECT 1; INSERT INTO orders VALUES ('x')",
         False),

        # Edge cases
        ("Keyword en nombre de columna — no debe fallar (palabra completa)",
         "SELECT order_id, order_status FROM orders",
         True),

        ("Vacío",
         "",
         False),

        ("EXEC como palabra completa",
         "EXEC sp_helptext 'orders'",
         False),
    ]

    passed = 0
    failed = 0

    SEP = "-" * 60
    print(f"\n{SEP}")
    print(f"  Sanitizer tests ({len(TESTS)} casos)")
    print(SEP)

    for description, sql, expected_valid in TESTS:
        result = sanitize(sql)
        ok = result["valid"] == expected_valid
        status = "PASS" if ok else "FAIL"

        if ok:
            passed += 1
        else:
            failed += 1

        preview = sql[:55] + "..." if len(sql) > 55 else sql
        print(f"\n[{status}] {description}")
        print(f"       SQL     : {preview!r}")
        print(f"       Valido  : {result['valid']} (esperado: {expected_valid})")
        if not result["valid"]:
            print(f"       Razon   : {result['reason']}")

    print(f"\n{SEP}")
    print(f"  Resultado: {passed} passed, {failed} failed")
    print(f"{SEP}\n")

    if failed:
        raise SystemExit(1)
