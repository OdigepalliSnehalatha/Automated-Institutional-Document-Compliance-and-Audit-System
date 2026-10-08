import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(
    "postgresql://postgres:sneha%40429reddy@localhost:5432/mydatabase",
    row_factory=dict_row
)
cur = conn.cursor()

# Check if CAI already exists
cur.execute("SELECT * FROM departments WHERE code = 'CAI' AND institution_id = 6;")
existing = cur.fetchone()

if not existing:
    cur.execute(
        """
        INSERT INTO departments (code, name, institution_id)
        VALUES ('CAI', 'Computer Artificial Intelligence', 6)
        RETURNING *;
        """
    )
    conn.commit()
    print("Added CAI branch:", cur.fetchone())
else:
    print("CAI branch already exists:", existing)

cur.execute("SELECT id, code, name FROM departments WHERE institution_id = 6 ORDER BY id;")
print("All departments:", cur.fetchall())
conn.close()
