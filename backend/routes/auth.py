from fastapi import APIRouter, Request, HTTPException
from backend.models.schemas import (
    LoginRequest,
    VerifyOTPRequest,
    RegisterRequest,
    VerifyRegistrationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from backend.services.auth_service import (
    validate_user_login,
    register_new_user,
    build_session_user,
    get_current_user,
    hash_password,
    ALLOWED_ROLES
)
from backend.services.otp_service import (
    create_and_send_login_otp,
    verify_login_otp,
    verify_registration_otp
)
from backend.database import get_db_cursor

router = APIRouter(tags=["Authentication"])

@router.post("/login")
@router.post("/auth/request-otp")
def login(data: LoginRequest):
    # 1. Validate credentials & role against database
    user = validate_user_login(
        institution_name=data.institution_name,
        email=data.email,
        role=data.role,
        password=data.password
    )

    # 2. Generate and store hashed OTP, dispatch via real email service
    create_and_send_login_otp(
        institution_name=user["institution_name"],
        email=user["email"],
        role=user["role"]
    )

    return {
        "message": f"A 6-digit verification code has been dispatched to {user['email']}.",
        "requires_otp": True,
        "email": user["email"],
        "institution": user["institution_name"],
        "role": user["role"]
    }

@router.post("/verify-otp")
def verify_otp(data: VerifyOTPRequest, request: Request):
    # 1. Verify OTP against hash, expiration, and attempt limits
    verify_login_otp(
        email=data.email,
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
            (data.email.strip().lower(),)
        )
        user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="User record not found.")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is deactivated. Access denied.")

    session_user = build_session_user(user)

    # 3. Create server-side session
    request.session.clear()
    request.session["user"] = session_user

    return {
        "message": "OTP verified successfully. Welcome to the portal!",
        "authenticated": True,
        "user": session_user
    }

@router.post("/register")
@router.post("/auth/register")
def register(data: RegisterRequest):
    return register_new_user(
        name=data.name,
        email=data.email,
        password=data.password,
        department_id=data.department_id,
        institution_name=data.institution_name or "Anantha Lakshmi Institute of Technology and Sciences"
    )

@router.post("/verify-registration")
@router.post("/auth/verify-registration")
def verify_registration(data: VerifyRegistrationRequest, request: Request):
    new_user = verify_registration_otp(
        email=data.email,
        entered_otp=data.otp
    )

    session_user = build_session_user(new_user)
    request.session.clear()
    request.session["user"] = session_user

    return {
        "message": f"Welcome, {session_user['name']}! Your institutional account has been verified and created successfully.",
        "authenticated": True,
        "user": session_user
    }

@router.post("/auth/forgot-password")
@router.post("/forgot-password")
def forgot_password_request(data: ForgotPasswordRequest):
    email = data.email.strip().lower()
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT u.id, u.name, u.email, u.role, u.is_active, i.name AS institution_name
            FROM users u
            JOIN institution i ON i.id = u.institution_id
            WHERE LOWER(u.email) = %s
            """,
            (email,)
        )
        user = cursor.fetchone()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="No registered account found with this email address."
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=403,
            detail="This account is deactivated. Please contact your Institution Administrator."
        )

    create_and_send_login_otp(
        institution_name=user["institution_name"],
        email=user["email"],
        role="Password Reset"
    )

    return {
        "message": f"A password reset passcode has been dispatched to {user['email']}.",
        "email": user["email"]
    }

@router.post("/auth/reset-password")
@router.post("/reset-password")
def reset_password_request(data: ResetPasswordRequest):
    email = data.email.strip().lower()
    if len(data.new_password.strip()) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long.")

    # Verify OTP
    verify_login_otp(email=email, entered_otp=data.otp)

    # Hash new password and update database
    new_hash = hash_password(data.new_password.strip())
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE LOWER(email) = %s RETURNING id",
            (new_hash, email)
        )
        updated = cursor.fetchone()

    if not updated:
        raise HTTPException(status_code=404, detail="User account not found.")

    return {
        "message": "Password successfully reset! You can now log in with your new password.",
        "success": True
    }

@router.get("/auth/me")
@router.get("/me")
def auth_me(request: Request):
    user = get_current_user(request)
    return {
        "authenticated": True,
        "user": user,
        "id": user.get("id"),
        "email": user.get("email"),
        "role": user.get("role"),
        "institution": user.get("institution"),
        "institution_logo": user.get("institution_logo"),
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
