import psycopg2
from flask import current_app
import os

def get_db_connection():
    """Return a new psycopg2 connection using app config or environment variables."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", current_app.config.get("DB_HOST", "localhost")),
        port=os.getenv("DB_PORT", current_app.config.get("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", current_app.config.get("DB_NAME", "myappdb")),
        user=os.getenv("DB_USER", current_app.config.get("DB_USER", "myuser")),
        password=os.getenv("DB_PASSWORD", current_app.config.get("DB_PASSWORD", "secret")),
    )
    return conn
