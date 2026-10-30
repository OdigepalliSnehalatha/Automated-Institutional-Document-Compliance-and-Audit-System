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

def authenticate_user(
    email: str,
    password: str,
    institution_name: str | None = None
) -> dict:
    """
    Authenticates a user against the database using email and password.
    Never trusts role from client; checks verified role stored in database.
    Does not require OTP for normal login.
    """
    email = email.strip().lower()
    password = password.strip() if password else ""

    if not email:
        raise HTTPException(status_code=400, detail="Official email address is required.")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")

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
                u.is_active,
                d.name AS department_name,
                d.code AS department_code,
                i.id AS institution_id,
                i.name AS institution_name,
                i.logo_url AS institution_logo
            FROM users u
            JOIN institution i ON i.id = u.institution_id
            LEFT JOIN departments d ON d.id = u.department_id
            WHERE LOWER(u.email) = %s
            ORDER BY u.id DESC
            LIMIT 1
            """,
            (email,)
        )
        user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.get("password_hash") or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=403,
            detail="Account is deactivated. Please contact your Institution Administrator."
        )

    return user

def register_new_user(
    name: str,
    email: str,
    password: str,
    role: str = "Faculty",
    department_id: int | None = None,
    institution_name: str = "Anantha Lakshmi Institute of Technology and Sciences"
) -> dict:
    """
    Registers a new user with email, name, password, and assigned role.
    Prevents duplicate registrations with the same email.
    """
    name = name.strip()
    email = email.strip().lower()
    password = password.strip()
    role = role.strip() if role else "Faculty"

    if not name:
        raise HTTPException(status_code=400, detail="Full name is required.")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid official email address is required.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Allowed roles: {', '.join(sorted(ALLOWED_ROLES))}")

    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = %s", (email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="An account with this email address is already registered. Please sign in."
            )

        cursor.execute("SELECT id, name FROM institution WHERE LOWER(name) = LOWER(%s)", (institution_name.strip(),))
        inst = cursor.fetchone()
        if not inst:
            cursor.execute("SELECT id, name FROM institution ORDER BY id LIMIT 1")
            inst = cursor.fetchone()
        inst_id = inst["id"] if inst else 6

        # Verify department if provided
        if department_id:
            cursor.execute("SELECT id FROM departments WHERE id = %s AND institution_id = %s", (department_id, inst_id))
            if not cursor.fetchone():
                department_id = None

        # Auditor and Admin typically do not require a single department constraint
        if role in ("Auditor", "Admin"):
            department_id = None

        pwd_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO users (institution_id, department_id, name, email, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id, name, email, role, department_id, institution_id, is_active
            """,
            (inst_id, department_id, name, email, pwd_hash, role)
        )
        new_user = cursor.fetchone()

        cursor.execute(
            """
            SELECT 
                u.id,
                u.name,
                u.email,
                u.role,
                u.department_id,
                u.is_active,
                d.name AS department_name,
                d.code AS department_code,
                i.id AS institution_id,
                i.name AS institution_name,
                i.logo_url AS institution_logo
            FROM users u
            JOIN institution i ON i.id = u.institution_id
            LEFT JOIN departments d ON d.id = u.department_id
            WHERE u.id = %s
            """,
            (new_user["id"],)
        )
        user_full = cursor.fetchone()

    return {
        "success": True,
        "message": "Account created successfully! You can now log in with your credentials.",
        "user": build_session_user(user_full)
    }

def build_session_user(user_record: dict) -> dict:
    return {
        "id": user_record["id"],
        "name": user_record.get("name"),
        "email": user_record["email"],
        "role": user_record["role"],
        "department_id": user_record.get("department_id"),
        "department_name": user_record.get("department_name"),
        "department_code": user_record.get("department_code"),
        "institution_id": user_record.get("institution_id") or 6,
        "institution_name": user_record.get("institution_name", "Anantha Lakshmi Institute of Technology and Sciences"),
        "institution_logo": user_record.get("institution_logo"),
        "is_active": user_record.get("is_active", True)
    }

def get_current_user(request: Request) -> dict:
    """Dependency ensuring request comes from an authenticated session user."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    return user

def require_roles(*allowed_roles: str):
    """Dependency enforcing role-based access control."""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def check_department_access(user: dict, target_department_id: int | None):
    """Enforces department scope for department-level roles (HOD, Faculty)."""
    if user["role"] in {"Admin", "Auditor"}:
        return True
    if target_department_id is None:
        return True
    if user.get("department_id") != target_department_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to access resources outside your department."
        )
    return True
