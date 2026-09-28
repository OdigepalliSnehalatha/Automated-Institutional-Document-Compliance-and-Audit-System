from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from backend.services.auth_service import require_roles, get_current_user
from backend.database import get_db_cursor
from backend.models.schemas import FormatCreateRequest, FormatUpdateRequest

router = APIRouter(prefix="", tags=["Auditor"])

@router.get("/auditor/dashboard")
def get_auditor_dashboard(current_user: dict = Depends(require_roles("Auditor"))):
    inst_id = current_user["institution_id"]

    with get_db_cursor() as cursor:
        # Overview Cards
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
        counts = cursor.fetchone()

        # Total Formats
        cursor.execute(
            "SELECT COUNT(*) AS total_formats FROM document_formats WHERE institution_id = %s",
            (inst_id,)
        )
        formats_count = cursor.fetchone()["total_formats"]

        # Recent Submissions (up to 10)
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
            WHERE d.institution_id = %s
            ORDER BY d.uploaded_at DESC
            LIMIT 10
            """,
            (inst_id,)
        )
        recent_submissions = cursor.fetchall()

    return {
        "overview": {
            "total_documents": counts["total_documents"],
            "accepted_documents": counts["accepted_documents"],
            "rejected_documents": counts["rejected_documents"],
            "pending_documents": counts["pending_documents"],
            "total_formats": formats_count
        },
        "recent_submissions": recent_submissions
    }

@router.get("/formats")
def get_formats(
    department_id: Optional[int] = None,
    document_type_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    inst_id = current_user["institution_id"]
    query = """
        SELECT 
            df.id,
            df.institution_id,
            df.department_id,
            df.document_type_id,
            df.format_name,
            df.instructions,
            df.created_by,
            df.created_at,
            df.updated_at,
            dt.name AS document_type_name,
            dept.code AS department_code,
            dept.name AS department_name
        FROM document_formats df
        JOIN document_types dt ON dt.id = df.document_type_id
        LEFT JOIN departments dept ON dept.id = df.department_id
        WHERE df.institution_id = %s
    """
    params = [inst_id]

    if department_id:
        query += " AND (df.department_id = %s OR df.department_id IS NULL)"
        params.append(department_id)
    if document_type_id:
        query += " AND df.document_type_id = %s"
        params.append(document_type_id)

    query += " ORDER BY df.created_at DESC"

    with get_db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        formats = cursor.fetchall()

        for item in formats:
            cursor.execute(
                """
                SELECT id, format_id, requirement_name, requirement_type, requirement_value, is_required, display_order
                FROM format_requirements
                WHERE format_id = %s
                ORDER BY display_order ASC, id ASC
                """,
                (item["id"],)
            )
            item["requirements"] = cursor.fetchall()

    return formats

@router.post("/formats")
def create_format(
    data: FormatCreateRequest,
    current_user: dict = Depends(require_roles("Auditor"))
):
    inst_id = current_user["institution_id"]

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO document_formats
                (institution_id, department_id, document_type_id, format_name, instructions, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                inst_id,
                data.department_id,
                data.document_type_id,
                data.format_name.strip(),
                data.instructions,
                current_user["id"]
            )
        )
        format_record = cursor.fetchone()
        format_id = format_record["id"]

        saved_reqs = []
        for idx, req in enumerate(data.requirements, start=1):
            if not req.requirement_name.strip():
                continue
            cursor.execute(
                """
                INSERT INTO format_requirements
                    (format_id, requirement_name, requirement_type, requirement_value, is_required, display_order)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    format_id,
                    req.requirement_name.strip(),
                    req.requirement_type,
                    (req.requirement_value or "").strip(),
                    req.is_required,
                    req.display_order or idx
                )
            )
            saved_reqs.append(cursor.fetchone())

        format_record["requirements"] = saved_reqs

    return {
        "message": "Format created successfully.",
        "format": format_record
    }

@router.get("/formats/{format_id}")
def get_format(format_id: int, current_user: dict = Depends(get_current_user)):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                df.*,
                dt.name AS document_type_name,
                dept.name AS department_name
            FROM document_formats df
            JOIN document_types dt ON dt.id = df.document_type_id
            LEFT JOIN departments dept ON dept.id = df.department_id
            WHERE df.id = %s
            """,
            (format_id,)
        )
        fmt = cursor.fetchone()
        if not fmt:
            raise HTTPException(status_code=404, detail="Format not found.")

        cursor.execute(
            """
            SELECT id, format_id, requirement_name, requirement_type, requirement_value, is_required, display_order
            FROM format_requirements
            WHERE format_id = %s
            ORDER BY display_order ASC, id ASC
            """,
            (format_id,)
        )
        fmt["requirements"] = cursor.fetchall()
        return fmt

@router.put("/formats/{format_id}")
def update_format(
    format_id: int,
    data: FormatUpdateRequest,
    current_user: dict = Depends(require_roles("Auditor"))
):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM document_formats WHERE id = %s", (format_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Format not found.")

        # Update base fields if present
        updates = []
        params = []
        if data.format_name is not None:
            updates.append("format_name = %s")
            params.append(data.format_name.strip())
        if data.instructions is not None:
            updates.append("instructions = %s")
            params.append(data.instructions.strip())
        if data.department_id is not None:
            updates.append("department_id = %s")
            params.append(data.department_id)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(format_id)
            cursor.execute(
                f"UPDATE document_formats SET {', '.join(updates)} WHERE id = %s",
                tuple(params)
            )

        # Update requirements if provided
        if data.requirements is not None:
            cursor.execute("DELETE FROM format_requirements WHERE format_id = %s", (format_id,))
            for idx, req in enumerate(data.requirements, start=1):
                if not req.requirement_name.strip():
                    continue
                cursor.execute(
                    """
                    INSERT INTO format_requirements
                        (format_id, requirement_name, requirement_type, requirement_value, is_required, display_order)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        format_id,
                        req.requirement_name.strip(),
                        req.requirement_type,
                        (req.requirement_value or "").strip(),
                        req.is_required,
                        req.display_order or idx
                    )
                )

    return {"message": "Format updated successfully."}

@router.delete("/formats/{format_id}")
def delete_format(
    format_id: int,
    current_user: dict = Depends(require_roles("Auditor"))
):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM document_formats WHERE id = %s RETURNING id", (format_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Format not found.")

    return {"message": "Format deleted successfully."}
