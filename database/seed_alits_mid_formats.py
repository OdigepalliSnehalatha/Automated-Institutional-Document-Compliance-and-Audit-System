import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_cursor

def seed_mid_formats():
    print("[*] Seeding ALITS Autonomous Mid-1 and Mid-2 Standard Requirements...")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM document_types WHERE name = 'Question Paper'")
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO document_types (name, description, is_active) VALUES ('Question Paper', 'Examination Question Papers', TRUE) RETURNING id")
            row = cursor.fetchone()
        doc_type_id = row["id"]

        # 1. Standard Mid-1 Format
        mid1_reqs = [
            ("College Header", "header", "Anantha Lakshmi Institute of Technology & Sciences", True, 1),
            ("Autonomous Status", "text", "(AUTONOMOUS)", True, 2),
            ("Institutional Location", "text", "Near S.K. University, Ananthapuramu- 515721", True, 3),
            ("Class & Semester", "heading", "B.Tech Semester (e.g., I B.Tech II Semester)", True, 4),
            ("Examination Title", "heading", "I-MID Examinations", True, 5),
            ("Subject with Code", "heading", "Subject with Code: [Subject Name] : [Subject Code]", True, 6),
            ("Branch Identifier", "text", "Branch: CSE, EEE (or designated engineering branch)", True, 7),
            ("Academic Regulations", "text", "Regulations: R-24", True, 8),
            ("Time Duration", "text", "Time: 110 Min", True, 9),
            ("Maximum Marks", "marks", "Max. Marks: 40", True, 10),
            ("General Instruction", "text", "Answer all questions", True, 11),
            ("Table Column: S.No", "structure", "S.No", True, 12),
            ("Table Column: Blooms Level", "structure", "Blooms Level (e.g. Apply, Remember, Understand, Analyze)", True, 13),
            ("Table Column: Course Outcome", "structure", "Course Outcome (e.g. CO1 to CO6)", True, 14),
            ("Table Column: Marks", "structure", "Marks (e.g. 2, 5, 10)", True, 15),
            ("Question 1 (Short Answer Section)", "question_count", "Question 1 with 5 sub-questions (a, b, c, d, e) @ 2 Marks each = 10 Marks", True, 16),
            ("Unit Syllabus Architecture", "structure", "UNIT-I, UNIT-II, and UNIT-III (Part)", True, 17),
            ("Descriptive Internal Choice (OR)", "structure", "Internal Choice 'OR' between questions under each Unit", True, 18),
            ("Unit Descriptive Marks Weightage", "marks", "Each Unit carries 10 Marks (either single 10M or subdivided 5M + 5M)", True, 19),
            ("Total Marks Scheme Verification", "marks", "Total 40 Marks (Q1: 10M + 3 Units x 10M = 40 Marks)", True, 20),
        ]

        # 2. Standard Mid-2 Format
        mid2_reqs = [
            ("College Header", "header", "Anantha Lakshmi Institute of Technology & Sciences", True, 1),
            ("Autonomous Status", "text", "(AUTONOMOUS)", True, 2),
            ("Institutional Location", "text", "Near S.K. University, Ananthapuramu- 515721", True, 3),
            ("Class & Semester", "heading", "B.Tech Semester (e.g., I B.Tech II Semester)", True, 4),
            ("Examination Title", "heading", "II-MID Examinations", True, 5),
            ("Subject with Code", "heading", "Subject with Code: [Subject Name] : [Subject Code]", True, 6),
            ("Branch Identifier", "text", "Branch: CSE, EEE (or designated engineering branch)", True, 7),
            ("Academic Regulations", "text", "Regulations: R-24", True, 8),
            ("Time Duration", "text", "Time: 110 Min", True, 9),
            ("Maximum Marks", "marks", "Max. Marks: 40", True, 10),
            ("General Instruction", "text", "Answer all questions", True, 11),
            ("Table Column: S.No", "structure", "S.No", True, 12),
            ("Table Column: Blooms Level", "structure", "Blooms Level (e.g. Apply, Remember, Understand, Analyze)", True, 13),
            ("Table Column: Course Outcome", "structure", "Course Outcome (e.g. CO1 to CO6)", True, 14),
            ("Table Column: Marks", "structure", "Marks (e.g. 2, 5, 10)", True, 15),
            ("Question 1 (Short Answer Section)", "question_count", "Question 1 with 5 sub-questions (a, b, c, d, e) @ 2 Marks each = 10 Marks", True, 16),
            ("Unit Syllabus Architecture", "structure", "UNIT-III, UNIT-IV, and UNIT-V", True, 17),
            ("Descriptive Internal Choice (OR)", "structure", "Internal Choice 'OR' between questions under each Unit", True, 18),
            ("Unit Descriptive Marks Weightage", "marks", "Each Unit carries 10 Marks (either single 10M or subdivided 5M + 5M)", True, 19),
            ("Total Marks Scheme Verification", "marks", "Total 40 Marks (Q1: 10M + 3 Units x 10M = 40 Marks)", True, 20),
        ]

        formats_to_seed = [
            (
                "Standard I-MID Question Paper Format (Autonomous R-24 / 40 Marks)",
                "I-MID Examinations (Autonomous R-24 Format). Requires official header with (AUTONOMOUS), location 515721, Subject with Code, Regulations: R-24, Time: 110 Min, Max Marks: 40, Table format with Blooms Level & CO, Question 1 (a-e @ 2M = 10M), and 3 Unit questions with internal choice (10M each). Total = 40 Marks.",
                mid1_reqs
            ),
            (
                "Standard II-MID Question Paper Format (Autonomous R-24 / 40 Marks)",
                "II-MID Examinations (Autonomous R-24 Format). Requires official header with (AUTONOMOUS), location 515721, Subject with Code, Regulations: R-24, Time: 110 Min, Max Marks: 40, Table format with Blooms Level & CO, Question 1 (a-e @ 2M = 10M), and 3 Unit questions with internal choice (10M each). Total = 40 Marks.",
                mid2_reqs
            )
        ]

        cursor.execute("SELECT id FROM users WHERE role IN ('Admin', 'Auditor') LIMIT 1")
        user_row = cursor.fetchone()
        user_id = user_row["id"] if user_row else 1

        for fmt_name, instructions, req_list in formats_to_seed:
            cursor.execute("SELECT id FROM document_formats WHERE format_name = %s", (fmt_name,))
            existing = cursor.fetchone()
            if existing:
                fmt_id = existing["id"]
                cursor.execute("UPDATE document_formats SET instructions = %s, document_type_id = %s WHERE id = %s", (instructions, doc_type_id, fmt_id))
                cursor.execute("DELETE FROM format_requirements WHERE format_id = %s", (fmt_id,))
                print(f"[+] Updated existing format: {fmt_name}")
            else:
                cursor.execute(
                    "INSERT INTO document_formats (institution_id, document_type_id, format_name, instructions, created_by) VALUES (6, %s, %s, %s, %s) RETURNING id",
                    (doc_type_id, fmt_name, instructions, user_id)
                )
                fmt_id = cursor.fetchone()["id"]
                print(f"[+] Inserted new format: {fmt_name}")

            for r_name, r_type, r_val, is_req, order in req_list:
                cursor.execute(
                    """
                    INSERT INTO format_requirements (format_id, requirement_name, requirement_type, requirement_value, is_required, display_order)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (fmt_id, r_name, r_type, r_val, is_req, order)
                )
            print(f"[+] Seeded {len(req_list)} rules for {fmt_name}")

    print("[SUCCESS] All Mid 1 and Mid 2 standard requirements seeded into PostgreSQL!")

if __name__ == "__main__":
    seed_mid_formats()
