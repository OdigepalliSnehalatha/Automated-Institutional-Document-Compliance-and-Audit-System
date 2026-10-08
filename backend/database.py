import os
from contextlib import contextmanager

try:
    import psycopg
    from psycopg.rows import dict_row
    _USE_PSYCOPG3 = True
except Exception:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    _USE_PSYCOPG3 = False

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:sneha%40429reddy@localhost:5432/mydatabase"
)

def get_connection():
    """Returns a new database connection."""
    if _USE_PSYCOPG3:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    return psycopg2.connect(DATABASE_URL)

@contextmanager
def get_db_cursor(commit=False):
    """Context manager yielding a dictionary cursor with transaction control."""
    conn = get_connection()
    try:
        if _USE_PSYCOPG3:
            with conn.cursor() as cursor:
                yield cursor
            if commit:
                conn.commit()
        else:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
            if commit:
                conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()