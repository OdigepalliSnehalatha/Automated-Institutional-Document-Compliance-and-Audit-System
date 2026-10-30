import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from backend.services.auth_service import require_roles, get_current_user, check_department_access
from backend.services.structural_analyzer import (
    validate_any_document,
    perform_cross_document_validation
)
from backend.routes.documents import execute_safe_document_deletion
from backend.database import get_db_cursor

router = APIRouter(tags=["Faculty"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type_id: int = Form(...),
    department_id: int | None = Form(None),
    course_id: int | None = Form(None),
    current_user: dict = Depends(require_roles("Faculty", "HOD", "Auditor", "Admin", "Student"))
):
    # 1. Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # 2. Determine department
    user_dept_id = current_user.get("department_id")
    target_dept_id = department_id or user_dept_id

    if not target_dept_id:
        raise HTTPException(status_code=400, detail="Department is required.")

    check_department_access(current_user, target_dept_id)

    # 3. Read content and validate size
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds maximum allowed size (25MB).")

    # 4. Generate safe unique filename and preserve original PDF
    safe_name = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.pdf"
    destination = UPLOAD_DIR / safe_name
    destination.write_bytes(content)

    # Fetch document type details
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, name FROM document_types WHERE id = %s", (document_type_id,))
        doc_type_row = cursor.fetchone()
        doc_type_name = doc_type_row["name"] if doc_type_row else "Document"

        # Fetch department code/name
        cursor.execute("SELECT id, name, code FROM departments WHERE id = %s", (target_dept_id,))
        dept_row = cursor.fetchone()

        # Fetch course info if course_id provided
        course_row = None
        if course_id:
            cursor.execute("SELECT id, name, code FROM courses WHERE id = %s", (course_id,))
            course_row = cursor.fetchone()

    # Automatic PDF Document Validation
    metadata = {
        "institution_name": "Anantha Lakshmi Institute of Technology & Sciences",
        "file_name": file.filename,
        "document_type_name": doc_type_name,
        "department_code": dept_row["code"] if dept_row else None,
        "department_name": dept_row["name"] if dept_row else None,
        "course_code": course_row["code"] if course_row else None,
        "course_name": course_row["name"] if course_row else None
    }

    report = validate_any_document(str(destination), doc_type_name, metadata)
    initial_status = report.get("validation_status", "REJECTED")

    # Adapt report to provide backward-compatible 'requirements' array for matrix views
    items = report.get("items", [])
    report["requirements"] = [
        {
            "name": it.get("requirement"),
            "status": "PASS" if it.get("result") == "Correct" else "FAIL",
            "reason": it.get("explanation"),
            "type": it.get("expected_value"),
            "detected": it.get("detected_value"),
            "correction": it.get("recommended_correction")
        }
        for it in items
    ]

    # 5. Insert record into database with immediate automated validation results
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO documents 
                (institution_id, department_id, document_type_id, uploaded_by, file_name, file_path, uploaded_at, 
                 analysis_status, analysis_result, analyzed_at, course_id)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, CURRENT_TIMESTAMP, %s)
            RETURNING id, file_name, uploaded_at, analysis_status, department_id, document_type_id
            """,
            (
                current_user["institution_id"],
                target_dept_id,
                document_type_id,
                current_user["id"],
                file.filename,
                str(destination),
                initial_status,
                json.dumps(report),
                course_id
            )
        )
        new_doc = cursor.fetchone()

    return {
        "message": f"Document uploaded and automatically validated: {initial_status}",
        "document": new_doc,
        "analysis_result": report
    }

@router.get("/faculty/documents")
def get_faculty_documents(current_user: dict = Depends(require_roles("Faculty", "HOD", "Auditor", "Admin", "Student"))):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                d.id,
                d.file_name,
                d.uploaded_at,
                d.analysis_status,
                d.analyzed_at,
                dt.name AS document_type_name,
                dept.name AS department_name,
                dept.code AS department_code
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN departments dept ON dept.id = d.department_id
            WHERE d.uploaded_by = %s
            ORDER BY d.uploaded_at DESC
            """,
            (current_user["id"],)
        )
        return cursor.fetchall()

@router.get("/faculty/documents/{document_id}")
def get_faculty_document(document_id: int, current_user: dict = Depends(require_roles("Faculty", "Student"))):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                d.*,
                dt.name AS document_type_name,
                dept.name AS department_name
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN departments dept ON dept.id = d.department_id
            WHERE d.id = %s AND d.uploaded_by = %s
            """,
            (document_id, current_user["id"])
        )
        doc = cursor.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        return doc

@router.post("/documents/{document_id}/analyze")
def analyze_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT d.*, dt.name AS document_type_name, dept.name AS department_name, dept.code AS department_code,
                   c.name AS course_name, c.code AS course_code, inst.name AS institution_name
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN departments dept ON dept.id = d.department_id
            LEFT JOIN courses c ON c.id = d.course_id
            LEFT JOIN institution inst ON inst.id = d.institution_id
            WHERE d.id = %s
            """,
            (document_id,)
        )
        document = cursor.fetchone()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    if current_user["role"] in ("Faculty", "Student") and document["uploaded_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only analyze documents uploaded by you.")
    elif current_user["role"] == "HOD":
        check_department_access(current_user, document["department_id"])

    file_path = document["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Underlying PDF file was not found on the server.")

    metadata = {
        "institution_name": document.get("institution_name") or "Anantha Lakshmi Institute of Technology & Sciences",
        "file_name": document["file_name"],
        "document_type_name": document.get("document_type_name") or "Document",
        "department_code": document.get("department_code"),
        "department_name": document.get("department_name"),
        "course_code": document.get("course_code"),
        "course_name": document.get("course_name")
    }

    # Execute comprehensive structural analysis according to standard institutional requirements
    analysis_result = validate_any_document(file_path, document.get("document_type_name"), metadata)
    final_status = analysis_result["validation_status"]

    # Provide backward-compatible 'requirements' array for matrix views
    items = analysis_result.get("items", [])
    analysis_result["requirements"] = [
        {
            "name": it.get("requirement"),
            "status": "PASS" if it.get("result") == "Correct" else "FAIL",
            "reason": it.get("explanation"),
            "type": it.get("expected_value"),
            "detected": it.get("detected_value"),
            "correction": it.get("recommended_correction")
        }
        for it in items
    ]

    # Save analysis results back to database
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE documents
            SET analysis_status = %s,
                analysis_result = %s,
                analyzed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, analysis_status, analyzed_at
            """,
            (final_status, json.dumps(analysis_result), document_id)
        )
        updated = cursor.fetchone()

    return {
        "message": f"Structural analysis completed: {final_status}",
        "document_id": document_id,
        "status": final_status,
        "result": analysis_result
    }

@router.delete("/documents/{document_id}")
def delete_document_faculty(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Safely deletes an uploaded document, associated audit records, and physical file."""
    # Check permissions
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, uploaded_by, file_name FROM documents WHERE id = %s", (document_id,))
        doc = cursor.fetchone()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or already deleted.")

    if current_user["role"] in ("Faculty", "Student") and doc["uploaded_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this document.")

    return execute_safe_document_deletion(document_id)

@router.get("/courses/{course_id}/cross-document-validation")
def get_cross_document_validation(
    course_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Compares Course Structure, Question Papers, and Question Bank for cross-document consistency."""
    return perform_cross_document_validation(course_id)
