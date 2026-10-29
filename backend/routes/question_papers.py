import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse

from backend.database import get_db_cursor
from backend.services.auth_service import get_current_user, require_roles, check_department_access
from backend.services.structural_analyzer import (
    validate_question_paper_document,
    compute_file_hash
)
from backend.models.schemas import QuestionPaperDecisionRequest

router = APIRouter(prefix="/question-papers", tags=["Question Paper Management"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/filters")
def get_management_filters(current_user: dict = Depends(get_current_user)):
    """Returns academic years, semesters, departments, and exam categories for filtering."""
    inst_id = current_user.get("institution_id", 6)
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, year_name, is_current FROM academic_years WHERE institution_id = %s ORDER BY id DESC", (inst_id,))
        academic_years = cursor.fetchall()

        cursor.execute("SELECT id, semester_name, semester_code, semester_number FROM semesters WHERE institution_id = %s ORDER BY semester_number", (inst_id,))
        semesters = cursor.fetchall()

        cursor.execute("SELECT id, code, name FROM departments WHERE institution_id = %s ORDER BY id", (inst_id,))
        departments = cursor.fetchall()

        cursor.execute("SELECT id, name, code, max_marks, is_mandatory FROM exam_categories WHERE institution_id = %s ORDER BY display_order", (inst_id,))
        exam_categories = cursor.fetchall()

    return {
        "academic_years": academic_years,
        "semesters": semesters,
        "departments": departments,
        "exam_categories": exam_categories
    }

@router.get("/overview")
def get_question_papers_overview(
    academic_year_id: Optional[int] = Query(None),
    semester_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the comprehensive 12-column Question Paper Management table:
    1. Academic Year
    2. Semester
    3. Department
    4. Course / Subject
    5. Faculty Name
    6. Mid-1 Question Paper
    7. Mid-2 Question Paper
    8. Semester / End-Semester Question Paper
    9. Uploaded Date
    10. Validation Status
    11. Approval Status
    12. Actions
    """
    inst_id = current_user.get("institution_id", 6)
    user_role = current_user["role"]
    user_dept_id = current_user.get("department_id")

    # Enforce department isolation for HOD
    if user_role == "HOD" and user_dept_id:
        department_id = user_dept_id

    query = """
        SELECT 
            c.id AS course_id,
            c.course_code,
            c.course_name,
            c.credits,
            dept.id AS department_id,
            dept.code AS department_code,
            dept.name AS department_name,
            sem.id AS semester_id,
            sem.semester_name,
            sem.semester_code,
            ay.id AS academic_year_id,
            ay.year_name AS academic_year,
            u.id AS faculty_id,
            COALESCE(u.name, 'Unassigned') AS faculty_name,
            u.email AS faculty_email
        FROM courses c
        JOIN departments dept ON dept.id = c.department_id
        LEFT JOIN semesters sem ON sem.id = c.semester_id
        LEFT JOIN academic_years ay ON ay.id = c.academic_year_id
        LEFT JOIN faculty_course_assignments fca ON fca.course_id = c.id
        LEFT JOIN users u ON u.id = fca.faculty_id
        WHERE c.institution_id = %s
    """
    params = [inst_id]

    if academic_year_id:
        query += " AND (c.academic_year_id = %s OR c.academic_year_id IS NULL)"
        params.append(academic_year_id)
    if semester_id:
        query += " AND c.semester_id = %s"
        params.append(semester_id)
    if department_id:
        query += " AND c.department_id = %s"
        params.append(department_id)
    # Allow viewing filtered department or all institutional courses
    pass

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query += " AND (LOWER(c.course_code) LIKE %s OR LOWER(c.course_name) LIKE %s OR LOWER(u.name) LIKE %s)"
        params.extend([term, term, term])

    query += " ORDER BY dept.code, sem.semester_number, c.course_code"

    with get_db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        courses = cursor.fetchall()

        # Fetch all uploaded question paper documents for these courses
        cursor.execute("""
            SELECT 
                d.id,
                d.course_id,
                d.exam_category,
                d.file_name,
                d.uploaded_at,
                d.uploaded_by,
                d.version,
                d.validation_status,
                d.approval_status,
                d.approval_comments,
                d.approved_at,
                d.analysis_result,
                u.name AS uploader_name
            FROM documents d
            LEFT JOIN users u ON u.id = d.uploaded_by
            WHERE d.institution_id = %s AND d.course_id IS NOT NULL
            ORDER BY d.id DESC
        """, (inst_id,))
        docs = cursor.fetchall()

    # Group documents by (course_id, exam_category)
    doc_map = {}
    for d in docs:
        cid = d["course_id"]
        cat = (d["exam_category"] or "").upper()
        if (cid, cat) not in doc_map:
            compliance_pct = 0.0
            if d.get("analysis_result") and isinstance(d["analysis_result"], dict):
                compliance_pct = d["analysis_result"].get("compliance_percentage", 0.0)

            doc_map[(cid, cat)] = {
                "id": d["id"],
                "file_name": d["file_name"],
                "uploaded_at": d["uploaded_at"].strftime("%Y-%m-%d %H:%M") if d.get("uploaded_at") else None,
                "version": d["version"],
                "validation_status": d["validation_status"] or "PENDING",
                "approval_status": d["approval_status"] or "PENDING",
                "approval_comments": d.get("approval_comments"),
                "compliance_percentage": compliance_pct,
                "uploader_name": d.get("uploader_name")
            }

    rows = []
    for c in courses:
        cid = c["course_id"]
        mid1 = doc_map.get((cid, "MID1"))
        mid2 = doc_map.get((cid, "MID2"))
        sem = doc_map.get((cid, "SEM"))

        # Determine overall validation status
        # If any mandatory is missing -> Missing
        # If any is Invalid -> Invalid
        # If any is Needs Review -> Needs Review
        # If all 3 are Valid -> Valid
        papers = [mid1, mid2, sem]
        existing_papers = [p for p in papers if p]

        if len(existing_papers) < 3:
            overall_val = "Missing"
        elif any(p["validation_status"] == "INVALID" for p in existing_papers):
            overall_val = "Invalid"
        elif any(p["validation_status"] == "NEEDS_REVIEW" for p in existing_papers):
            overall_val = "Needs Review"
        elif all(p["validation_status"] == "VALID" for p in existing_papers):
            overall_val = "Valid"
        else:
            overall_val = "Pending"

        # Determine overall approval status
        if len(existing_papers) < 3:
            overall_app = "Pending"
        elif any(p["approval_status"] == "REJECTED" for p in existing_papers):
            overall_app = "Rejected"
        elif any(p["approval_status"] == "NEEDS_REVIEW" for p in existing_papers):
            overall_app = "Needs Review"
        elif all(p["approval_status"] == "ACCEPTED" for p in existing_papers):
            overall_app = "Accepted"
        else:
            overall_app = "Pending"

        # Find latest upload date
        upload_dates = [p["uploaded_at"] for p in existing_papers if p.get("uploaded_at")]
        latest_date = max(upload_dates) if upload_dates else "-"

        # Determine permitted actions for current user role
        can_upload = user_role in ("Faculty", "Admin") and (c["faculty_id"] == current_user["id"] or user_role == "Admin" or c["faculty_id"] is None)
        can_review = user_role in ("HOD", "Auditor", "Admin")

        rows.append({
            "course_id": cid,
            "academic_year": c.get("academic_year") or "2025-2026",
            "academic_year_id": c.get("academic_year_id"),
            "semester": c.get("semester_name") or "Semester III",
            "semester_id": c.get("semester_id"),
            "department": c["department_code"],
            "department_id": c["department_id"],
            "department_name": c["department_name"],
            "course_code": c["course_code"],
            "course_name": c["course_name"],
            "faculty_name": c["faculty_name"],
            "faculty_id": c["faculty_id"],
            "mid1_paper": mid1,
            "mid2_paper": mid2,
            "sem_paper": sem,
            "uploaded_date": latest_date,
            "validation_status": overall_val,
            "approval_status": overall_app,
            "is_fully_compliant": overall_val == "Valid" and overall_app == "Accepted",
            "permissions": {
                "can_upload": can_upload,
                "can_review": can_review
            }
        })

    return {
        "total_courses": len(rows),
        "compliant_count": sum(1 for r in rows if r["is_fully_compliant"]),
        "rows": rows
    }

@router.post("/upload")
async def upload_question_paper(
    course_id: int = Form(...),
    exam_category: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Uploads a Question Paper PDF for a specific course and exam category (MID1, MID2, SEM).
    Validates file type (PDF only), computes SHA-256 hash, runs automated structural validation,
    archives previous version if replacing, and records validation results in database.
    """
    exam_cat = exam_category.strip().upper()
    if exam_cat not in ("MID1", "MID2", "SEM"):
        raise HTTPException(status_code=400, detail="Invalid exam category. Must be MID1, MID2, or SEM.")

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF documents (.pdf) are permitted.")

    # Fetch course details
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                c.id, c.institution_id, c.department_id, c.semester_id, c.academic_year_id,
                c.course_code, c.course_name,
                dept.code AS department_code, dept.name AS department_name,
                i.name AS institution_name
            FROM courses c
            JOIN departments dept ON dept.id = c.department_id
            JOIN institution i ON i.id = c.institution_id
            WHERE c.id = %s
        """, (course_id,))
        course = cursor.fetchone()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    # Check permission: Faculty assigned to course, HOD of dept, or Admin
    if current_user["role"] == "Faculty":
        check_department_access(current_user, course["department_id"])
    elif current_user["role"] == "HOD":
        check_department_access(current_user, course["department_id"])

    # Read file content safely
    content = await file.read()
    file_size = len(content)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")
    if file_size > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum permitted limit of 25MB.")

    # Generate safe unique path on disk
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / unique_name
    file_path.write_bytes(content)

    # Compute SHA-256 hash
    file_hash = compute_file_hash(str(file_path))

    # Run automated validation report against institutional standards
    validation_meta = {
        "file_name": file.filename,
        "institution_name": course["institution_name"],
        "department_code": course["department_code"],
        "department_name": course["department_name"],
        "course_code": course["course_code"],
        "course_name": course["course_name"],
        "exam_category": exam_cat,
        "max_marks": 30 if exam_cat in ("MID1", "MID2") else 70
    }

    report = validate_question_paper_document(str(file_path), validation_meta)

    with get_db_cursor(commit=True) as cursor:
        # Check if a question paper already exists for this (course_id, exam_category)
        cursor.execute("""
            SELECT id, version, file_name, file_path, file_hash, file_size, validation_status, analysis_result, approval_status, approval_comments
            FROM documents
            WHERE course_id = %s AND exam_category = %s
            ORDER BY id DESC LIMIT 1
        """, (course_id, exam_cat))
        existing_doc = cursor.fetchone()

        if existing_doc:
            doc_id = existing_doc["id"]
            current_ver = existing_doc["version"] or 1
            next_ver = current_ver + 1

            # Archive existing record in document_versions table (audit retention)
            cursor.execute("""
                INSERT INTO document_versions 
                    (document_id, version, file_name, file_path, file_hash, file_size, uploaded_by, validation_status, validation_result, approval_status, approval_comments, change_summary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                doc_id,
                current_ver,
                existing_doc["file_name"],
                existing_doc["file_path"],
                existing_doc.get("file_hash"),
                existing_doc.get("file_size", 0),
                current_user["id"],
                existing_doc["validation_status"],
                json.dumps(existing_doc["analysis_result"]) if existing_doc.get("analysis_result") else None,
                existing_doc["approval_status"],
                existing_doc.get("approval_comments"),
                f"Replaced with Version {next_ver} by {current_user['name']}"
            ))

            # Update document to new version
            cursor.execute("""
                UPDATE documents
                SET file_name = %s,
                    file_path = %s,
                    file_hash = %s,
                    file_size = %s,
                    uploaded_by = %s,
                    uploaded_at = CURRENT_TIMESTAMP,
                    version = %s,
                    validation_status = %s,
                    analysis_status = %s,
                    analysis_result = %s,
                    analyzed_at = CURRENT_TIMESTAMP,
                    approval_status = 'PENDING',
                    approval_comments = NULL,
                    approved_by = NULL,
                    approved_at = NULL
                WHERE id = %s
                RETURNING id
            """, (
                file.filename,
                str(file_path),
                file_hash,
                file_size,
                current_user["id"],
                next_ver,
                report["validation_status"],
                report["validation_status"],
                json.dumps(report),
                doc_id
            ))
        else:
            # Insert new document record
            cursor.execute("""
                INSERT INTO documents (
                    institution_id, department_id, course_id, academic_year_id, semester_id,
                    exam_category, uploaded_by, file_name, file_path, file_hash, file_size,
                    validation_status, analysis_status, analysis_result, analyzed_at,
                    approval_status, version
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, CURRENT_TIMESTAMP,
                    'PENDING', 1
                ) RETURNING id
            """, (
                course["institution_id"],
                course["department_id"],
                course_id,
                course["academic_year_id"],
                course["semester_id"],
                exam_cat,
                current_user["id"],
                file.filename,
                str(file_path),
                file_hash,
                file_size,
                report["validation_status"],
                report["validation_status"],
                json.dumps(report)
            ))
            doc_id = cursor.fetchone()["id"]

    return {
        "success": True,
        "message": f"Successfully uploaded and analyzed {file.filename}.",
        "document_id": doc_id,
        "exam_category": exam_cat,
        "validation_status": report["validation_status"],
        "compliance_percentage": report["compliance_percentage"],
        "validation_report": report
    }

@router.get("/{document_id}/report")
def get_document_validation_report(document_id: int, current_user: dict = Depends(get_current_user)):
    """Returns the detailed 6-column validation report and audit history for a document."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                d.id, d.file_name, d.exam_category, d.version, d.validation_status, d.approval_status,
                d.approval_comments, d.approved_at, d.analysis_result, d.uploaded_at,
                c.course_code, c.course_name,
                u.name AS uploader_name,
                app_u.name AS approver_name
            FROM documents d
            LEFT JOIN courses c ON c.id = d.course_id
            LEFT JOIN users u ON u.id = d.uploaded_by
            LEFT JOIN users app_u ON app_u.id = d.approved_by
            WHERE d.id = %s
        """, (document_id,))
        doc = cursor.fetchone()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    res = doc.get("analysis_result")
    if isinstance(res, str):
        res = json.loads(res)
    elif not res:
        res = {
            "validation_status": doc["validation_status"] or "PENDING",
            "compliance_percentage": 0.0,
            "summary": {
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "missing_requirements": 0,
                "needs_review": 0,
                "compliance_percentage": 0.0,
                "validation_status": doc["validation_status"] or "PENDING"
            },
            "items": []
        }

    return {
        "document_id": doc["id"],
        "file_name": doc["file_name"],
        "course_code": doc.get("course_code"),
        "course_name": doc.get("course_name"),
        "exam_category": doc.get("exam_category"),
        "version": doc.get("version", 1),
        "validation_status": doc["validation_status"],
        "approval_status": doc["approval_status"],
        "approval_comments": doc.get("approval_comments"),
        "approver_name": doc.get("approver_name"),
        "approved_at": doc["approved_at"].strftime("%Y-%m-%d %H:%M") if doc.get("approved_at") else None,
        "uploaded_at": doc["uploaded_at"].strftime("%Y-%m-%d %H:%M") if doc.get("uploaded_at") else None,
        "uploader_name": doc.get("uploader_name"),
        "report": res
    }

@router.post("/{document_id}/decision")
def submit_document_decision(
    document_id: int,
    data: QuestionPaperDecisionRequest,
    current_user: dict = Depends(require_roles("HOD", "Auditor", "Admin"))
):
    """
    Allows HOD, Auditor, or Admin to submit an approval decision:
    'ACCEPTED', 'REJECTED', or 'NEEDS_REVIEW' with review comments.
    """
    decision = data.decision.strip().upper()
    if decision not in ("ACCEPTED", "REJECTED", "NEEDS_REVIEW"):
        raise HTTPException(status_code=400, detail="Invalid decision. Must be ACCEPTED, REJECTED, or NEEDS_REVIEW.")

    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, department_id, file_name, approval_status FROM documents WHERE id = %s", (document_id,))
        doc = cursor.fetchone()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if current_user["role"] == "HOD":
        check_department_access(current_user, doc["department_id"])

    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE documents
            SET approval_status = %s,
                approved_by = %s,
                approval_comments = %s,
                approved_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, approval_status
        """, (decision, current_user["id"], data.comments or "", document_id))

        # Record in audit_findings table
        cursor.execute("""
            INSERT INTO audit_findings (document_id, user_id, finding_type, severity, description, recommendation, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            document_id,
            current_user["id"],
            "FORMAL_AUDIT_DECISION",
            "INFO" if decision == "ACCEPTED" else "HIGH",
            f"Document marked {decision} by {current_user['role']} {current_user['name']}. Comments: {data.comments or 'None provided.'}",
            "Proceed with official archiving." if decision == "ACCEPTED" else "Faculty must upload a corrected revision.",
            decision
        ))

    return {
        "success": True,
        "document_id": document_id,
        "approval_status": decision,
        "message": f"Document status updated to {decision} successfully."
    }
