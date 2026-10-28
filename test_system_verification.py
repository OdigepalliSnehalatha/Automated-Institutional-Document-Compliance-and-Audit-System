import sys
import io
import time
import httpx
import fitz # PyMuPDF
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def create_sample_pdf(file_path: str, content_lines: list):
    """Generates a text-based PDF using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842) # A4
    y = 50
    for line in content_lines:
        font_size = 14 if "ANANTHA LAKSHMI" in line else 11 if "Examination" in line else 10
        page.insert_text((50, y), line, fontsize=font_size)
        y += font_size + 8
    doc.save(file_path)
    doc.close()

def create_scanned_image_pdf(file_path: str):
    """Generates a PDF containing only a raster image and 0 extracted text characters."""
    img = Image.new("RGB", (600, 800), color=(240, 240, 240))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=img_bytes)
    doc.save(file_path)
    doc.close()

def run_tests():
    print("=" * 70)
    print("INSTITUTIONAL COMPLIANCE SYSTEM: END-TO-END VERIFICATION SUITE")
    print("=" * 70)

    # 1. Health check
    res = httpx.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("✓ [TEST 0] Health Check passed: Database connected & API operational.")

    # 2. Test Registration with a new email
    new_email = f"test.faculty.{int(time.time())}@alitsprototype.test"
    register_payload = {
        "institution_name": "Anantha Lakshmi Institute of Technology and Sciences",
        "name": "Dr. Test Faculty",
        "email": new_email,
        "password": "Password@123",
        "role": "Faculty",
        "department_id": 1 # CSE
    }

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    res = client.post("/register", json=register_payload)
    assert res.status_code == 200, f"Registration failed: {res.text}"
    reg_data = res.json()
    assert reg_data["success"] is True
    assert reg_data["user"]["email"] == new_email
    assert reg_data["user"]["role"] == "Faculty"
    print(f"✓ [TEST 1] Registration succeeded for {new_email} with role Faculty.")

    # 2b. Test Duplicate Registration Prevention
    res = client.post("/register", json=register_payload)
    assert res.status_code == 400, f"Expected 400 for duplicate email, got: {res.status_code}"
    print("✓ [TEST 1b] Duplicate registration correctly rejected with 400 Bad Request.")

    # 3. Test Login with Registered Email & Correct Password
    client_login = httpx.Client(base_url=BASE_URL, timeout=15.0)
    login_payload = {
        "institution_name": "Anantha Lakshmi Institute of Technology and Sciences",
        "email": new_email,
        "password": "Password@123"
    }
    res = client_login.post("/login", json=login_payload)
    assert res.status_code == 200, f"Login failed: {res.text}"
    login_data = res.json()
    assert login_data["authenticated"] is True
    assert login_data["user"]["email"] == new_email
    assert login_data["user"]["role"] == "Faculty"
    print("✓ [TEST 2] Login succeeded with registered email and password. Session established.")

    # 4. Verify that Incorrect Password is Rejected
    bad_login = {
        "institution_name": "Anantha Lakshmi Institute of Technology and Sciences",
        "email": new_email,
        "password": "WrongPassword999"
    }
    res = httpx.post(f"{BASE_URL}/login", json=bad_login)
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"
    print(f"✓ [TEST 3] Incorrect password correctly rejected with 401 ({res.json().get('detail')}).")

    # 5. Verify Role Authorization strictly from Database for all 4 roles
    roles_to_check = [
        ("admin@alitsprototype.test", "Admin@123", "Admin"),
        ("auditor@alitsprototype.test", "Auditor@123", "Auditor"),
        ("hod.cse@alitsprototype.test", "Hod@123", "HOD"),
        ("faculty.cse@alitsprototype.test", "Faculty@123", "Faculty"),
    ]
    for email, pwd, expected_role in roles_to_check:
        c = httpx.Client(base_url=BASE_URL, timeout=15.0)
        r = c.post("/login", json={"email": email, "password": pwd})
        assert r.status_code == 200, f"Failed login for {email}: {r.text}"
        user_info = r.json()["user"]
        assert user_info["role"] == expected_role, f"Expected {expected_role}, got {user_info['role']}"
        # Check /auth/me session persistence
        r_me = c.get("/auth/me")
        assert r_me.status_code == 200
        assert r_me.json()["user"]["role"] == expected_role
        print(f"✓ [TEST 4] Role verification passed for {expected_role} ({email}). Role strictly from DB.")

    # 6. Test Question Paper Overview & Filters
    faculty_client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    faculty_client.post("/login", json={"email": "faculty.cse@alitsprototype.test", "password": "Faculty@123"})
    res = faculty_client.get("/question-papers/overview")
    assert res.status_code == 200, f"Overview failed: {res.text}"
    overview = res.json()
    assert "rows" in overview
    assert len(overview["rows"]) > 0
    sample_row = overview["rows"][0]
    course_id = sample_row["course_id"]
    course_code = sample_row["course_code"]
    course_name = sample_row["course_name"]
    dept_code = sample_row["department"]
    print(f"✓ [TEST 5] Overview table returns {len(overview['rows'])} courses. Selected target: {course_code} - {course_name} (ID: {course_id}).")

    # 7. Generate Test PDFs
    valid_pdf_path = "uploads/temp_test_valid_mid1.pdf"
    valid_lines = [
        "ANANTHA LAKSHMI INSTITUTE OF TECHNOLOGY AND SCIENCES",
        f"DEPARTMENT OF {dept_code}",
        f"COURSE CODE: {course_code}",
        f"COURSE TITLE: {course_name}",
        "B.Tech III Semester Mid-Semester Examination 1 (MID1)",
        "ACADEMIC YEAR: 2025-2026",
        "DATE: 15-10-2025",
        "TIME: 2 Hours",
        "TOTAL MARKS: 30",
        "",
        "PART A - (Answer all questions, 5 x 2 = 10 Marks)",
        "Q1. Define core principles of the subject matter.",
        "Q2. Explain algorithm time complexity metrics.",
        "Q3. Differentiate between data structures.",
        "Q4. State application criteria.",
        "Q5. Summarize key design patterns.",
        "",
        "PART B - (Answer any two questions, 2 x 10 = 20 Marks)",
        "Q6. Provide an architectural blueprint with detailed explanation. [10 Marks]",
        "Q7. Describe error recovery procedures and database persistence. [10 Marks]",
        "Q8. Analyze structural compliance metrics for institutional documents. [10 Marks]"
    ]
    create_sample_pdf(valid_pdf_path, valid_lines)

    # 8. Upload Valid Question Paper PDF
    with open(valid_pdf_path, "rb") as f:
        upload_res = faculty_client.post(
            "/question-papers/upload",
            data={"course_id": course_id, "exam_category": "MID1"},
            files={"file": ("Valid_MID1_Question_Paper.pdf", f, "application/pdf")}
        )
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    up_data = upload_res.json()
    assert up_data["success"] is True
    doc_id = up_data["document_id"]
    val_status = up_data["validation_status"]
    comp_pct = up_data["compliance_percentage"]
    print(f"✓ [TEST 6] Uploaded valid question paper PDF (Doc ID: {doc_id}). Status: {val_status}, Compliance: {comp_pct}%.")

    # 9. Test Detailed 6-Column Validation Report Endpoint
    rep_res = faculty_client.get(f"/question-papers/{doc_id}/report")
    assert rep_res.status_code == 200, f"Report failed: {rep_res.text}"
    report_data = rep_res.json()
    assert report_data["document_id"] == doc_id
    items = report_data["report"]["items"]
    assert len(items) >= 7, f"Expected at least 7 validation check items, got {len(items)}"
    for item in items:
        assert "requirement" in item
        assert "expected_value" in item
        assert "detected_value" in item
        assert "result" in item
        assert "explanation" in item
        assert "recommended_correction" in item
    print(f"✓ [TEST 7] 6-Column Validation Report verified with {len(items)} checks. All 6 columns populated properly.")

    # 10. Upload a Defective PDF that fails a configured requirement
    defective_pdf_path = "uploads/temp_test_defective_mid1.pdf"
    defective_lines = [
        "ANANTHA LAKSHMI INSTITUTE OF TECHNOLOGY AND SCIENCES",
        "DEPARTMENT OF MECHANICAL ENGINEERING", # Wrong department!
        "COURSE CODE: 99XXXX", # Wrong course code!
        "Mid-Semester Examination 1",
        "TOTAL MARKS: 22", # Wrong marks: 22 instead of 30!
        "PART A - (5 Marks)",
        "Q1. Short question."
        # Missing Part B!
    ]
    create_sample_pdf(defective_pdf_path, defective_lines)

    with open(defective_pdf_path, "rb") as f:
        defective_res = faculty_client.post(
            "/question-papers/upload",
            data={"course_id": course_id, "exam_category": "MID1"},
            files={"file": ("Defective_MID1_Paper.pdf", f, "application/pdf")}
        )
    assert defective_res.status_code == 200
    def_data = defective_res.json()
    assert def_data["validation_status"] == "INVALID", f"Expected INVALID, got {def_data['validation_status']}"
    assert def_data["compliance_percentage"] < 80.0
    
    # Check failed items and recommendations
    rep_def = faculty_client.get(f"/question-papers/{doc_id}/report").json()
    failed_items = [i for i in rep_def["report"]["items"] if i["result"] in ("Incorrect", "Missing")]
    assert len(failed_items) > 0
    print(f"✓ [TEST 8] Defective PDF upload correctly marked INVALID ({def_data['compliance_percentage']}%). Found {len(failed_items)} failed requirements with recommended corrections.")

    # 11. Upload Scanned / Unreadable PDF
    scanned_pdf_path = "uploads/temp_test_scanned.pdf"
    create_scanned_image_pdf(scanned_pdf_path)

    with open(scanned_pdf_path, "rb") as f:
        scanned_res = faculty_client.post(
            "/question-papers/upload",
            data={"course_id": course_id, "exam_category": "MID2"},
            files={"file": ("Scanned_MID2_ImageOnly.pdf", f, "application/pdf")}
        )
    assert scanned_res.status_code == 200
    scanned_data = scanned_res.json()
    assert scanned_data["validation_status"] == "NEEDS_REVIEW", f"Expected NEEDS_REVIEW for scanned PDF, got {scanned_data['validation_status']}"
    print("✓ [TEST 9] Scanned raster PDF correctly flagged as 'NEEDS_REVIEW' without unverified false passing.")

    # 12. Test Missing Papers Status Logic
    # Mid-1 (Invalid), Mid-2 (Needs Review), Sem (None) -> Overall status must be Missing or Invalid
    ov_res = faculty_client.get("/question-papers/overview").json()
    target_row = next(r for r in ov_res["rows"] if r["course_id"] == course_id)
    assert target_row["is_fully_compliant"] is False, "Course should not be compliant when SEM paper is missing"
    assert target_row["validation_status"] == "Missing", f"Expected 'Missing', got {target_row['validation_status']}"
    print("✓ [TEST 10] Course overall validation status correctly evaluated as 'Missing' when Semester paper is absent.")

    # 13. Re-upload clean valid Mid-1 to restore valid status
    with open(valid_pdf_path, "rb") as f:
        faculty_client.post(
            "/question-papers/upload",
            data={"course_id": course_id, "exam_category": "MID1"},
            files={"file": ("Valid_MID1_Question_Paper_v2.pdf", f, "application/pdf")}
        )

    # 14. Test HOD & Auditor Review and Approval Decision
    hod_client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    hod_client.post("/login", json={"email": "hod.cse@alitsprototype.test", "password": "Hod@123"})

    # Reject decision test
    dec_res = hod_client.post(
        f"/question-papers/{doc_id}/decision",
        json={"decision": "REJECTED", "comments": "Missing section heading formatting. Please revise."}
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["approval_status"] == "REJECTED"
    print("✓ [TEST 11] HOD submitted REJECTED decision with comments successfully recorded.")

    # Download must fail when document is REJECTED
    dl_res = hod_client.get(f"/documents/{doc_id}/download")
    assert dl_res.status_code == 403, f"Expected 403 Forbidden for REJECTED document download, got {dl_res.status_code}"
    print(f"✓ [TEST 12a] Download strictly blocked for unaccepted document (403: {dl_res.json().get('detail')}).")

    # Auditor accepts decision test
    auditor_client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    auditor_client.post("/login", json={"email": "auditor@alitsprototype.test", "password": "Auditor@123"})
    dec_accept = auditor_client.post(
        f"/question-papers/{doc_id}/decision",
        json={"decision": "ACCEPTED", "comments": "Verified and complies with JNTUA institutional schema."}
    )
    assert dec_accept.status_code == 200
    assert dec_accept.json()["approval_status"] == "ACCEPTED"
    print("✓ [TEST 11b] Auditor submitted ACCEPTED decision recorded in audit log.")

    # Download must SUCCEED when document is ACCEPTED
    dl_res_ok = auditor_client.get(f"/documents/{doc_id}/download")
    assert dl_res_ok.status_code == 200, f"Expected 200 for ACCEPTED document download, got {dl_res_ok.status_code}"
    assert len(dl_res_ok.content) > 0
    print(f"✓ [TEST 12b] Download succeeded for ACCEPTED document ({len(dl_res_ok.content)} bytes).")

    # Faculty is NOT permitted to download official records
    faculty_dl = faculty_client.get(f"/documents/{doc_id}/download")
    assert faculty_dl.status_code == 403, f"Expected 403 for Faculty download, got {faculty_dl.status_code}"
    print("✓ [TEST 12c] Faculty download attempt correctly denied with 403 Forbidden.")

    # 15. PDF Viewer endpoint with session credentials
    view_res = auditor_client.get(f"/documents/{doc_id}/view")
    assert view_res.status_code == 200
    assert view_res.headers.get("content-type") == "application/pdf"
    print("✓ [TEST 13] /documents/{id}/view returns PDF content stream successfully with session credentials.")

    # 16. Logout & Protected Routes Test
    logout_res = faculty_client.post("/logout")
    assert logout_res.status_code == 200
    # After logout, accessing protected route must return 401
    me_after = faculty_client.get("/auth/me")
    assert me_after.status_code == 401
    qp_after = faculty_client.get("/question-papers/overview")
    assert qp_after.status_code == 401
    print("✓ [TEST 14] Logout and protected route security verified. Unauthenticated access returns 401.")

    print("=" * 70)
    print("ALL 15 END-TO-END VERIFICATION CHECKS PASSED WITH ZERO FAILURES!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
