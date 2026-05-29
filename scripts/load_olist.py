"""
load_olist.py
Script de ejecución única: crea las tablas en PostgreSQL y carga los CSVs del dataset Olist.
Ejecutar desde fuera del contenedor; conecta a localhost:5432.

Uso:
    python scripts/load_olist.py

Dependencias (instalar si no están):
    pip install psycopg2-binary python-dotenv
"""

import logging
import os
import sys
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# CSVs en scripts/data/, .env en la raíz del proyecto
DATA_DIR = Path(__file__).parent / "data"
ENV_PATH = Path(__file__).parent.parent / ".env"

# Tablas en orden de carga respetando dependencias de FK
TABLAS = [
    (
        "customers",
        """
        CREATE TABLE customers (
            customer_id                TEXT,
            customer_unique_id         TEXT,
            customer_zip_code_prefix   TEXT,
            customer_city              TEXT,
            customer_state             TEXT
        )
        """,
        "olist_customers_dataset.csv",
    ),
    (
        "sellers",
        """
        CREATE TABLE sellers (
            seller_id                TEXT,
            seller_zip_code_prefix   TEXT,
            seller_city              TEXT,
            seller_state             TEXT
        )
        """,
        "olist_sellers_dataset.csv",
    ),
    (
        "products",
        """
        CREATE TABLE products (
            product_id                   TEXT,
            product_category_name        TEXT,
            product_name_lenght          NUMERIC,
            product_description_lenght   NUMERIC,
            product_photos_qty           NUMERIC,
            product_weight_g             NUMERIC,
            product_length_cm            NUMERIC,
            product_height_cm            NUMERIC,
            product_width_cm             NUMERIC
        )
        """,
        "olist_products_dataset.csv",
    ),
    (
        "product_category_name_translation",
        """
        CREATE TABLE product_category_name_translation (
            product_category_name          TEXT,
            product_category_name_english  TEXT
        )
        """,
        "product_category_name_translation.csv",
    ),
    (
        # orders tiene 8 columnas en el CSV real vs 6 en el SPEC
        # order_approved_at y order_delivered_carrier_date son las dos adicionales
        "orders",
        """
        CREATE TABLE orders (
            order_id                        TEXT,
            customer_id                     TEXT,
            order_status                    TEXT,
            order_purchase_timestamp        TEXT,
            order_approved_at               TEXT,
            order_delivered_carrier_date    TEXT,
            order_delivered_customer_date   TEXT,
            order_estimated_delivery_date   TEXT
        )
        """,
        "olist_orders_dataset.csv",
    ),
    (
        "order_items",
        """
        CREATE TABLE order_items (
            order_id             TEXT,
            order_item_id        NUMERIC,
            product_id           TEXT,
            seller_id            TEXT,
            shipping_limit_date  TEXT,
            price                NUMERIC,
            freight_value        NUMERIC
        )
        """,
        "olist_order_items_dataset.csv",
    ),
    (
        "order_payments",
        """
        CREATE TABLE order_payments (
            order_id              TEXT,
            payment_sequential    NUMERIC,
            payment_type          TEXT,
            payment_installments  NUMERIC,
            payment_value         NUMERIC
        )
        """,
        "olist_order_payments_dataset.csv",
    ),
    (
        "order_reviews",
        """
        CREATE TABLE order_reviews (
            review_id                TEXT,
            order_id                 TEXT,
            review_score             NUMERIC,
            review_comment_title     TEXT,
            review_comment_message   TEXT,
            review_creation_date     TEXT,
            review_answer_timestamp  TEXT
        )
        """,
        "olist_order_reviews_dataset.csv",
    ),
    (
        "geolocation",
        """
        CREATE TABLE geolocation (
            geolocation_zip_code_prefix  TEXT,
            geolocation_lat              NUMERIC,
            geolocation_lng              NUMERIC,
            geolocation_city             TEXT,
            geolocation_state            TEXT
        )
        """,
        "olist_geolocation_dataset.csv",
    ),
]


def conectar() -> psycopg2.extensions.connection:
    """Abre la conexión usando el .env del proyecto, forzando host=localhost."""
    load_dotenv(ENV_PATH)
    return psycopg2.connect(
        host="localhost",
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "olist"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def cargar_tabla(conn: psycopg2.extensions.connection, nombre: str, ddl: str, csv_nombre: str) -> int:
    """
    Elimina, recrea y carga una tabla desde su CSV.
    Devuelve el número de filas cargadas, o -1 si hubo error.
    Hace rollback por tabla en caso de falla, sin detener las demás.
    """
    csv_path = DATA_DIR / csv_nombre

    if not csv_path.exists():
        logger.error("Archivo no encontrado: %s", csv_path)
        return -1

    try:
        with conn.cursor() as cur:
            logger.info("Creando tabla %s...", nombre)
            cur.execute(f"DROP TABLE IF EXISTS {nombre} CASCADE")
            cur.execute(ddl)

            with open(csv_path, encoding="utf-8") as f:
                cur.copy_expert(
                    f"COPY {nombre} FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')",
                    f,
                )

            # rowcount capturado antes del commit
            filas = cur.rowcount

        conn.commit()
        logger.info("Cargando %d filas en tabla %s...", filas, nombre)
        return filas

    except Exception as exc:
        conn.rollback()
        logger.error("Error al cargar %s: %s", nombre, exc)
        return -1


def mostrar_resumen(conn: psycopg2.extensions.connection) -> None:
    """Muestra COUNT(*) de cada tabla como verificación final."""
    print("\n--- Resumen de carga ---")
    with conn.cursor() as cur:
        for nombre, _, _ in TABLAS:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {nombre}")  # noqa: S608
                count = cur.fetchone()[0]
                print(f"  {nombre:<42} {count:>8} filas")
            except Exception as exc:
                print(f"  {nombre:<42} ERROR: {exc}")


def main() -> None:
    inicio = time.time()

    try:
        conn = conectar()
        logger.info("Conexión establecida con PostgreSQL")
    except Exception as exc:
        logger.error("No se pudo conectar a la base de datos: %s", exc)
        sys.exit(1)

    errores = 0
    for nombre, ddl, csv_nombre in TABLAS:
        if cargar_tabla(conn, nombre, ddl, csv_nombre) == -1:
            errores += 1

    logger.info("Carga completa en %.1f segundos", time.time() - inicio)
    mostrar_resumen(conn)
    conn.close()

    if errores:
        logger.warning("%d tabla(s) tuvieron errores durante la carga", errores)
        sys.exit(1)


if __name__ == "__main__":
    main()
