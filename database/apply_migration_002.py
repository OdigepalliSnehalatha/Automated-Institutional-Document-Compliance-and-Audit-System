import psycopg
import bcrypt
from pathlib import Path

DB_URL = "postgresql://postgres:postgres@localhost:5432/mydatabase"

def run_migration():
    print("[*] Connecting to database...")
    conn = psycopg.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    migration_file = Path("database/migrations/002_professional_compliance_system.sql")
    sql = migration_file.read_text(encoding="utf-8")
    print("[*] Applying migration 002_professional_compliance_system.sql...")
    cur.execute(sql)
    print("[+] Migration 002 tables and columns created successfully.")

    inst_id = 6  # ALITS

    # 1. Seed Academic Years
    years = [
        ("2024-2025", False),
        ("2025-2026", True),
        ("2026-2027", False),
    ]
    for y_name, is_cur in years:
        cur.execute("""
            INSERT INTO academic_years (institution_id, year_name, is_current)
            VALUES (%s, %s, %s)
            ON CONFLICT (institution_id, year_name) 
            DO UPDATE SET is_current = EXCLUDED.is_current;
        """, (inst_id, y_name, is_cur))
    print("[+] Seeded academic years.")

    # 2. Seed Semesters (I to VIII)
    semesters = [
        ("Semester I", "SEM-1", 1),
        ("Semester II", "SEM-2", 2),
        ("Semester III", "SEM-3", 3),
        ("Semester IV", "SEM-4", 4),
        ("Semester V", "SEM-5", 5),
        ("Semester VI", "SEM-6", 6),
        ("Semester VII", "SEM-7", 7),
        ("Semester VIII", "SEM-8", 8),
    ]
    for name, code, num in semesters:
        cur.execute("""
            INSERT INTO semesters (institution_id, semester_name, semester_code, semester_number)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (institution_id, semester_code) DO NOTHING;
        """, (inst_id, name, code, num))
    print("[+] Seeded semesters.")

    # 3. Seed Exam Categories
    exam_cats = [
        ("Mid-1 Question Paper", "MID1", 30, True, 1),
        ("Mid-2 Question Paper", "MID2", 30, True, 2),
        ("Semester / End-Semester Question Paper", "SEM", 70, True, 3),
    ]
    for name, code, marks, mandatory, order in exam_cats:
        cur.execute("""
            INSERT INTO exam_categories (institution_id, name, code, max_marks, is_mandatory, display_order)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (institution_id, code) DO UPDATE SET max_marks = EXCLUDED.max_marks;
        """, (inst_id, name, code, marks, mandatory, order))
    print("[+] Seeded examination categories.")

    # 4. Fetch department and semester references
    cur.execute("SELECT id, code FROM departments WHERE institution_id = %s;", (inst_id,))
    dept_map = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute("SELECT id, semester_code FROM semesters WHERE institution_id = %s;", (inst_id,))
    sem_map = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute("SELECT id FROM academic_years WHERE institution_id = %s AND is_current = TRUE LIMIT 1;", (inst_id,))
    cur_year = cur.fetchone()[0]

    # 5. Seed Courses / Subjects
    courses = [
        ("CSE", "SEM-3", "CS301", "Computer Networks", 3),
        ("CSE", "SEM-3", "CS302", "Operating Systems", 3),
        ("CSE", "SEM-3", "CS303", "Database Management Systems", 4),
        ("CSE", "SEM-4", "CS401", "Software Engineering", 3),
        ("CSE", "SEM-4", "CS402", "Design & Analysis of Algorithms", 4),
        ("ECE", "SEM-3", "EC301", "Digital Electronics", 3),
        ("ECE", "SEM-3", "EC302", "Signals & Systems", 4),
        ("CAI", "SEM-3", "AI301", "Artificial Intelligence & Machine Learning", 4),
        ("CAI", "SEM-3", "AI302", "Natural Language Processing", 3),
        ("ME",  "SEM-3", "ME301", "Thermodynamics", 4),
        ("CE",  "SEM-3", "CE301", "Structural Analysis", 4),
    ]

    for dept_code, sem_code, c_code, c_name, creds in courses:
        dept_id = dept_map.get(dept_code)
        sem_id = sem_map.get(sem_code)
        if dept_id and sem_id:
            cur.execute("""
                INSERT INTO courses (institution_id, department_id, semester_id, academic_year_id, course_code, course_name, credits)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (institution_id, department_id, course_code) 
                DO UPDATE SET course_name = EXCLUDED.course_name, semester_id = EXCLUDED.semester_id;
            """, (inst_id, dept_id, sem_id, cur_year, c_code, c_name, creds))
    print("[+] Seeded courses across departments.")

    # 6. Ensure standard users exist with password hashes
    cur.execute("SELECT id FROM users WHERE email = 'faculty.cse@alitsprototype.test';")
    fac_user = cur.fetchone()
    if fac_user:
        fac_id = fac_user[0]
        # Assign courses to faculty
        cur.execute("SELECT id FROM courses WHERE course_code IN ('CS301', 'CS302');")
        for row in cur.fetchall():
            cur.execute("""
                INSERT INTO faculty_course_assignments (course_id, faculty_id, academic_year_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (course_id, faculty_id, academic_year_id) DO NOTHING;
            """, (row[0], fac_id, cur_year))
        print("[+] Assigned sample courses to Faculty (faculty.cse@alitsprototype.test).")

    # Update existing documents with defaults if null
    cur.execute("""
        UPDATE documents d
        SET academic_year_id = %s,
            semester_id = COALESCE(d.semester_id, %s),
            exam_category = COALESCE(d.exam_category, 'MID1'),
            validation_status = COALESCE(d.validation_status, d.analysis_status, 'PENDING'),
            approval_status = COALESCE(d.approval_status, 
                CASE 
                    WHEN d.analysis_status = 'ACCEPTED' THEN 'ACCEPTED' 
                    WHEN d.analysis_status = 'REJECTED' THEN 'REJECTED' 
                    ELSE 'PENDING' 
                END)
        WHERE d.academic_year_id IS NULL;
    """, (cur_year, sem_map.get("SEM-3")))

    conn.close()
    print("[OK] All migration and seeding tasks completed successfully!")

if __name__ == "__main__":
    run_migration()
