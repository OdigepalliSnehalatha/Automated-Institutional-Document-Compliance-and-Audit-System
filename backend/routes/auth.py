from fastapi import APIRouter, Request, HTTPException
from backend.models.schemas import LoginRequest, VerifyOTPRequest
from backend.services.auth_service import (
    validate_user_login,
    build_session_user,
    get_current_user,
    ALLOWED_ROLES
)
from backend.services.otp_service import (
    create_and_send_otp,
    verify_login_otp
)
from backend.database import get_db_cursor

router = APIRouter(tags=["Authentication"])

@router.post("/login")
@router.post("/auth/request-otp")
def login(data: LoginRequest):
    # 1. Validate credentials & role
    user = validate_user_login(
        institution_name=data.institution_name,
        role=data.role,
        email=data.email,
        password=data.password
    )

    # 2. Generate and store hashed OTP, dispatch email / log
    create_and_send_otp(
        institution_name=user["institution_name"],
        email=user["email"],
        role=user["role"]
    )

    return {
        "message": "OTP has been sent to your registered email.",
        "requires_otp": True,
        "email": user["email"],
        "institution": user["institution_name"]
    }

@router.post("/verify-otp")
def verify_otp(data: VerifyOTPRequest, request: Request):
    # 1. Verify OTP against hash, expiration, and attempt limits
    verify_login_otp(
        institution_name=data.institution_name,
        email=data.email,
        role=data.role,
        entered_otp=data.otp
    )

    # 2. Query user details
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                u.id,
                u.name,
                u.email,
                u.role,
                u.department_id,
                d.name AS department_name,
                i.id AS institution_id,
                i.name AS institution_name
            FROM users u
            JOIN institution i ON i.id = u.institution_id
            LEFT JOIN departments d ON d.id = u.department_id
            WHERE LOWER(u.email) = %s
              AND u.role = %s
              AND LOWER(i.name) = LOWER(%s)
            LIMIT 1
            """,
            (data.email.strip().lower(), data.role.strip(), data.institution_name.strip())
        )
        user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="User record not found.")

    session_user = build_session_user(user)

    # 3. Create server-side session
    request.session.clear()
    request.session["user"] = session_user

    return {
        "message": "OTP verified successfully.",
        "authenticated": True,
        "user": session_user
    }

@router.get("/auth/me")
def auth_me(request: Request):
    user = get_current_user(request)
    return {
        "authenticated": True,
        "user": user,
        "id": user.get("id"),
        "email": user.get("email"),
        "role": user.get("role"),
        "institution": user.get("institution"),
        "department": user.get("department"),
        "department_id": user.get("department_id")
    }

@router.post("/logout")
@router.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully."}

@router.get("/institutions")
def get_institutions():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, name FROM institution ORDER BY name")
        return cursor.fetchall()

@router.get("/departments")
def get_departments(institution_id: int | None = None):
    with get_db_cursor() as cursor:
        if institution_id:
            cursor.execute("SELECT id, code, name FROM departments WHERE institution_id = %s ORDER BY id", (institution_id,))
        else:
            cursor.execute("SELECT id, code, name FROM departments ORDER BY id")
        return cursor.fetchall()

@router.get("/document-types")
def get_document_types():
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name, description 
            FROM document_types 
            WHERE is_active = TRUE 
            ORDER BY id
            """
        )
        return cursor.fetchall()
