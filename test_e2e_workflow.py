import sys
import io
import json

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import pymupdf as fitz
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db_cursor

client = TestClient(app)

INSTITUTION = "Anantha Lakshmi Institute of Technology and Sciences"

def get_latest_otp(email: str, role: str) -> str:
    # Helper to look up active OTP from test database to simulate user reading email
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, otp_hash FROM login_otps
            WHERE LOWER(email) = LOWER(%s) AND role = %s AND is_used = FALSE
            ORDER BY created_at DESC LIMIT 1
            """,
            (email, role)
        )
        # In real life, user receives the 6-digit code via email or console.
        # Since hash is stored, our otp_service printed it to console or we can generate one.
    return None

def create_sample_pdf(content_type="valid_question_paper") -> bytes:
    doc = fitz.open()
    page = doc.new_page()

    if content_type == "valid_question_paper":
        text = """ANANTHA LAKSHMI INSTITUTE OF TECHNOLOGY AND SCIENCES
B.Tech Mid Examination - Semester III
Department of Computer Science & Engineering
Subject: Computer Networks | Subject Code: CS301 | Time: 2 Hours | Maximum Marks: 70

PART A (Answer all questions, 5 x 2 = 10 Marks)
1. Define network topology with examples. [2 marks]
2. What is the function of the Physical Layer? [2 marks]
3. Explain the difference between bit rate and baud rate. [2 marks]
4. What is cyclic redundancy check (CRC)? [2 marks]
5. Define flow control and error control. [2 marks]

PART B (Answer all questions, 6 x 10 = 60 Marks)
1. Explain the OSI 7-Layer Reference Model with neat diagrams and functions of each layer. [10 marks]
2. Compare and contrast TCP and UDP transport protocols in detail. [10 marks]
3. Describe the Sliding Window Protocol with selective repeat mechanism. [10 marks]
4. Explain Distance Vector Routing Algorithm and count-to-infinity problem. [10 marks]
5. Discuss Carrier Sense Multiple Access with Collision Detection (CSMA/CD). [10 marks]
6. Explain the architecture and message formats of Domain Name System (DNS). [10 marks]

*** End of Question Paper - Confidential Institutional Record ***
"""
    elif content_type == "invalid_question_paper":
        # Missing Part B completely!
        text = """ANANTHA LAKSHMI INSTITUTE OF TECHNOLOGY AND SCIENCES
B.Tech Mid Examination
Department of Computer Science & Engineering
Subject: Computer Networks | Maximum Marks: 70

PART A (Answer all questions)
1. Define network topology. [2 marks]
2. What is the function of the Physical Layer? [2 marks]

*** End of Question Paper ***
"""
    elif content_type == "valid_course_structure":
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

References and Text Books:
1. Introduction to Algorithms - Cormen, Leiserson, Rivest.
"""

    rect = fitz.Rect(50, 50, 550, 800)
    page.insert_textbox(rect, text, fontsize=10, fontname="helv")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def run_tests():
    print("=======================================================")
    print("STARTING COMPREHENSIVE END-TO-END WORKFLOW TESTS")
    print("=======================================================")

    # ---------------------------------------------------------
    # TEST 1: Authentication Security & Failures
    # ---------------------------------------------------------
    print("\n[TEST 1] Verifying Login Security & Validation Failures...")

    # Wrong password
    res = client.post("/login", json={
        "institution_name": INSTITUTION,
        "role": "Auditor",
        "email": "auditor@alitsprototype.test",
        "password": "WrongPassword!999"
    })
    assert res.status_code == 401, f"Expected 401 for wrong password, got {res.status_code}"
    print("  ✓ Invalid password rejected with 401")

    # Wrong institution
    res = client.post("/login", json={
        "institution_name": "NonExistent Institute",
        "role": "Auditor",
        "email": "auditor@alitsprototype.test",
        "password": "Auditor@123"
    })
    assert res.status_code == 401, f"Expected 401 for wrong institution, got {res.status_code}"
    print("  ✓ Wrong institution rejected with 401")

    # Wrong role
    res = client.post("/login", json={
        "institution_name": INSTITUTION,
        "role": "Faculty",
        "email": "auditor@alitsprototype.test",
        "password": "Auditor@123"
    })
    assert res.status_code == 401, f"Expected 401 for mismatched role, got {res.status_code}"
    print("  ✓ Mismatched role rejected with 401")

    # ---------------------------------------------------------
    # TEST 2: Auditor Login & OTP Verification Flow
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Auditor Login & Session Verification...")
    auditor_client = TestClient(app)

    res = auditor_client.post("/login", json={
        "institution_name": INSTITUTION,
        "role": "Auditor",
        "email": "auditor@alitsprototype.test",
        "password": "Auditor@123"
    })
    assert res.status_code == 200 and res.json().get("requires_otp"), f"Expected 200 requires_otp, got {res.text}"
    print("  ✓ Auditor credentials valid, OTP dispatched")

    # Find the generated OTP in login_otps by hashing attempts or test DB
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, otp_hash FROM login_otps WHERE email = 'auditor@alitsprototype.test' AND is_used = FALSE ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        assert row is not None, "Login OTP record was not inserted"

    # Test invalid OTP
    res = auditor_client.post("/verify-otp", json={
        "institution_name": INSTITUTION,
        "role": "Auditor",
        "email": "auditor@alitsprototype.test",
        "otp": "000000"
    })
    assert res.status_code == 400, f"Expected 400 for bad OTP, got {res.status_code}"
    print("  ✓ Bad OTP rejected with 400")

    # Now verify with correct OTP
    # For automated test, let's look up the plain OTP from our test session or seed a known OTP
    from backend.services.otp_service import hash_otp
    known_otp = "123456"
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE login_otps SET otp_hash = %s, attempts = 0 WHERE id = %s",
            (hash_otp(known_otp), row["id"])
        )

    res = auditor_client.post("/verify-otp", json={
        "institution_name": INSTITUTION,
        "role": "Auditor",
        "email": "auditor@alitsprototype.test",
        "otp": known_otp
    })
    assert res.status_code == 200, f"Expected 200 on OTP verify, got {res.text}"
    assert res.json().get("authenticated") is True
    print("  ✓ Auditor OTP verified successfully, session cookie received")

    # Test /auth/me session restoration
    res = auditor_client.get("/auth/me")
    assert res.status_code == 200
    user_me = res.json()["user"]
    assert user_me["role"] == "Auditor"
    assert user_me["institution"] == INSTITUTION
    print("  ✓ /auth/me returns authenticated user details correctly")

    # ---------------------------------------------------------
    # TEST 3: Auditor Creates Master Structural Format
    # ---------------------------------------------------------
    print("\n[TEST 3] Auditor Creating Master Structural Format...")
    format_payload = {
        "institution_id": user_me["institution_id"],
        "department_id": None, # Institution-wide
        "document_type_id": 8, # Question Paper
        "format_name": "Standard Mid Examination Format",
        "instructions": "Strict compliance rules for Mid Examinations.",
        "requirements": [
            {"requirement_name": "College Header", "requirement_type": "header", "requirement_value": "Anantha Lakshmi", "is_required": True, "display_order": 1},
            {"requirement_name": "Examination Type", "requirement_type": "field", "requirement_value": "Mid Examination", "is_required": True, "display_order": 2},
            {"requirement_name": "Part A", "requirement_type": "part a structure", "requirement_value": "Part A", "is_required": True, "display_order": 3},
            {"requirement_name": "Part A Question Count", "requirement_type": "question_count", "requirement_value": "5", "is_required": True, "display_order": 4},
            {"requirement_name": "Part A Marks Pattern", "requirement_type": "marks", "requirement_value": "2", "is_required": True, "display_order": 5},
            {"requirement_name": "Part B", "requirement_type": "part b structure", "requirement_value": "Part B", "is_required": True, "display_order": 6},
            {"requirement_name": "Part B Question Count", "requirement_type": "question_count", "requirement_value": "6", "is_required": True, "display_order": 7},
            {"requirement_name": "Part B Marks Pattern", "requirement_type": "marks", "requirement_value": "10", "is_required": True, "display_order": 8},
            {"requirement_name": "Footer", "requirement_type": "footer", "requirement_value": "End of Question Paper", "is_required": True, "display_order": 9}
        ]
    }
    res = auditor_client.post("/formats", json=format_payload)
    assert res.status_code == 200, f"Format creation failed: {res.text}"
    created_format = res.json()["format"]
    format_id = created_format["id"]
    print(f"  ✓ Structural format created successfully (ID: {format_id}, Rules: {len(created_format['requirements'])})")

    # Verify format listing
    res = auditor_client.get("/formats")
    assert res.status_code == 200
    formats_list = res.json()
    assert any(f["id"] == format_id for f in formats_list)
    print("  ✓ Formats listed successfully with embedded requirements")

    # ---------------------------------------------------------
    # TEST 4: Faculty Login & Document Uploads
    # ---------------------------------------------------------
    print("\n[TEST 4] Testing Faculty Login & Document Upload Workflow...")
    faculty_client = TestClient(app)

    res = faculty_client.post("/login", json={
        "institution_name": INSTITUTION,
        "role": "Faculty",
        "email": "faculty.cse@alitsprototype.test",
        "password": "Faculty@123"
    })
    assert res.status_code == 200

    # Retrieve and verify OTP
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM login_otps WHERE email = 'faculty.cse@alitsprototype.test' AND is_used = FALSE ORDER BY id DESC LIMIT 1")
        f_row = cursor.fetchone()
        cursor.execute("UPDATE login_otps SET otp_hash = %s, attempts = 0 WHERE id = %s", (hash_otp(known_otp), f_row["id"]))

    res = faculty_client.post("/verify-otp", json={
        "institution_name": INSTITUTION,
        "role": "Faculty",
        "email": "faculty.cse@alitsprototype.test",
        "otp": known_otp
    })
    assert res.status_code == 200
    print("  ✓ Faculty authenticated successfully")

    # Upload Valid PDF
    valid_pdf = create_sample_pdf("valid_question_paper")
    res = faculty_client.post(
        "/documents/upload",
        data={"document_type_id": 8, "department_id": 1},
        files={"file": ("Mid_Exam_Valid.pdf", valid_pdf, "application/pdf")}
    )
    assert res.status_code == 200, f"Upload failed: {res.text}"
    valid_doc = res.json()["document"]
    valid_doc_id = valid_doc["id"]
    print(f"  ✓ Valid Question Paper PDF uploaded (ID: {valid_doc_id})")

    # Upload Invalid PDF (Missing Part B)
    invalid_pdf = create_sample_pdf("invalid_question_paper")
    res = faculty_client.post(
        "/documents/upload",
        data={"document_type_id": 8, "department_id": 1},
        files={"file": ("Mid_Exam_Defective.pdf", invalid_pdf, "application/pdf")}
    )
    assert res.status_code == 200
    invalid_doc = res.json()["document"]
    invalid_doc_id = invalid_doc["id"]
    print(f"  ✓ Defective Question Paper PDF uploaded (ID: {invalid_doc_id})")

    # ---------------------------------------------------------
    # TEST 5: Structural Analysis & Strict Decision Rule
    # ---------------------------------------------------------
    print("\n[TEST 5] Executing Structural Analysis & Testing Decision Rules...")

    # Analyze Valid Document -> MUST BE ACCEPTED
    res = faculty_client.post(f"/documents/{valid_doc_id}/analyze")
    assert res.status_code == 200, f"Analysis failed: {res.text}"
    analysis_res = res.json()["result"]
    print("  Valid Doc Analysis Status:", analysis_res["status"])
    assert analysis_res["status"] == "ACCEPTED", f"Expected ACCEPTED for valid document, got {analysis_res['status']}"
    print("  ✓ Valid Document strictly evaluated as ACCEPTED (all rules passed)")

    # Analyze Defective Document -> MUST BE REJECTED
    res = faculty_client.post(f"/documents/{invalid_doc_id}/analyze")
    assert res.status_code == 200
    analysis_res_invalid = res.json()["result"]
    print("  Defective Doc Analysis Status:", analysis_res_invalid["status"])
    assert analysis_res_invalid["status"] == "REJECTED", f"Expected REJECTED for defective document, got {analysis_res_invalid['status']}"

    # Verify failure reasons in requirement breakdown
    failed_reqs = [r for r in analysis_res_invalid["requirements"] if r["status"] == "FAIL"]
    assert len(failed_reqs) > 0, "Expected at least one failed requirement in defective document"
    print(f"  ✓ Defective Document strictly evaluated as REJECTED ({len(failed_reqs)} failed rules with reasons):")
    for f in failed_reqs:
        print(f"     - Rule '{f['name']}': Reason: {f['reason']}")

    # ---------------------------------------------------------
    # TEST 6: HOD Workflow & Accepted PDF Downloads
    # ---------------------------------------------------------
    print("\n[TEST 6] Testing HOD Access, Department Documents & Download Permissions...")
    hod_client = TestClient(app)

    res = hod_client.post("/login", json={
        "institution_name": INSTITUTION,
        "role": "HOD",
        "email": "hod.cse@alitsprototype.test",
        "password": "Hod@123"
    })
    assert res.status_code == 200

    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM login_otps WHERE email = 'hod.cse@alitsprototype.test' AND is_used = FALSE ORDER BY id DESC LIMIT 1")
        h_row = cursor.fetchone()
        cursor.execute("UPDATE login_otps SET otp_hash = %s, attempts = 0 WHERE id = %s", (hash_otp(known_otp), h_row["id"]))

    res = hod_client.post("/verify-otp", json={
        "institution_name": INSTITUTION,
        "role": "HOD",
        "email": "hod.cse@alitsprototype.test",
        "otp": known_otp
    })
    assert res.status_code == 200
    print("  ✓ HOD authenticated successfully")

    # HOD Views Department Documents
    res = hod_client.get("/hod/documents")
    assert res.status_code == 200
    dept_docs = res.json()
    assert any(d["id"] == valid_doc_id for d in dept_docs)
    print("  ✓ HOD can view department submitted documents")

    # HOD Views Accepted Documents
    res = hod_client.get("/hod/accepted-documents")
    assert res.status_code == 200
    accepted_docs = res.json()
    assert any(d["id"] == valid_doc_id for d in accepted_docs)
    assert not any(d["id"] == invalid_doc_id for d in accepted_docs)
    print("  ✓ HOD accepted documents list only includes strictly ACCEPTED documents")

    # SECURITY CHECK: Attempting to download REJECTED PDF
    res = hod_client.get(f"/documents/{invalid_doc_id}/download")
    assert res.status_code == 403, f"Expected 403 when downloading rejected document, got {res.status_code}"
    print("  ✓ Security Enforced: Rejected PDF download blocked with 403 Forbidden")

    # HOD downloads ACCEPTED PDF
    res = hod_client.get(f"/documents/{valid_doc_id}/download")
    assert res.status_code == 200, f"Expected 200 when downloading accepted document, got {res.status_code}"
    assert res.headers["content-type"] == "application/pdf"
    print("  ✓ Authorized Download: HOD successfully downloaded accepted PDF")

    # Auditor downloads ACCEPTED PDF
    res = auditor_client.get(f"/documents/{valid_doc_id}/download")
    assert res.status_code == 200
    print("  ✓ Authorized Download: Auditor successfully downloaded accepted PDF")

    # Faculty downloads blocked
    res = faculty_client.get(f"/documents/{valid_doc_id}/download")
    assert res.status_code == 403
    print("  ✓ Role Security Enforced: Faculty blocked from accepted-document download endpoint")

    # ---------------------------------------------------------
    # TEST 7: Logout Destroys Session
    # ---------------------------------------------------------
    print("\n[TEST 7] Testing Logout & Session Invalidation...")
    res = auditor_client.post("/logout")
    assert res.status_code == 200

    # /auth/me must now return 401
    res = auditor_client.get("/auth/me")
    assert res.status_code == 401, f"Expected 401 after logout, got {res.status_code}"
    print("  ✓ Session destroyed on logout, subsequent requests return 401")

    print("\n=======================================================")
    print("ALL END-TO-END WORKFLOW TESTS PASSED SUCCESSFULLY! ✓")
    print("=======================================================\n")

if __name__ == "__main__":
    run_tests()
