import bcrypt
from fastapi import HTTPException, Request, Depends
from backend.database import get_db_cursor

ALLOWED_ROLES = {"Auditor", "HOD", "Faculty"}

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

def validate_user_login(institution_name: str, role: str, email: str, password: str) -> dict:
    role = role.strip()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    email = email.strip().lower()
    institution_name = institution_name.strip()

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                u.id,
                u.name,
                u.email,
                u.password_hash,
                u.role,
                u.department_id,
                d.name AS department_name,
                i.id AS institution_id,
                i.name AS institution_name
            FROM users u
            JOIN institution i ON i.id = u.institution_id
            LEFT JOIN departments d ON d.id = u.department_id
            WHERE LOWER(u.email) = %s
              AND LOWER(i.name) = LOWER(%s)
            """,
            (email, institution_name)
        )
        user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid institution, email, or password.")

    if user["role"] != role:
        raise HTTPException(status_code=401, detail=f"Selected role does not match registered role for this user.")

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid login credentials.")

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
    Auditor has institution-wide access (target_department_id allowed).
    HOD and Faculty can only access their assigned department.
    """
    role = current_user.get("role")
    user_dept_id = current_user.get("department_id")

    if role == "Auditor":
        # Auditor is institution-level; can view or manage all departments in their institution
        return

    if user_dept_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to any department.")

    if target_department_id is not None and int(user_dept_id) != int(target_department_id):
        raise HTTPException(status_code=403, detail="Access denied: Cannot access documents from another department.")
