from fastapi import APIRouter, Request, HTTPException
from backend.models.schemas import (
    LoginRequest,
    RegisterRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyOTPRequest
)
from backend.services.auth_service import (
    authenticate_user,
    register_new_user,
    build_session_user,
    get_current_user,
    hash_password,
    ALLOWED_ROLES
)
from backend.services.otp_service import (
    create_and_send_login_otp,
    verify_login_otp
)
from backend.database import get_db_cursor

router = APIRouter(tags=["Authentication"])

@router.post("/login")
@router.post("/auth/login")
def login(data: LoginRequest, request: Request):
    """
    Direct email and password authentication.
    Does not require OTP for normal login.
    Verifies assigned role directly from database.
    """
    user = authenticate_user(
        email=data.email,
        password=data.password or "",
        institution_name=data.institution_name
    )

    session_user = build_session_user(user)

    # Establish secure server-side session
    request.session.clear()
    request.session["user"] = session_user

    return {
        "authenticated": True,
        "message": f"Welcome back, {session_user['name']}!",
        "user": session_user
    }

@router.post("/register")
@router.post("/auth/register")
def register(data: RegisterRequest, request: Request):
    """
    Creates a new institutional user account with name, email, password, role, and department.
    Prevents duplicate registrations with the same email.
    """
    result = register_new_user(
        name=data.name,
        email=data.email,
        password=data.password,
        role=data.role or "Faculty",
        department_id=data.department_id,
        institution_name=data.institution_name or "Anantha Lakshmi Institute of Technology and Sciences"
    )

    # Automatically establish session after successful registration
    request.session.clear()
    request.session["user"] = result["user"]

    return {
        "success": True,
        "authenticated": True,
        "message": f"Account created successfully! Welcome, {result['user']['name']}.",
        "user": result["user"]
    }

@router.get("/auth/me")
@router.get("/me")
def get_session_profile(request: Request):
    """Restores active authenticated session."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="No active session. Please log in.")
    return {
        "authenticated": True,
        "user": user
    }

@router.post("/logout")
@router.post("/auth/logout")
def logout(request: Request):
    """Destroys active session."""
    request.session.clear()
    return {
        "authenticated": False,
        "message": "Logged out successfully."
    }

@router.get("/departments")
def get_departments(institution_id: int | None = None):
    """Lists available departments for registration and dropdowns."""
    with get_db_cursor() as cursor:
        if institution_id:
            cursor.execute("SELECT id, code, name FROM departments WHERE institution_id = %s ORDER BY id", (institution_id,))
        else:
            cursor.execute("SELECT id, code, name FROM departments ORDER BY id")
        return cursor.fetchall()

@router.get("/institutions")
def get_institutions():
    """Lists registered institutions."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, name, email, logo_url FROM institution ORDER BY name")
        return cursor.fetchall()

@router.post("/auth/forgot-password")
@router.post("/forgot-password")
def forgot_password_request(data: ForgotPasswordRequest):
    """Dispatches password reset OTP."""
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
        raise HTTPException(status_code=404, detail="No registered account found with this email address.")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="This account is deactivated. Please contact your Institution Administrator.")

    otp, delivery = create_and_send_login_otp(
        institution_name=user["institution_name"],
        email=user["email"],
        role="Password Reset"
    )

    email_delivered = delivery.get("delivered", False)
    msg = (
        f"Password reset code has been sent to {user['email']}."
        if email_delivered
        else f"Password reset passcode for {user['email']}: {otp}"
    )

    return {
        "message": msg,
        "otp": otp if not email_delivered else None,
        "email": user["email"],
        "email_delivered": email_delivered
    }

@router.post("/auth/reset-password")
@router.post("/reset-password")
def reset_password_request(data: ResetPasswordRequest):
    """Resets password using verified OTP."""
    email = data.email.strip().lower()
    if len(data.new_password.strip()) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long.")

    verify_login_otp(email=email, entered_otp=data.otp)

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
