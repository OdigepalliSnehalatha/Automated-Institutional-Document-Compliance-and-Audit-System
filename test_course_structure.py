import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pymupdf as fitz
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db_cursor
from backend.services.otp_service import hash_otp

client = TestClient(app)
INSTITUTION = "Anantha Lakshmi Institute of Technology and Sciences"
KNOWN_OTP = "123456"

def test_course_structure_and_qbank():
    print("Testing Course Structure & Question Bank structural flows...")

    # 1. Auditor creates Course Structure format
    auditor_client = TestClient(app)
    auditor_client.post("/login", json={
        "institution_name": INSTITUTION,
        "role": "Auditor",
        "email": "auditor@alitsprototype.test",
        "password": "Auditor@123"
    })
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM login_otps WHERE email = 'auditor@alitsprototype.test' AND is_used = FALSE ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        cursor.execute("UPDATE login_otps SET otp_hash = %s, attempts = 0 WHERE id = %s", (hash_otp(KNOWN_OTP), row["id"]))
    auditor_client.post("/verify-otp", json={
        "institution_name": INSTITUTION, "role": "Auditor", "email": "auditor@alitsprototype.test", "otp": KNOWN_OTP
    })

    # Create Course Structure format
    cs_format = {
        "institution_id": 6,
        "department_id": None,
        "document_type_id": 1, # Course Structure
        "format_name": "Standard Course Structure Format",
        "instructions": "Units 1-5 structural outline",
        "requirements": [
            {"requirement_name": "College Name", "requirement_type": "header", "requirement_value": "Anantha Lakshmi", "is_required": True, "display_order": 1},
            {"requirement_name": "Course Name", "requirement_type": "field", "requirement_value": "Data Structures", "is_required": True, "display_order": 2},
            {"requirement_name": "Course Code", "requirement_type": "field", "requirement_value": "CS202", "is_required": True, "display_order": 3},
            {"requirement_name": "Unit 1 Heading", "requirement_type": "heading", "requirement_value": "Unit 1", "is_required": True, "display_order": 4},
            {"requirement_name": "Unit 1 Topics", "requirement_type": "section", "requirement_value": "Unit 1", "is_required": True, "display_order": 5},
            {"requirement_name": "Unit 2 Heading", "requirement_type": "heading", "requirement_value": "Unit 2", "is_required": True, "display_order": 6},
            {"requirement_name": "Unit 2 Topics", "requirement_type": "section", "requirement_value": "Unit 2", "is_required": True, "display_order": 7},
            {"requirement_name": "Unit 3 Heading", "requirement_type": "heading", "requirement_value": "Unit 3", "is_required": True, "display_order": 8},
            {"requirement_name": "Unit 3 Topics", "requirement_type": "section", "requirement_value": "Unit 3", "is_required": True, "display_order": 9},
            {"requirement_name": "Unit 4 Heading", "requirement_type": "heading", "requirement_value": "Unit 4", "is_required": True, "display_order": 10},
            {"requirement_name": "Unit 4 Topics", "requirement_type": "section", "requirement_value": "Unit 4", "is_required": True, "display_order": 11},
            {"requirement_name": "Unit 5 Heading", "requirement_type": "heading", "requirement_value": "Unit 5", "is_required": True, "display_order": 12},
            {"requirement_name": "Unit 5 Topics", "requirement_type": "section", "requirement_value": "Unit 5", "is_required": True, "display_order": 13},
        ]
    }
    res = auditor_client.post("/formats", json=cs_format)
    assert res.status_code == 200, f"Error creating CS format: {res.text}"
    print("  ✓ Course Structure format created")

    # Faculty uploads valid Course Structure
    faculty_client = TestClient(app)
    faculty_client.post("/login", json={
        "institution_name": INSTITUTION,
        "role": "Faculty",
        "email": "faculty.cse@alitsprototype.test",
        "password": "Faculty@123"
    })
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM login_otps WHERE email = 'faculty.cse@alitsprototype.test' AND is_used = FALSE ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        cursor.execute("UPDATE login_otps SET otp_hash = %s, attempts = 0 WHERE id = %s", (hash_otp(KNOWN_OTP), row["id"]))
    faculty_client.post("/verify-otp", json={
        "institution_name": INSTITUTION, "role": "Faculty", "email": "faculty.cse@alitsprototype.test", "otp": KNOWN_OTP
    })

    doc = fitz.open()
    page = doc.new_page()
    text = """ANANTHA LAKSHMI INSTITUTE OF TECHNOLOGY AND SCIENCES
Course Structure and Syllabus
Course Name: Data Structures and Algorithms
Course Code: CS202

Unit 1: Introduction to Data Structures and Arrays
Unit 1 Topics: Stacks, queues, linked lists, array implementations, time complexity.

Unit 2: Trees and Binary Trees
Unit 2 Topics: Binary search trees, AVL trees, tree traversals, expression trees.

Unit 3: Graphs and Graph Algorithms
Unit 3 Topics: Graph representations, BFS, DFS, Dijkstra algorithm, Minimum Spanning Trees.

Unit 4: Sorting and Searching Techniques
Unit 4 Topics: Quick sort, merge sort, heap sort, linear and binary search algorithms.

Unit 5: Hashing and Advanced Structures
Unit 5 Topics: Hash functions, collision resolution, open addressing, chaining, B-trees.
"""
    page.insert_textbox(fitz.Rect(50, 50, 550, 800), text, fontsize=10, fontname="helv")
    pdf_bytes = doc.tobytes()
    doc.close()

    res = faculty_client.post(
        "/documents/upload",
        data={"document_type_id": 1, "department_id": 1},
        files={"file": ("Course_Structure_CS202.pdf", pdf_bytes, "application/pdf")}
    )
    assert res.status_code == 200
    doc_id = res.json()["document"]["id"]

    res = faculty_client.post(f"/documents/{doc_id}/analyze")
    assert res.status_code == 200
    status = res.json()["status"]
    assert status == "ACCEPTED", f"Expected ACCEPTED, got {status}"
    print(f"  ✓ Course Structure analyzed: {status}")

if __name__ == "__main__":
    test_course_structure_and_qbank()
