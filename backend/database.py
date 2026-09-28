import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:sneha%40429reddy@localhost:5432/mydatabase"
)

def get_connection():
    """Returns a new psycopg2 connection."""
    return psycopg2.connect(DATABASE_URL)

@contextmanager
def get_db_cursor(commit=False):
    """Context manager yielding a RealDictCursor with auto-commit or rollback."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()