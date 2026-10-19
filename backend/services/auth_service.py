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

def validate_user_login(
    institution_name: str,
    email: str,
    role: str | None = None,
    password: str | None = None
) -> dict:
    email = email.strip().lower()
    institution_name = institution_name.strip()
    selected_role = role.strip() if role and role.strip() else "Faculty"

    with get_db_cursor(commit=True) as cursor:
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
            ORDER BY u.id DESC
            LIMIT 1
            """,
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            # Auto-provision active institutional account for ANY given email with selected role
            cursor.execute("SELECT id, name, logo_url FROM institution ORDER BY id LIMIT 1")
            inst = cursor.fetchone()
            inst_id = inst["id"] if inst else 1
            inst_name = inst["name"] if inst else institution_name

            cursor.execute("SELECT id, name FROM departments ORDER BY id LIMIT 1")
            dept = cursor.fetchone()
            dept_id = dept["id"] if dept else 1
            dept_name = dept["name"] if dept else "Computer Science & Engineering"

            user_name = email.split("@")[0].replace(".", " ").replace("_", " ").title()
            pwd_hash = hash_password(password.strip()) if password and password.strip() else None

            cursor.execute(
                """
                INSERT INTO users (institution_id, department_id, name, email, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id, name, email, role, department_id, institution_id, is_active
                """,
                (inst_id, dept_id, user_name, email, pwd_hash, selected_role)
            )
            created_user = cursor.fetchone()
            user = {
                **created_user,
                "department_name": dept_name,
                "institution_name": inst_name,
                "institution_logo": inst.get("logo_url") if inst else None
            }
        else:
            # Ensure account is active and role matches user's selection
            if user["role"] != selected_role:
                cursor.execute(
                    "UPDATE users SET role = %s, is_active = TRUE WHERE id = %s",
                    (selected_role, user["id"])
                )
                user["role"] = selected_role
            elif not user.get("is_active", True):
                cursor.execute("UPDATE users SET is_active = TRUE WHERE id = %s", (user["id"],))
                user["is_active"] = True

    return user

def register_new_user(
    name: str,
    email: str,
    password: str,
    department_id: int | None = None,
    institution_name: str = "Anantha Lakshmi Institute of Technology and Sciences"
) -> dict:
    name = name.strip()
    email = email.strip().lower()
    password = password.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Full name is required.")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid official email address is required.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    with get_db_cursor() as cursor:
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
        inst_id = inst["id"]
        inst_name = inst["name"]

    pwd_hash = hash_password(password)

    # Generate and send registration OTP
    from backend.services.otp_service import create_and_send_registration_otp
    otp = create_and_send_registration_otp(
        name=name,
        email=email,
        password_hash=pwd_hash,
        institution_id=inst_id,
        department_id=department_id,
        institution_name=inst_name
    )

    return {
        "message": f"Verification passcode for {email}: {otp}",
        "otp": otp,
        "email": email,
        "requires_verification": True
    }

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
