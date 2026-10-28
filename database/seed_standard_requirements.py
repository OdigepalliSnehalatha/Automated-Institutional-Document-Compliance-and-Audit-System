import sys
import json
from backend.database import get_db_cursor

sys.stdout.reconfigure(encoding="utf-8")

def seed_standards():
    with get_db_cursor(commit=True) as cursor:
        # 1. Ensure institution exists
        cursor.execute("SELECT id, name FROM institution LIMIT 1")
        inst = cursor.fetchone()
        inst_id = inst["id"] if inst else 6

        # 2. Ensure standard Document Types exist
        doc_types = [
            ("Course Structure", "Institutional standard format for Course Curriculum, Syllabus, and Unit Structure"),
            ("Question Bank", "Institutional standard format for 5-Unit Question Banks with Bloom's taxonomy & CO mapping"),
            ("Question Paper", "Institutional format for Mid-Semester (MID1, MID2) and End-Semester Examination Question Papers"),
            ("Lab Manual", "Institutional standard format for Laboratory Manuals, Experiments, and Rubrics")
        ]

        doc_type_map = {}
        for name, desc in doc_types:
            cursor.execute("SELECT id FROM document_types WHERE LOWER(name) = LOWER(%s)", (name,))
            row = cursor.fetchone()
            if row:
                doc_type_map[name] = row["id"]
            else:
                cursor.execute("""
                    INSERT INTO document_types (name, description, is_active)
                    VALUES (%s, %s, TRUE) RETURNING id
                """, (name, desc))
                doc_type_map[name] = cursor.fetchone()["id"]

        print(f"Document Types configured: {doc_type_map}")

        # 3. Master Formats and their Standard Requirements
        standard_formats = [
            {
                "name": "JNTUA Master Course Structure & Syllabus Format (R20/R23)",
                "doc_type": "Course Structure",
                "instructions": "Standard curriculum blueprint requiring official institutional header, academic regulation, course outcomes CO1-CO5, 5 units, and textbook citations.",
                "requirements": [
                    ("Searchable Digital Text Layer", "text", "Searchable text layer (non-scanned)", True, 1),
                    ("Institutional Header Banner", "header", "Anantha Lakshmi Institute of Technology and Sciences", True, 2),
                    ("Academic Regulation & Year", "text", "JNTUA Regulation (R20/R23) & Academic Year", True, 3),
                    ("Course / Subject Details", "heading", "Subject Code & Course Title", True, 4),
                    ("Course Outcomes (CO1-CO5)", "section", "Minimum 5 Course Outcomes mapped to Bloom's taxonomy", True, 5),
                    ("5-Unit Curriculum Architecture", "section", "Comprehensive coverage of Unit I through Unit V", True, 6),
                    ("Prescribed Textbooks & References", "section", "Standard textbooks with author, title, edition, and publisher", True, 7),
                    ("Evaluation & Marks Distribution", "marks", "Internal continuous assessment and end-semester weightage", True, 8)
                ]
            },
            {
                "name": "Institutional Master Question Bank Format (Units 1-5)",
                "doc_type": "Question Bank",
                "instructions": "Comprehensive unit-wise question bank requiring institutional header, dual-tier Part A (short) and Part B (long) questions, Bloom's cognitive levels, and CO mapping.",
                "requirements": [
                    ("Searchable Digital Text Layer", "text", "Searchable text layer (non-scanned)", True, 1),
                    ("Institutional Header Banner", "header", "Anantha Lakshmi Institute of Technology and Sciences", True, 2),
                    ("Course & Branch Identifier", "heading", "Department Name and Course Code", True, 3),
                    ("5-Unit Question Coverage", "section", "Questions spanning all 5 Units (Unit I to Unit V)", True, 4),
                    ("Dual-Tier Question Classification", "section", "Part A (Short Answer) and Part B (Descriptive/Analytical)", True, 5),
                    ("Bloom's Taxonomy & CO Mapping", "field", "Cognitive levels (L1-L4) and Course Outcome mapping (CO1-CO5)", True, 6),
                    ("Minimum Question Volume", "question_count", "Minimum 15-20 total questions across all units", True, 7),
                    ("Marks Allocation per Question", "marks", "Explicit marks declared for questions/sections", True, 8)
                ]
            },
            {
                "name": "Institutional Master Question Paper Format (Mid & Semester)",
                "doc_type": "Question Paper",
                "instructions": "Institutional standard examination question paper format with Part A and Part B division, question numbering, and 30/70 maximum marks.",
                "requirements": [
                    ("Searchable Digital Text Layer", "text", "Searchable text layer (non-scanned)", True, 1),
                    ("Institutional Header Banner", "header", "Anantha Lakshmi Institute of Technology and Sciences", True, 2),
                    ("Examination Type Specification", "heading", "Mid-Semester Examination / End-Semester Examination", True, 3),
                    ("Course Code & Title Matching", "field", "Approved Course Code and Subject Name", True, 4),
                    ("Section Breakdown (Part A & Part B)", "part a structure", "Part A and Part B clearly separated", True, 5),
                    ("Standard Question Numbering", "question_count", "Sequential numbering (Q1 to Q8+)", True, 6),
                    ("Total Maximum Marks Scheme", "marks", "30 Marks for Mid Exams, 70 Marks for Semester Exams", True, 7)
                ]
            },
            {
                "name": "Institutional Master Laboratory Manual Format",
                "doc_type": "Lab Manual",
                "instructions": "Standard laboratory manual requiring syllabus list of experiments, apparatus/software, procedures, safety guidelines, and evaluation rubrics.",
                "requirements": [
                    ("Searchable Digital Text Layer", "text", "Searchable text layer (non-scanned)", True, 1),
                    ("Institutional Header Banner", "header", "Anantha Lakshmi Institute of Technology and Sciences", True, 2),
                    ("Laboratory Course Identification", "heading", "Practical / Lab Subject Code and Title", True, 3),
                    ("Syllabus List of Experiments", "section", "Minimum 10-12 structured laboratory experiments", True, 4),
                    ("Experiment Standard Architecture", "section", "Aim, Apparatus/Software, Procedure, Viva-Voce", True, 5),
                    ("Laboratory Safety Guidelines", "section", "Institutional lab safety protocols and conduct", True, 6),
                    ("Continuous Evaluation Rubrics", "marks", "Day-to-day evaluation, Record, and Practical Exam marks", True, 7)
                ]
            }
        ]

        for fmt in standard_formats:
            dt_id = doc_type_map[fmt["doc_type"]]
            cursor.execute("""
                SELECT id FROM document_formats 
                WHERE institution_id = %s AND document_type_id = %s AND LOWER(format_name) = LOWER(%s)
            """, (inst_id, dt_id, fmt["name"]))
            existing = cursor.fetchone()

            if existing:
                fmt_id = existing["id"]
                cursor.execute("UPDATE document_formats SET instructions = %s WHERE id = %s", (fmt["instructions"], fmt_id))
                cursor.execute("DELETE FROM format_requirements WHERE format_id = %s", (fmt_id,))
            else:
                cursor.execute("""
                    INSERT INTO document_formats 
                        (institution_id, department_id, document_type_id, format_name, instructions, created_by)
                    VALUES (%s, NULL, %s, %s, %s, 1)
                    RETURNING id
                """, (inst_id, dt_id, fmt["name"], fmt["instructions"]))
                fmt_id = cursor.fetchone()["id"]

            for req_name, req_type, req_val, is_req, order in fmt["requirements"]:
                cursor.execute("""
                    INSERT INTO format_requirements 
                        (format_id, requirement_name, requirement_type, requirement_value, is_required, display_order)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fmt_id, req_name, req_type, req_val, is_req, order))

            print(f"✓ Seeded standard format: '{fmt['name']}' with {len(fmt['requirements'])} requirements.")

    print("\nMaster Standard Requirements Seeded Successfully!")

if __name__ == "__main__":
    seed_standards()
