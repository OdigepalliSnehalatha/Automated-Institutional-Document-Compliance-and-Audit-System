import psycopg
import bcrypt
from pathlib import Path

DB_URL = "postgresql://postgres:postgres@localhost:5432/mydatabase"

def setup():
    conn = psycopg.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    print("[*] Setting up core schema...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS institution (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        email VARCHAR(255),
        logo_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS departments (
        id SERIAL PRIMARY KEY,
        institution_id INTEGER REFERENCES institution(id) ON DELETE CASCADE,
        code VARCHAR(50) NOT NULL,
        name VARCHAR(255) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        institution_id INTEGER REFERENCES institution(id) ON DELETE CASCADE,
        department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        password_hash VARCHAR(255),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS document_types (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE
    );

    CREATE TABLE IF NOT EXISTS document_formats (
        id SERIAL PRIMARY KEY,
        institution_id INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
        department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
        document_type_id INTEGER NOT NULL REFERENCES document_types(id) ON DELETE CASCADE,
        format_name VARCHAR(255) NOT NULL,
        instructions TEXT,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS format_requirements (
        id SERIAL PRIMARY KEY,
        format_id INTEGER NOT NULL REFERENCES document_formats(id) ON DELETE CASCADE,
        requirement_name VARCHAR(255) NOT NULL,
        requirement_type VARCHAR(100) NOT NULL,
        requirement_value TEXT,
        is_required BOOLEAN DEFAULT TRUE,
        display_order INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        institution_id INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
        department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
        document_type_id INTEGER REFERENCES document_types(id) ON DELETE SET NULL,
        uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        file_name VARCHAR(255) NOT NULL,
        file_path TEXT NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        analysis_status VARCHAR(50) DEFAULT 'PENDING',
        analysis_result JSONB,
        analyzed_at TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS login_otps (
        id SERIAL PRIMARY KEY,
        institution_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        otp_hash TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        attempts INTEGER DEFAULT 0,
        is_used BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS pending_registrations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        institution_id INTEGER REFERENCES institution(id) ON DELETE CASCADE,
        department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
        otp_hash TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        attempts INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_pending_reg_email ON pending_registrations(email);

    CREATE INDEX IF NOT EXISTS idx_documents_dept ON documents(department_id);
    CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(uploaded_by);
    CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(analysis_status);
    CREATE INDEX IF NOT EXISTS idx_formats_dept ON document_formats(department_id);
    CREATE INDEX IF NOT EXISTS idx_formats_type ON document_formats(document_type_id);
    CREATE INDEX IF NOT EXISTS idx_login_otps_lookup ON login_otps(email, role, is_used);
    """)
    print("[+] Core schema created.")

    # Seed Institution
    cur.execute("SELECT id FROM institution WHERE name = 'Anantha Lakshmi Institute of Technology and Sciences';")
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO institution (id, name, email) 
            VALUES (6, 'Anantha Lakshmi Institute of Technology and Sciences', 'principal@alits.ac.in')
            ON CONFLICT (id) DO NOTHING
            RETURNING id;
        """)
        print("[+] Seeded institution ALITS (ID 6).")
    inst_id = 6

    # Seed Document Types
    cur.execute("""
    INSERT INTO document_types (id, name, description, is_active)
    VALUES 
        (1, 'Course Structure', 'Institution-defined structural format for course syllabi and units', TRUE),
        (2, 'Question Bank', 'Structural format for question banks (Units 1-5, Part A and Part B distribution)', TRUE),
        (3, 'Question Paper', 'Structural format for Mid and Semester Examination Question Papers', TRUE)
    ON CONFLICT (name) DO UPDATE SET is_active = TRUE;
    """)
    print("[+] Seeded document types.")

    # Seed Departments
    depts = [
        (1, 'CSE', 'Computer Science and Engineering'),
        (2, 'CSD', 'Computer Science and Design'),
        (3, 'CSM', 'Computer Science and Machine Learning'),
        (4, 'ECE', 'Electronics and Communication Engineering'),
        (5, 'ME', 'Mechanical Engineering'),
        (6, 'CE', 'Civil Engineering'),
        (7, 'CAI', 'Computer Artificial Intelligence'),
    ]
    for dept_id, code, name in depts:
        cur.execute("""
            INSERT INTO departments (id, institution_id, code, name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET code = EXCLUDED.code, name = EXCLUDED.name;
        """, (dept_id, inst_id, code, name))
    print("[+] Seeded standard engineering departments.")

    # Seed Demo Users
    users = [
        ("Prototype Auditor", "auditor@alitsprototype.test", "Auditor@123", "Auditor", None),
        ("Prototype HOD", "hod.cse@alitsprototype.test", "Hod@123", "HOD", 1),
        ("Prototype Faculty", "faculty.cse@alitsprototype.test", "Faculty@123", "Faculty", 1),
        ("Prototype Admin", "admin@alitsprototype.test", "Admin@123", "Admin", None),
    ]

    for name, email, password, role, dept_id in users:
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s);", (email,))
        existing = cur.fetchone()
        if existing:
            cur.execute("""
                UPDATE users SET password_hash = %s, role = %s, department_id = %s, is_active = TRUE
                WHERE id = %s;
            """, (pw_hash, role, dept_id, existing[0]))
        else:
            cur.execute("""
                INSERT INTO users (institution_id, department_id, name, email, role, password_hash, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE);
            """, (inst_id, dept_id, name, email, role, pw_hash))
        print(f"[+] Seeded user: {role} ({email})")

    # Reset sequences
    cur.execute("SELECT setval(pg_get_serial_sequence('institution', 'id'), coalesce(max(id), 1)) FROM institution;")
    cur.execute("SELECT setval(pg_get_serial_sequence('departments', 'id'), coalesce(max(id), 1)) FROM departments;")
    cur.execute("SELECT setval(pg_get_serial_sequence('document_types', 'id'), coalesce(max(id), 1)) FROM document_types;")
    cur.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id), 1)) FROM users;")

    conn.close()
    print("[OK] Database initialization and seeding completed successfully!")

if __name__ == "__main__":
    setup()
