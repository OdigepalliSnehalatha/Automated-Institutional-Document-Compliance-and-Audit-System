import psycopg2
from pathlib import Path

migration_path = Path("database/migrations/001_structural_system.sql")
sql = migration_path.read_text(encoding="utf-8")

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="mydatabase",
    user="postgres",
    password="sneha@429reddy"
)
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute(sql)
    print("Migration 001_structural_system.sql applied successfully!")
except Exception as e:
    print("Migration failed:", e)
finally:
    cur.close()
    conn.close()
