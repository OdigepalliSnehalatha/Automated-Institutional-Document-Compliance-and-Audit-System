import bcrypt
from fastapi import HTTPException, Request, Depends
from backend.database import get_db_cursor

ALLOWED_ROLES = {"Admin", "Auditor", "HOD", "Faculty"}

def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
    except Exception:
        return False

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

def validate_user_login(institution_name: str, role: str, email: str, password: str | None = None) -> dict:
    role = role.strip()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    email = email.strip().lower()
    institution_name = institution_name.strip()

    with get_db_cursor(commit=True) as cursor:
        # 1. Resolve institution
        cursor.execute("SELECT id, name FROM institution WHERE LOWER(name) = LOWER(%s)", (institution_name,))
        inst = cursor.fetchone()
        if not inst:
            cursor.execute("SELECT id, name FROM institution ORDER BY id LIMIT 1")
            inst = cursor.fetchone()
            if not inst:
                cursor.execute(
                    "INSERT INTO institution (name, email) VALUES (%s, %s) RETURNING id, name",
                    (institution_name, email)
                )
                inst = cursor.fetchone()
        inst_id = inst["id"]

        # Default department for HOD/Faculty if needed
        cursor.execute("SELECT id FROM departments WHERE institution_id = %s ORDER BY id LIMIT 1", (inst_id,))
        dept_row = cursor.fetchone()
        default_dept_id = dept_row["id"] if dept_row else None

        # 2. Check if user already exists
        cursor.execute(
            """
            SELECT 
                u.id,
                u.name,
                u.email,
                u.password_hash,
                u.role,
                u.department_id,
                u.is_active,
                d.name AS department_name,
                i.id AS institution_id,
                i.name AS institution_name,
                i.logo_url AS institution_logo
            FROM users u
            JOIN institution i ON i.id = u.institution_id
            LEFT JOIN departments d ON d.id = u.department_id
            WHERE LOWER(u.email) = %s
              AND u.institution_id = %s
            """,
            (email, inst_id)
        )
        user = cursor.fetchone()

        if not user:
            # Auto-provision user account for the entered email and role
            name_part = email.split("@")[0].replace(".", " ").title()
            user_dept = default_dept_id if role in {"Faculty", "HOD"} else None
            cursor.execute(
                """
                INSERT INTO users (institution_id, department_id, name, email, role, is_active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id, name, email, role, department_id, is_active
                """,
                (inst_id, user_dept, name_part, email, role)
            )
            created_user = cursor.fetchone()
            cursor.execute(
                """
                SELECT 
                    u.id,
                    u.name,
                    u.email,
                    u.password_hash,
                    u.role,
                    u.department_id,
                    u.is_active,
                    d.name AS department_name,
                    i.id AS institution_id,
                    i.name AS institution_name,
                    i.logo_url AS institution_logo
                FROM users u
                JOIN institution i ON i.id = u.institution_id
                LEFT JOIN departments d ON d.id = u.department_id
                WHERE u.id = %s
                """,
                (created_user["id"],)
            )
            user = cursor.fetchone()
        else:
            # Update role to the user's selected role and ensure active
            if user["role"] != role or not user.get("is_active", True):
                user_dept = user["department_id"] or (default_dept_id if role in {"Faculty", "HOD"} else None)
                cursor.execute(
                    """
                    UPDATE users
                    SET role = %s, is_active = TRUE, department_id = %s
                    WHERE id = %s
                    """,
                    (role, user_dept, user["id"])
                )
                cursor.execute(
                    """
                    SELECT 
                        u.id,
                        u.name,
                        u.email,
                        u.password_hash,
                        u.role,
                        u.department_id,
                        u.is_active,
                        d.name AS department_name,
                        i.id AS institution_id,
                        i.name AS institution_name,
                        i.logo_url AS institution_logo
                    FROM users u
                    JOIN institution i ON i.id = u.institution_id
                    LEFT JOIN departments d ON d.id = u.department_id
                    WHERE u.id = %s
                    """,
                    (user["id"],)
                )
                user = cursor.fetchone()

    # Optional password check if password was provided and user has a password_hash set
    if password and password.strip() and user.get("password_hash"):
        if not verify_password(password.strip(), user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid password provided.")

    return user

def build_session_user(user_record: dict) -> dict:
    return {
        "id": user_record["id"],
        "name": user_record.get("name"),
        "email": user_record["email"],
        "role": user_record["role"],
        "institution_id": user_record["institution_id"],
        "institution_name": user_record["institution_name"],
        "institution": user_record["institution_name"],
        "institution_logo": user_record.get("institution_logo") or user_record.get("logo_url"),
        "department_id": user_record.get("department_id"),
        "department_name": user_record.get("department_name"),
        "department": user_record.get("department_name")
    }

def get_current_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    return user

def require_roles(*roles):
    def dependency(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Operation requires one of roles: {', '.join(roles)}"
            )
        return current_user
    return dependency

def check_department_access(current_user: dict, target_department_id: int | None):
    """
    Admin and Auditor have institution-wide access.
    Faculty can submit and access documents across all branches/departments in their institution.
    HOD is department-specific and oversees their assigned department.
    """
    role = current_user.get("role")
    user_dept_id = current_user.get("department_id")

    if role in {"Admin", "Auditor", "Faculty", "HOD"}:
        return

    if user_dept_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to any department.")

    if target_department_id is not None and int(user_dept_id) != int(target_department_id):
        raise HTTPException(status_code=403, detail="Access denied: Cannot access documents from another department.")
