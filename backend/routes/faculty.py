import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from backend.services.auth_service import require_roles, get_current_user, check_department_access
from backend.services.structural_analyzer import analyze_document_structure
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

    # 5. Insert record into database
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO documents 
                (institution_id, department_id, document_type_id, uploaded_by, file_name, file_path, uploaded_at, analysis_status)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'PENDING')
            RETURNING id, file_name, uploaded_at, analysis_status, department_id, document_type_id
            """,
            (
                current_user["institution_id"],
                target_dept_id,
                document_type_id,
                current_user["id"],
                file.filename,
                str(destination)
            )
        )
        new_doc = cursor.fetchone()

    return {
        "message": "Document uploaded successfully.",
        "document": new_doc
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
    # Fetch document
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT d.*, dt.name AS document_type_name
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            WHERE d.id = %s
            """,
            (document_id,)
        )
        document = cursor.fetchone()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Permissions:
    # Faculty can analyze their own; Auditor can analyze any in institution; HOD can analyze their department
    if current_user["role"] in ("Faculty", "Student") and document["uploaded_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only analyze documents uploaded by you.")
    elif current_user["role"] == "HOD":
        check_department_access(current_user, document["department_id"])

    file_path = document["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Underlying PDF file was not found on the server.")

    # Find matching structural format
    # Match order:
    # 1. Exact match for institution, department, and document_type
    # 2. Match for institution and document_type (institution-wide format, department_id IS NULL)
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, format_name, instructions
            FROM document_formats
            WHERE institution_id = %s 
              AND document_type_id = %s
              AND (department_id = %s OR department_id IS NULL)
            ORDER BY department_id NULLS LAST, created_at DESC
            LIMIT 1
            """,
            (document["institution_id"], document["document_type_id"], document["department_id"])
        )
        format_record = cursor.fetchone()

        if not format_record:
            raise HTTPException(
                status_code=400,
                detail=f"No structural format has been defined for document type '{document['document_type_name']}' by the Auditor. Please contact the Auditor."
            )

        cursor.execute(
            """
            SELECT id, requirement_name, requirement_type, requirement_value, is_required, display_order
            FROM format_requirements
            WHERE format_id = %s
            ORDER BY display_order ASC, id ASC
            """,
            (format_record["id"],)
        )
        requirements = cursor.fetchall()

    if not requirements:
        raise HTTPException(
            status_code=400,
            detail="The structural format has no defined requirements. The Auditor must configure requirements first."
        )

    # Execute pure structural analysis
    analysis_result = analyze_document_structure(file_path, format_record, requirements)
    final_status = analysis_result["status"]

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
