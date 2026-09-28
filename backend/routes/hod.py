from fastapi import APIRouter, Depends, HTTPException
from backend.services.auth_service import require_roles, check_department_access
from backend.database import get_db_cursor

router = APIRouter(prefix="", tags=["HOD"])

@router.get("/hod/documents")
def get_hod_documents(current_user: dict = Depends(require_roles("HOD"))):
    dept_id = current_user.get("department_id")
    if not dept_id:
        raise HTTPException(status_code=403, detail="HOD is not assigned to a department.")

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
                dept.code AS department_code,
                u.name AS uploaded_by_name,
                u.email AS uploaded_by_email
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN departments dept ON dept.id = d.department_id
            LEFT JOIN users u ON u.id = d.uploaded_by
            WHERE d.department_id = %s
            ORDER BY d.uploaded_at DESC
            """,
            (dept_id,)
        )
        return cursor.fetchall()

@router.get("/hod/accepted-documents")
def get_hod_accepted_documents(current_user: dict = Depends(require_roles("HOD"))):
    dept_id = current_user.get("department_id")
    if not dept_id:
        raise HTTPException(status_code=403, detail="HOD is not assigned to a department.")

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
                dept.code AS department_code,
                u.name AS uploaded_by_name
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN departments dept ON dept.id = d.department_id
            LEFT JOIN users u ON u.id = d.uploaded_by
            WHERE d.department_id = %s
              AND d.analysis_status = 'ACCEPTED'
            ORDER BY d.analyzed_at DESC NULLS LAST
            """,
            (dept_id,)
        )
        return cursor.fetchall()

@router.get("/hod/documents/{document_id}")
def get_hod_document(document_id: int, current_user: dict = Depends(require_roles("HOD"))):
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

        check_department_access(current_user, doc["department_id"])
        return doc
