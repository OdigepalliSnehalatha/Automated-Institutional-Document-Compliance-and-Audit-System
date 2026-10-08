from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from backend.services.auth_service import require_roles, get_current_user
from backend.database import get_db_cursor

router = APIRouter(prefix="/admin", tags=["Admin"])

class InstitutionUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None

@router.get("/dashboard")
def get_admin_dashboard(current_user: dict = Depends(require_roles("Admin"))):
    inst_id = current_user["institution_id"]

    with get_db_cursor() as cursor:
        # Institution record
        cursor.execute("SELECT id, name, email, logo_url, created_at FROM institution WHERE id = %s", (inst_id,))
        inst = cursor.fetchone() or {}

        # Overview Counts
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE role = 'Faculty') AS total_faculty,
                COUNT(*) FILTER (WHERE role = 'HOD') AS total_hod,
                COUNT(*) FILTER (WHERE role = 'Auditor') AS total_auditors,
                COUNT(*) FILTER (WHERE role = 'Admin') AS total_admins
            FROM users
            WHERE institution_id = %s
            """,
            (inst_id,)
        )
        user_counts = cursor.fetchone() or {}

        cursor.execute(
            """
            SELECT 
                COUNT(*) AS total_documents,
                COUNT(*) FILTER (WHERE analysis_status = 'ACCEPTED') AS accepted_documents,
                COUNT(*) FILTER (WHERE analysis_status = 'REJECTED') AS rejected_documents,
                COUNT(*) FILTER (WHERE analysis_status = 'PENDING' OR analysis_status IS NULL) AS pending_documents
            FROM documents
            WHERE institution_id = %s
            """,
            (inst_id,)
        )
        doc_counts = cursor.fetchone() or {}

        cursor.execute("SELECT COUNT(*) AS total_departments FROM departments WHERE institution_id = %s", (inst_id,))
        dept_count = cursor.fetchone()["total_departments"]

        cursor.execute("SELECT COUNT(*) AS total_formats FROM document_formats WHERE institution_id = %s", (inst_id,))
        format_count = cursor.fetchone()["total_formats"]

        # Department Breakdown
        cursor.execute(
            """
            SELECT 
                d.id,
                d.code,
                d.name,
                COUNT(DISTINCT doc.id) AS document_count,
                COUNT(DISTINCT CASE WHEN doc.analysis_status = 'ACCEPTED' THEN doc.id END) AS accepted_count,
                COUNT(DISTINCT u.id) FILTER (WHERE u.role = 'Faculty') AS faculty_count
            FROM departments d
            LEFT JOIN documents doc ON doc.department_id = d.id
            LEFT JOIN users u ON u.department_id = d.id
            WHERE d.institution_id = %s
            GROUP BY d.id, d.code, d.name
            ORDER BY d.id
            """,
            (inst_id,)
        )
        departments = cursor.fetchall()

        # Recent Submissions across all departments
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
                u.role AS uploaded_by_role
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN departments dept ON dept.id = d.department_id
            LEFT JOIN users u ON u.id = d.uploaded_by
            WHERE d.institution_id = %s
            ORDER BY d.uploaded_at DESC
            LIMIT 10
            """,
            (inst_id,)
        )
        recent_submissions = cursor.fetchall()

    total_docs = doc_counts.get("total_documents", 0) or 0
    accepted_docs = doc_counts.get("accepted_documents", 0) or 0
    compliance_rate = round((accepted_docs / total_docs * 100), 1) if total_docs > 0 else 0.0

    return {
        "institution": inst,
        "metrics": {
            "total_faculty": user_counts.get("total_faculty", 0),
            "total_hod": user_counts.get("total_hod", 0),
            "total_auditors": user_counts.get("total_auditors", 0),
            "total_admins": user_counts.get("total_admins", 0),
            "total_departments": dept_count,
            "total_formats": format_count,
            "total_documents": total_docs,
            "accepted_documents": accepted_docs,
            "rejected_documents": doc_counts.get("rejected_documents", 0) or 0,
            "pending_documents": doc_counts.get("pending_documents", 0) or 0,
            "compliance_rate": compliance_rate
        },
        "departments": departments,
        "recent_submissions": recent_submissions
    }

@router.get("/users")
def get_admin_users(
    role: Optional[str] = None,
    current_user: dict = Depends(require_roles("Admin"))
):
    inst_id = current_user["institution_id"]
    query = """
        SELECT 
            u.id,
            u.name,
            u.email,
            u.role,
            u.department_id,
            d.code AS department_code,
            d.name AS department_name,
            u.created_at
        FROM users u
        LEFT JOIN departments d ON d.id = u.department_id
        WHERE u.institution_id = %s
    """
    params = [inst_id]
    if role:
        query += " AND u.role = %s"
        params.append(role)
    query += " ORDER BY u.role, u.name"

    with get_db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        return cursor.fetchall()

@router.put("/institution")
def update_institution_settings(
    data: InstitutionUpdateRequest,
    current_user: dict = Depends(require_roles("Admin"))
):
    inst_id = current_user["institution_id"]
    updates = []
    params = []

    if data.name is not None and data.name.strip():
        updates.append("name = %s")
        params.append(data.name.strip())
    if data.email is not None and data.email.strip():
        updates.append("email = %s")
        params.append(data.email.strip())
    if data.logo_url is not None:
        updates.append("logo_url = %s")
        params.append(data.logo_url.strip())

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    params.append(inst_id)
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            f"UPDATE institution SET {', '.join(updates)} WHERE id = %s RETURNING id, name, email, logo_url",
            tuple(params)
        )
        updated = cursor.fetchone()

    return {
        "message": "Institution profile updated successfully.",
        "institution": updated
    }
