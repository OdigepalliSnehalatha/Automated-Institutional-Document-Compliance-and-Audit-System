from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from backend.services.auth_service import require_roles, get_current_user, ALLOWED_ROLES
from backend.database import get_db_cursor
from backend.models.schemas import (
    UserCreateRequest,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest
)

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
            u.is_active,
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

@router.post("/users")
def create_admin_user(
    data: UserCreateRequest,
    current_user: dict = Depends(require_roles("Admin"))
):
    inst_id = current_user["institution_id"]
    email = data.email.strip().lower()
    name = data.name.strip()
    role = data.role.strip()

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid official email address is required.")
    if not name:
        raise HTTPException(status_code=400, detail="User full name is required.")
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(ALLOWED_ROLES)}")

    dept_id = data.department_id
    if role in {"Faculty", "HOD"} and not dept_id:
        raise HTTPException(status_code=400, detail=f"Department assignment is required for role '{role}'.")

    with get_db_cursor(commit=True) as cursor:
        # Check if email is already registered in this institution
        cursor.execute(
            "SELECT id, role FROM users WHERE LOWER(email) = %s AND institution_id = %s",
            (email, inst_id)
        )
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"User with email '{email}' is already registered as '{existing['role']}' in this institution."
            )

        # If department specified, verify it exists in this institution
        if dept_id:
            cursor.execute(
                "SELECT id FROM departments WHERE id = %s AND institution_id = %s",
                (dept_id, inst_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Invalid department ID for this institution.")

        cursor.execute(
            """
            INSERT INTO users (institution_id, department_id, name, email, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, email, role, department_id, is_active, created_at
            """,
            (inst_id, dept_id, name, email, role, data.is_active)
        )
        new_user = cursor.fetchone()

    return {
        "message": f"User {name} ({role}) created successfully.",
        "user": new_user
    }

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    data: UserRoleUpdateRequest,
    current_user: dict = Depends(require_roles("Admin"))
):
    inst_id = current_user["institution_id"]
    new_role = data.role.strip()

    if new_role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(ALLOWED_ROLES)}")

    dept_id = data.department_id
    if new_role in {"Faculty", "HOD"} and not dept_id:
        raise HTTPException(status_code=400, detail=f"Department assignment is required for role '{new_role}'.")

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT id, name, email, role, is_active FROM users WHERE id = %s AND institution_id = %s",
            (user_id, inst_id)
        )
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="User record not found in this institution.")

        # Guard against demoting the sole active Admin
        if target["role"] == "Admin" and new_role != "Admin":
            cursor.execute(
                "SELECT COUNT(*) AS active_admins FROM users WHERE role = 'Admin' AND institution_id = %s AND is_active = TRUE",
                (inst_id,)
            )
            count = cursor.fetchone()["active_admins"]
            if count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot change the role of the sole active Administrator in the institution."
                )

        if dept_id:
            cursor.execute(
                "SELECT id FROM departments WHERE id = %s AND institution_id = %s",
                (dept_id, inst_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Invalid department ID for this institution.")

        cursor.execute(
            """
            UPDATE users
            SET role = %s, department_id = %s
            WHERE id = %s
            RETURNING id, name, email, role, department_id, is_active
            """,
            (new_role, dept_id if new_role in {"Faculty", "HOD"} else None, user_id)
        )
        updated_user = cursor.fetchone()

    return {
        "message": f"Role updated to '{new_role}' for user {target['name']}.",
        "user": updated_user
    }

@router.put("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    data: UserStatusUpdateRequest,
    current_user: dict = Depends(require_roles("Admin"))
):
    inst_id = current_user["institution_id"]

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT id, name, email, role, is_active FROM users WHERE id = %s AND institution_id = %s",
            (user_id, inst_id)
        )
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="User record not found.")

        # Guard against deactivating the sole active Admin or current admin
        if not data.is_active and target["role"] == "Admin":
            cursor.execute(
                "SELECT COUNT(*) AS active_admins FROM users WHERE role = 'Admin' AND institution_id = %s AND is_active = TRUE",
                (inst_id,)
            )
            count = cursor.fetchone()["active_admins"]
            if count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot deactivate the sole active Administrator in the institution."
                )

        cursor.execute(
            "UPDATE users SET is_active = %s WHERE id = %s RETURNING id, name, email, role, is_active",
            (data.is_active, user_id)
        )
        updated = cursor.fetchone()

    status_str = "activated" if data.is_active else "deactivated"
    return {
        "message": f"User {target['name']} has been {status_str}.",
        "user": updated
    }

@router.delete("/users/{user_id}")
def delete_admin_user(
    user_id: int,
    current_user: dict = Depends(require_roles("Admin"))
):
    inst_id = current_user["institution_id"]
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own Administrator account.")

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT id, name, role FROM users WHERE id = %s AND institution_id = %s",
            (user_id, inst_id)
        )
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="User record not found.")

        # Check if user has uploaded documents
        cursor.execute("SELECT COUNT(*) AS doc_count FROM documents WHERE uploaded_by = %s", (user_id,))
        doc_count = cursor.fetchone()["doc_count"]

        if doc_count > 0:
            # Soft-deactivate to preserve audit trail integrity
            cursor.execute("UPDATE users SET is_active = FALSE WHERE id = %s", (user_id,))
            return {
                "message": f"User {target['name']} has {doc_count} audit documents on record. Account was deactivated to maintain institutional audit trail integrity."
            }
        else:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            return {"message": f"User {target['name']} deleted successfully."}

@router.get("/departments-list")
def get_admin_departments(current_user: dict = Depends(require_roles("Admin"))):
    inst_id = current_user["institution_id"]
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, code, name FROM departments WHERE institution_id = %s ORDER BY id", (inst_id,))
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
