"""
chart_service.py
Decide el tipo de gráfico y su config a partir de las columnas y datos del resultado.
El orden de decisión sigue exactamente el SPEC §11.
"""

from typing import Any

_DATE_KEYWORDS = ("date", "time", "month", "year", "mes")


def _classify_columns(
    columns: list[str], data: list[dict[str, Any]]
) -> tuple[list[str], list[str], list[str]]:
    """Devuelve (cols_numericas, cols_texto, cols_fecha)."""
    numeric, text, date = [], [], []

    for col in columns:
        first_val = next(
            (row[col] for row in data if col in row and row[col] is not None), None
        )
        col_lower = col.lower()
        is_date_name = any(kw in col_lower for kw in _DATE_KEYWORDS)

        if isinstance(first_val, bool):
            # bool hereda de int — se trata como texto para evitar falsos positivos
            text.append(col)
        elif isinstance(first_val, (int, float)):
            numeric.append(col)
        elif isinstance(first_val, str):
            if is_date_name:
                date.append(col)
            else:
                text.append(col)
        else:
            # None u objetos datetime — el nombre de la columna decide
            if is_date_name:
                date.append(col)
            else:
                text.append(col)

    return numeric, text, date


def decide(columns: list[str], data: list[dict[str, Any]]) -> dict:
    """
    Devuelve { "chart_type": str, "chart_config": dict | None }.
    El caller esparce el resultado en los campos de QueryResponse.
    """
    if not columns or not data:
        return {"chart_type": "table", "chart_config": None}

    numeric, text, date = _classify_columns(columns, data)

    num_n = len(numeric)
    txt_n = len(text)
    date_n = len(date)
    rows = len(data)

    # Regla 1 - KPI: exactamente 1 col numerica, 1 fila, nada más
    if rows == 1 and num_n == 1 and txt_n == 0 and date_n == 0:
        col = numeric[0]
        return {"chart_type": "kpi", "chart_config": {"value_key": col, "label": col}}

    # Regla 2 - Line: exactamente 1 numerica + 1 fecha (sin texto)
    if num_n == 1 and date_n == 1 and txt_n == 0:
        return {
            "chart_type": "line",
            "chart_config": {"x_key": date[0], "y_key": numeric[0]},
        }

    # Reglas 3 y 4 - Pie / Bar: exactamente 1 texto + 1 numerica (sin fecha)
    if txt_n == 1 and num_n == 1 and date_n == 0:
        if rows <= 6:
            return {
                "chart_type": "pie",
                "chart_config": {"name_key": text[0], "value_key": numeric[0]},
            }
        return {
            "chart_type": "bar",
            "chart_config": {"x_key": text[0], "y_key": numeric[0]},
        }

    # Regla 5 - Multibar: 1 texto + 2 o más numericas (sin fecha)
    if txt_n == 1 and num_n >= 2 and date_n == 0:
        return {
            "chart_type": "multibar",
            "chart_config": {"x_key": text[0], "y_keys": numeric},
        }

    # Regla 6 - Fallback
    return {"chart_type": "table", "chart_config": None}


# tests
if __name__ == "__main__":
    PASS = "\033[92mPASS\033[0m"
    FAIL = "\033[91mFAIL\033[0m"
    errors = 0

    def check(label, got, expected):
        global errors
        if got == expected:
            print(f"{PASS} {label}")
        else:
            print(f"{FAIL} {label}")
            print(f"     obtenido: {got}")
            print(f"     esperado: {expected}")
            errors += 1

    # 1 - KPI: 1 fila, 1 col numerica, nada mas
    check(
        "KPI - 1 fila, 1 col numerica",
        decide(["total_orders"], [{"total_orders": 99471}]),
        {"chart_type": "kpi", "chart_config": {"value_key": "total_orders", "label": "total_orders"}},
    )

    # 2 - KPI descartado: 1 fila pero hay col de texto tambien -> pie
    check(
        "No KPI - 1 fila con col de texto -> pie",
        decide(["status", "total"], [{"status": "delivered", "total": 5}]),
        {"chart_type": "pie", "chart_config": {"name_key": "status", "value_key": "total"}},
    )

    # 3 - Line: col con keyword de fecha + col numerica
    check(
        "Line - col 'month' + col numerica",
        decide(
            ["month", "revenue"],
            [
                {"month": "2018-01", "revenue": 120000},
                {"month": "2018-02", "revenue": 135000},
            ],
        ),
        {"chart_type": "line", "chart_config": {"x_key": "month", "y_key": "revenue"}},
    )

    # 4 - Pie: 1 texto + 1 numerica, 4 filas (<= 6)
    check(
        "Pie - 1 texto + 1 numerica, 4 filas",
        decide(
            ["payment_type", "total"],
            [
                {"payment_type": "credit_card", "total": 76795},
                {"payment_type": "boleto", "total": 19784},
                {"payment_type": "voucher", "total": 5775},
                {"payment_type": "debit_card", "total": 1529},
            ],
        ),
        {"chart_type": "pie", "chart_config": {"name_key": "payment_type", "value_key": "total"}},
    )

    # 5 - Bar: 1 texto + 1 numerica, mas de 6 filas
    check(
        "Bar - 1 texto + 1 numerica, 8 filas",
        decide(
            ["category", "sales"],
            [{"category": f"cat_{i}", "sales": i * 100} for i in range(8)],
        ),
        {"chart_type": "bar", "chart_config": {"x_key": "category", "y_key": "sales"}},
    )

    # 6 - Multibar: 1 texto + 2 cols numericas
    check(
        "Multibar - 1 texto + 2 cols numericas",
        decide(
            ["state", "avg_price", "avg_freight"],
            [
                {"state": "SP", "avg_price": 120.5, "avg_freight": 15.3},
                {"state": "RJ", "avg_price": 130.0, "avg_freight": 18.1},
            ],
        ),
        {
            "chart_type": "multibar",
            "chart_config": {"x_key": "state", "y_keys": ["avg_price", "avg_freight"]},
        },
    )

    # 7 - Table fallback: 2 columnas de texto
    check(
        "Table - 2 columnas de texto (fallback)",
        decide(
            ["order_id", "customer_id"],
            [{"order_id": "abc", "customer_id": "xyz"}],
        ),
        {"chart_type": "table", "chart_config": None},
    )

    # 8 - Table fallback: data vacia
    check(
        "Table - data vacia",
        decide(["col_a", "col_b"], []),
        {"chart_type": "table", "chart_config": None},
    )

    # 9 - Line con nombre de columna que contiene 'date'
    check(
        "Line - columna 'order_purchase_date' + numerica",
        decide(
            ["order_purchase_date", "total"],
            [{"order_purchase_date": "2018-01-01", "total": 500}],
        ),
        {"chart_type": "line", "chart_config": {"x_key": "order_purchase_date", "y_key": "total"}},
    )

    print()
    if errors == 0:
        print("Todos los tests pasaron.")
    else:
        print(f"{errors} test(s) fallaron.")
        raise SystemExit(1)
