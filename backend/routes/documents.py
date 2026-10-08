import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from backend.services.auth_service import get_current_user, check_department_access
from backend.database import get_db_cursor

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("")
def list_documents(current_user: dict = Depends(get_current_user)):
    role = current_user["role"]
    inst_id = current_user["institution_id"]

    query = """
        SELECT 
            d.id,
            d.file_name,
            d.uploaded_at,
            d.analysis_status,
            d.analyzed_at,
            dt.name AS document_type_name,
            dept.name AS department_name,
            dept.code AS department_code,
            u.name AS uploaded_by_name,
            u.email AS uploaded_by_email
        FROM documents d
        LEFT JOIN document_types dt ON dt.id = d.document_type_id
        LEFT JOIN departments dept ON dept.id = d.department_id
        LEFT JOIN users u ON u.id = d.uploaded_by
        WHERE d.institution_id = %s
    """
    params = [inst_id]

    if role == "HOD":
        query += " AND d.department_id = %s"
        params.append(current_user["department_id"])
    elif role == "Faculty":
        query += " AND d.uploaded_by = %s"
        params.append(current_user["id"])

    query += " ORDER BY d.uploaded_at DESC"

    with get_db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        return cursor.fetchall()

@router.get("/by-department/code/{code}")
def get_documents_by_dept_code(code: str, current_user: dict = Depends(get_current_user)):
    inst_id = current_user["institution_id"]
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, code, name FROM departments WHERE UPPER(code) = UPPER(%s) AND institution_id = %s", (code.strip(), inst_id))
        dept = cursor.fetchone()
        if not dept:
            raise HTTPException(status_code=404, detail=f"Department code '{code}' not found.")

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
                dept.code AS department_code,
                u.name AS uploaded_by_name,
                u.email AS uploaded_by_email
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN departments dept ON dept.id = d.department_id
            LEFT JOIN users u ON u.id = d.uploaded_by
            WHERE d.department_id = %s AND d.institution_id = %s
            ORDER BY d.uploaded_at DESC
            """,
            (dept["id"], inst_id)
        )
        docs = cursor.fetchall()

        return {
            "department": dept,
            "documents": docs
        }

@router.get("/by-department/{department_id}")
def get_documents_by_dept_id(department_id: int, current_user: dict = Depends(get_current_user)):
    inst_id = current_user["institution_id"]
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, code, name FROM departments WHERE id = %s AND institution_id = %s", (department_id, inst_id))
        dept = cursor.fetchone()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found.")

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
                dept.code AS department_code,
                u.name AS uploaded_by_name,
                u.email AS uploaded_by_email
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN departments dept ON dept.id = d.department_id
            LEFT JOIN users u ON u.id = d.uploaded_by
            WHERE d.department_id = %s AND d.institution_id = %s
            ORDER BY d.uploaded_at DESC
            """,
            (department_id, inst_id)
        )
        docs = cursor.fetchall()

        return {
            "department": dept,
            "documents": docs
        }

@router.get("/{document_id}")
def get_document_details(document_id: int, current_user: dict = Depends(get_current_user)):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                d.*,
                dt.name AS document_type_name,
                dept.name AS department_name,
                u.name AS uploaded_by_name
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN departments dept ON dept.id = d.department_id
            LEFT JOIN users u ON u.id = d.uploaded_by
            WHERE d.id = %s
            """,
            (document_id,)
        )
        doc = cursor.fetchone()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if current_user["role"] == "Faculty" and doc["uploaded_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot access this document.")
    elif current_user["role"] == "HOD":
        check_department_access(current_user, doc["department_id"])

    return doc

@router.get("/{document_id}/comparison")
def get_document_comparison(document_id: int, current_user: dict = Depends(get_current_user)):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                d.id,
                d.file_name,
                d.department_id,
                d.uploaded_by,
                d.analysis_status,
                d.analysis_result,
                d.analyzed_at,
                dt.name AS document_type_name
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            WHERE d.id = %s
            """,
            (document_id,)
        )
        doc = cursor.fetchone()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Permissions
    if current_user["role"] == "Faculty" and doc["uploaded_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    elif current_user["role"] == "HOD":
        check_department_access(current_user, doc["department_id"])

    if not doc["analysis_result"]:
        raise HTTPException(status_code=404, detail="Document has not been analyzed yet.")

    comparison = doc["analysis_result"]
    if isinstance(comparison, str):
        comparison = json.loads(comparison)

    return {
        "document_id": doc["id"],
        "file_name": doc["file_name"],
        "document_type": doc.get("document_type_name"),
        "final_result": doc["analysis_status"],
        "comparison": comparison,
        "analyzed_at": doc["analyzed_at"]
    }

@router.get("/{document_id}/view")
def view_document_pdf(document_id: int, current_user: dict = Depends(get_current_user)):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
        doc = cursor.fetchone()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Authorization check
    if current_user["role"] == "Faculty" and doc["uploaded_by"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden.")
    elif current_user["role"] == "HOD":
        check_department_access(current_user, doc["department_id"])

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file was not found on the server.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{doc["file_name"]}"'}
    )

@router.get("/{document_id}/download")
def download_accepted_pdf(document_id: int, current_user: dict = Depends(get_current_user)):
    # Admin, Auditor, and HOD can download accepted documents
    if current_user["role"] not in {"Auditor", "HOD", "Admin"}:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only Admin, Auditor and HOD have download authorization for accepted documents."
        )

    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
        doc = cursor.fetchone()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if current_user["role"] == "HOD":
        check_department_access(current_user, doc["department_id"])

    # Strict check: only ACCEPTED documents can be downloaded
    if doc["analysis_status"] != "ACCEPTED":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only accepted documents can be downloaded as official institutional records."
        )

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file was not found on the server.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=doc["file_name"]
    )
