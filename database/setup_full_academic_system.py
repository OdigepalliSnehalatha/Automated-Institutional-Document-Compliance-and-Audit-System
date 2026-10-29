import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_cursor, get_connection
from backend.services.auth_service import hash_password

def setup_full_academic_system():
    print("[*] Connecting to database...")
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    # 1. Apply Migration 002 SQL
    migration_file = Path("database/migrations/002_professional_compliance_system.sql")
    if migration_file.exists():
        print("[*] Executing migration 002...")
        sql = migration_file.read_text(encoding="utf-8")
        cur.execute(sql)
        print("[+] Migration 002 executed successfully.")

    # 2. Get ALITS Institution ID
    cur.execute("SELECT id FROM institution WHERE name ILIKE '%Anantha Lakshmi%' LIMIT 1")
    inst_row = cur.fetchone()
    if not inst_row:
        cur.execute("SELECT id FROM institution LIMIT 1")
        inst_row = cur.fetchone()
    inst_id = inst_row["id"] if inst_row else 6
    print(f"[+] Using Institution ID: {inst_id}")

    # 3. Seed / Ensure All Requested Departments with full names
    # CSE, CSD, CSM, CSE-AIML, ECE, EEE, ME (Mechanical), CE (Civil), CAI
    departments_data = [
        ("CSE", "Computer Science & Engineering"),
        ("CSD", "Computer Science & Design"),
        ("CSM", "Computer Science & Machine Learning"),
        ("CSE-AIML", "Computer Science & Engineering (Artificial Intelligence & Machine Learning)"),
        ("CAI", "Computer Artificial Intelligence"),
        ("ECE", "Electronics & Communication Engineering"),
        ("EEE", "Electrical & Electronics Engineering"),
        ("ME", "Mechanical Engineering"),
        ("CE", "Civil Engineering"),
    ]

    dept_id_map = {}
    for code, full_name in departments_data:
        cur.execute(
            """
            SELECT id FROM departments 
            WHERE institution_id = %s AND (UPPER(code) = UPPER(%s) OR UPPER(name) = UPPER(%s))
            """,
            (inst_id, code, full_name)
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                "UPDATE departments SET code = %s, name = %s WHERE id = %s",
                (code, full_name, existing["id"])
            )
            dept_id_map[code] = existing["id"]
        else:
            cur.execute(
                """
                INSERT INTO departments (institution_id, code, name)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (inst_id, code, full_name)
            )
            dept_id_map[code] = cur.fetchone()["id"]
    print(f"[+] Ensured all {len(departments_data)} departments with full names.")

    # 4. Seed / Ensure Academic Years
    academic_years_data = [
        ("2023-2024", False),
        ("2024-2025", False),
        ("2025-2026", True),
        ("2026-2027", False),
    ]
    year_id_map = {}
    for y_name, is_cur in academic_years_data:
        cur.execute(
            """
            INSERT INTO academic_years (institution_id, year_name, is_current)
            VALUES (%s, %s, %s)
            ON CONFLICT (institution_id, year_name)
            DO UPDATE SET is_current = EXCLUDED.is_current
            RETURNING id
            """,
            (inst_id, y_name, is_cur)
        )
        row = cur.fetchone()
        year_id_map[y_name] = row["id"]
    current_year_id = year_id_map["2025-2026"]
    print(f"[+] Ensured {len(academic_years_data)} Academic Years (Current: 2025-2026).")

    # 5. Seed / Ensure All 8 Semesters (1st year 1st sem to 4th year 8th sem)
    semesters_data = [
        ("I Year - I Semester", "SEM 1-1", 1),
        ("I Year - II Semester", "SEM 1-2", 2),
        ("II Year - I Semester", "SEM 2-1", 3),
        ("II Year - II Semester", "SEM 2-2", 4),
        ("III Year - I Semester", "SEM 3-1", 5),
        ("III Year - II Semester", "SEM 3-2", 6),
        ("IV Year - I Semester", "SEM 4-1", 7),
        ("IV Year - II Semester", "SEM 4-2", 8),
    ]
    sem_id_map = {}
    for s_name, s_code, s_num in semesters_data:
        cur.execute(
            """
            INSERT INTO semesters (institution_id, semester_name, semester_code, semester_number)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (institution_id, semester_code)
            DO UPDATE SET semester_name = EXCLUDED.semester_name, semester_number = EXCLUDED.semester_number
            RETURNING id
            """,
            (inst_id, s_name, s_code, s_num)
        )
        row = cur.fetchone()
        sem_id_map[s_code] = row["id"]
    print(f"[+] Ensured all 8 Semesters from 1st Year 1st Sem to 4th Year 8th Sem.")

    # 6. Seed / Ensure Exam Categories
    exam_categories_data = [
        ("Mid-1 Question Paper", "MID1", 30, True, 1),
        ("Mid-2 Question Paper", "MID2", 30, True, 2),
        ("Semester / End-Semester Question Paper", "SEM", 70, True, 3),
    ]
    for e_name, e_code, marks, is_mand, order in exam_categories_data:
        cur.execute(
            """
            INSERT INTO exam_categories (institution_id, name, code, max_marks, is_mandatory, display_order)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (institution_id, code)
            DO UPDATE SET name = EXCLUDED.name, max_marks = EXCLUDED.max_marks, display_order = EXCLUDED.display_order
            """,
            (inst_id, e_name, e_code, marks, is_mand, order)
        )
    print(f"[+] Ensured Exam Categories (MID1, MID2, SEM).")

    # 7. Seed Standard Courses across departments and semesters
    courses_data = [
        # CSE
        ("CSE", "SEM 1-1", "CS101", "Problem Solving and Programming with Python", 3),
        ("CSE", "SEM 1-2", "CS102", "Data Structures using C", 4),
        ("CSE", "SEM 2-1", "CS201", "Computer Organization & Architecture", 3),
        ("CSE", "SEM 2-1", "CS202", "Database Management Systems", 4),
        ("CSE", "SEM 2-2", "CS203", "Operating Systems", 3),
        ("CSE", "SEM 2-2", "CS204", "Design and Analysis of Algorithms", 4),
        ("CSE", "SEM 3-1", "CS301", "Computer Networks", 3),
        ("CSE", "SEM 3-1", "CS302", "Software Engineering", 3),
        ("CSE", "SEM 3-2", "CS303", "Compiler Design", 3),
        ("CSE", "SEM 4-1", "CS401", "Cloud Computing & DevOps", 3),
        ("CSE", "SEM 4-2", "CS402", "Comprehensive Viva & Capstone Project", 8),

        # CSD
        ("CSD", "SEM 2-1", "DS201", "Data Engineering & Statistics", 3),
        ("CSD", "SEM 2-2", "DS202", "Data Wrangling and Visualization", 3),
        ("CSD", "SEM 3-1", "DS301", "Big Data Analytics", 4),

        # CSM
        ("CSM", "SEM 2-1", "ML201", "Applied Probability & Linear Algebra", 3),
        ("CSM", "SEM 2-2", "ML202", "Foundations of Machine Learning", 4),
        ("CSM", "SEM 3-1", "ML301", "Deep Neural Networks", 4),

        # CSE-AIML
        ("CSE-AIML", "SEM 2-1", "AIML201", "Artificial Intelligence Principles", 3),
        ("CSE-AIML", "SEM 2-2", "AIML202", "Machine Learning Techniques", 4),
        ("CSE-AIML", "SEM 3-1", "AIML301", "Natural Language Processing", 3),

        # ECE
        ("ECE", "SEM 2-1", "EC201", "Electronic Devices and Circuits", 3),
        ("ECE", "SEM 2-2", "EC202", "Signals and Systems", 4),
        ("ECE", "SEM 3-1", "EC301", "Digital Signal Processing", 4),

        # EEE
        ("EEE", "SEM 2-1", "EE201", "Electrical Circuit Analysis", 3),
        ("EEE", "SEM 2-2", "EE202", "Electrical Machines - I", 4),
        ("EEE", "SEM 3-1", "EE301", "Power Electronics", 4),

        # ME
        ("ME", "SEM 2-1", "ME201", "Engineering Thermodynamics", 3),
        ("ME", "SEM 2-2", "ME202", "Fluid Mechanics and Hydraulic Machines", 4),
        ("ME", "SEM 3-1", "ME301", "Design of Machine Elements", 4),

        # CE
        ("CE", "SEM 2-1", "CE201", "Strength of Materials", 3),
        ("CE", "SEM 2-2", "CE202", "Fluid Mechanics", 4),
        ("CE", "SEM 3-1", "CE301", "Structural Analysis - I", 4),
    ]

    for dept_code, sem_code, c_code, c_name, credits in courses_data:
        dept_id = dept_id_map.get(dept_code)
        sem_id = sem_id_map.get(sem_code)
        if dept_id and sem_id:
            cur.execute(
                """
                INSERT INTO courses (institution_id, department_id, semester_id, academic_year_id, course_code, course_name, credits)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (institution_id, department_id, course_code)
                DO UPDATE SET course_name = EXCLUDED.course_name, semester_id = EXCLUDED.semester_id, academic_year_id = EXCLUDED.academic_year_id
                """,
                (inst_id, dept_id, sem_id, current_year_id, c_code, c_name, credits)
            )
    print(f"[+] Ensured representative Courses across all departments and semesters.")

    # 8. Setup Primary Working Prototype Email: faculty@alits.ac.in
    # Password: Faculty@123
    primary_email = "faculty@alits.ac.in"
    primary_pwd = "Faculty@123"
    primary_hash = hash_password(primary_pwd)
    cse_id = dept_id_map["CSE"]

    cur.execute("SELECT id FROM users WHERE LOWER(email) = %s", (primary_email.lower(),))
    existing_faculty = cur.fetchone()
    if existing_faculty:
        cur.execute(
            """
            UPDATE users 
            SET name = 'Snehalatha', password_hash = %s, role = 'Faculty', 
                department_id = %s, institution_id = %s, is_active = TRUE
            WHERE id = %s
            RETURNING id
            """,
            (primary_hash, cse_id, inst_id, existing_faculty["id"])
        )
        faculty_user_id = existing_faculty["id"]
        print(f"[+] Updated primary working prototype email: {primary_email} (Password: {primary_pwd})")
    else:
        cur.execute(
            """
            INSERT INTO users (institution_id, department_id, name, email, password_hash, role, is_active)
            VALUES (%s, %s, 'Snehalatha', %s, %s, 'Faculty', TRUE)
            RETURNING id
            """,
            (inst_id, cse_id, primary_email.lower(), primary_hash)
        )
        faculty_user_id = cur.fetchone()["id"]
        print(f"[+] Created primary working prototype email: {primary_email} (Password: {primary_pwd})")

    # Also make sure the other demo email aliases have the exact same password and active status
    other_aliases = [
        ("odigepallisnehareddy@gmail.com", "Faculty@123", "Snehalatha", "Faculty", cse_id),
        ("faculty.cse@alitsprototype.test", "Faculty@123", "Snehalatha", "Faculty", cse_id),
        ("admin@alits.ac.in", "Admin@123", "Institutional Administrator", "Admin", None),
        ("hod.cse@alits.ac.in", "HOD@123", "Dr. K. Ramesh (HOD CSE)", "HOD", cse_id),
        ("auditor@alits.ac.in", "Auditor@123", "Institutional Auditor", "Auditor", None),
    ]
    for email, pwd, name, role, dept_id in other_aliases:
        h = hash_password(pwd)
        cur.execute("SELECT id FROM users WHERE LOWER(email) = %s", (email.lower(),))
        u = cur.fetchone()
        if u:
            cur.execute(
                "UPDATE users SET password_hash = %s, name = %s, role = %s, department_id = %s, institution_id = %s, is_active = TRUE WHERE id = %s",
                (h, name, role, dept_id, inst_id, u["id"])
            )
        else:
            cur.execute(
                "INSERT INTO users (institution_id, department_id, name, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, %s, %s, TRUE)",
                (inst_id, dept_id, name, email.lower(), h, role)
            )

    print("[SUCCESS] All departments, 8 semesters, academic years, courses, and the working prototype email are fully configured!")

if __name__ == "__main__":
    setup_full_academic_system()
