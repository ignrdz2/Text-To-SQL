"""
sql_prompt.py
Templates del prompt para generación de SQL con Gemini.
Separado de la lógica del servicio para poder iterar el prompt de forma independiente.
"""

_SYSTEM_INSTRUCTIONS = """\
Eres un experto en SQL y en la base de datos Olist de e-commerce brasileno.
Tu unica tarea es generar consultas SQL validas para PostgreSQL.
Responde UNICAMENTE con la query SQL, sin explicaciones, sin bloques markdown, sin backticks.
NUNCA generes INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, EXEC
ni ninguna operacion que no sea SELECT.
Si la pregunta requiere modificar datos, responde exactamente: ERROR_UNSAFE_QUERY
Si la pregunta es ambigua o no podes generar SQL confiable, responde exactamente:
CLARIFICATION_NEEDED: <tu pregunta de clarificacion en el mismo idioma del usuario>\
"""

_FEW_SHOT_EXAMPLES = """\
Q: Cuantas ordenes hay por estado?
A: SELECT order_status, COUNT(*) as total FROM orders GROUP BY order_status ORDER BY total DESC

Q: Total facturado por mes en 2018
A: SELECT DATE_TRUNC('month', order_purchase_timestamp) as mes, SUM(payment_value) as total
   FROM orders o JOIN order_payments op ON o.order_id = op.order_id
   WHERE EXTRACT(YEAR FROM order_purchase_timestamp) = 2018
   GROUP BY mes ORDER BY mes

Q: Top 5 categorias con mejor puntaje promedio de resenas
A: SELECT pct.product_category_name_english, AVG(r.review_score) as avg_score
   FROM order_reviews r
   JOIN order_items oi ON r.order_id = oi.order_id
   JOIN products p ON oi.product_id = p.product_id
   JOIN product_category_name_translation pct ON p.product_category_name = pct.product_category_name
   GROUP BY pct.product_category_name_english
   ORDER BY avg_score DESC LIMIT 5\
"""


def build_prompt(question: str, schema_text: str) -> str:
    """
    Construye el prompt completo listo para enviar a Gemini.

    Args:
        question:    Pregunta del usuario en lenguaje natural.
        schema_text: Schema formateado como texto (generado por llm_service._format_schema).
    """
    return (
        f"[SYSTEM]\n{_SYSTEM_INSTRUCTIONS}\n\n"
        f"[SCHEMA]\n{schema_text}\n\n"
        f"[EXAMPLES]\n{_FEW_SHOT_EXAMPLES}\n\n"
        f"[QUESTION]\n{question}"
    )
