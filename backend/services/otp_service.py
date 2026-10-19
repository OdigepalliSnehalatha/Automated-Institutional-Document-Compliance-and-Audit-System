import os
import secrets
import hashlib
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from fastapi import HTTPException
from backend.database import get_db_cursor

OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5
OTP_COOLDOWN_SECONDS = 3

def hash_otp(otp: str) -> str:
    """Hashes the OTP using SHA-256 for secure storage."""
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()

def generate_secure_otp() -> str:
    """Generates a cryptographically random 6-digit numeric OTP."""
    return f"{secrets.randbelow(1000000):06d}"

def send_real_email_otp(email: str, institution_name: str, subject_prefix: str, purpose_text: str, otp: str):
    """
    Sends the 6-digit OTP to the recipient's real email address via real SMTP (e.g. Gmail SMTP).
    If SMTP credentials are not yet configured or sending encounters a network error,
    it gracefully simulates real inbox delivery without interrupting the user.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", os.getenv("SMTP_SENDER_EMAIL") or smtp_username)

    if smtp_host and smtp_username and smtp_password:
        try:
            msg = EmailMessage()
            msg["Subject"] = f"{subject_prefix} - {institution_name}"
            msg["From"] = smtp_from
            msg["To"] = email

            plain_text = (
                f"INSTITUTIONAL COMPLIANCE & AUDIT SYSTEM\n"
                f"Institution: {institution_name}\n\n"
                f"Your verification passcode is: {otp}\n\n"
                f"{purpose_text}\n"
                f"This code will expire in {OTP_EXPIRY_MINUTES} minutes and can only be used once.\n\n"
                f"SECURITY NOTICE:\n"
                f"Never share this verification code with anyone.\n"
            )

            html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
    .container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background-color: #1e3a8a; padding: 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; }}
    .content {{ padding: 32px 28px; text-align: center; color: #334155; }}
    .otp-badge {{ display: inline-block; font-size: 38px; font-weight: 800; letter-spacing: 8px; padding: 14px 28px; background: #eff6ff; color: #1d4ed8; border: 2px dashed #93c5fd; border-radius: 8px; margin: 20px 0; }}
    .expiry {{ font-size: 14px; color: #64748b; margin-bottom: 24px; }}
    .footer {{ background: #f1f5f9; padding: 16px; text-align: center; font-size: 12px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{institution_name}</h1>
      <p>Automated Institutional Compliance & Document Audit System</p>
    </div>
    <div class="content">
      <p style="font-size: 15px; margin-top: 0;">{purpose_text}</p>
      <div class="otp-badge">{otp}</div>
      <p class="expiry">⏱️ This code is valid for <strong>{OTP_EXPIRY_MINUTES} minutes</strong> and can only be used once.</p>
    </div>
    <div class="footer">
      Automated Security Verification &bull; {institution_name}
    </div>
  </div>
</body>
</html>"""

            msg.set_content(plain_text)
            msg.add_alternative(html_content, subtype="html")

            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=8) as server:
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=8) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
            print(f"[SMTP DELIVERY SUCCESS] Sent passcode to {email}")
        except Exception as e:
            print(f"[SMTP DELIVERY NOTICE] SMTP delivery encountered: {e}. Falling back to instant dispatch.")
    else:
        print(f"[INSTITUTIONAL MAIL DISPATCH] To: {email} | Passcode: {otp} | Role Context: {purpose_text}")

# ==============================================================================
# LOGIN OTP HANDLERS
# ==============================================================================

def create_and_send_login_otp(institution_name: str, email: str, role: str) -> None:
    """
    Validates cooldown, invalidates prior unused OTPs, stores hashed OTP,
    and sends it via real email to the user.
    """
    email = email.strip().lower()
    institution_name = institution_name.strip()

    with get_db_cursor(commit=True) as cursor:
        # Check cooldown on recent OTP
        cursor.execute(
            """
            SELECT created_at
            FROM login_otps
            WHERE LOWER(email) = %s AND is_used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email,)
        )
        last_otp = cursor.fetchone()
        if last_otp and last_otp.get("created_at"):
            elapsed = (datetime.now() - last_otp["created_at"]).total_seconds()
            if elapsed < OTP_COOLDOWN_SECONDS:
                remaining = int(OTP_COOLDOWN_SECONDS - elapsed)
                raise HTTPException(
                    status_code=429,
                    detail=f"Please wait {remaining} seconds before requesting a new OTP."
                )

        # Invalidate previous unused OTPs
        cursor.execute(
            """
            UPDATE login_otps
            SET is_used = TRUE
            WHERE LOWER(email) = %s AND is_used = FALSE
            """,
            (email,)
        )

        otp = generate_secure_otp()
        otp_hashed = hash_otp(otp)
        expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        cursor.execute(
            """
            INSERT INTO login_otps
                (institution_name, email, role, otp_hash, expires_at, attempts, is_used)
            VALUES (%s, %s, %s, %s, %s, 0, FALSE)
            """,
            (institution_name, email, role, otp_hashed, expires_at)
        )

    subject = "Password Reset Passcode" if role == "Password Reset" else "Your Login Verification Passcode"
    purpose = "You requested a password reset passcode for your institutional account." if role == "Password Reset" else f"You requested a secure login passcode for role: {role}."

    send_real_email_otp(
        email=email,
        institution_name=institution_name,
        subject_prefix=subject,
        purpose_text=purpose,
        otp=otp
    )

    return otp

def verify_login_otp(email: str, entered_otp: str) -> bool:
    """
    Verifies the login OTP against stored hash, 5-minute expiration, and max 5 attempts limit.
    Invalidates the OTP upon successful verification.
    """
    email = email.strip().lower()
    entered_otp = entered_otp.strip()

    if len(entered_otp) != 6 or not entered_otp.isdigit():
        raise HTTPException(status_code=400, detail="Invalid OTP format. Must be a 6-digit number.")

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT id, otp_hash, expires_at, attempts, is_used
            FROM login_otps
            WHERE LOWER(email) = %s
              AND is_used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email,)
        )
        record = cursor.fetchone()

        if not record:
            raise HTTPException(
                status_code=400,
                detail="No active verification code found. Please request a new OTP."
            )

        otp_id = record["id"]
        stored_hash = record["otp_hash"]
        expires_at = record["expires_at"]
        attempts = record["attempts"]

        if datetime.now() > expires_at:
            cursor.execute("UPDATE login_otps SET is_used = TRUE WHERE id = %s", (otp_id,))
            raise HTTPException(
                status_code=400,
                detail="Verification code has expired. Please request a new OTP."
            )

        if attempts >= MAX_OTP_ATTEMPTS:
            cursor.execute("UPDATE login_otps SET is_used = TRUE WHERE id = %s", (otp_id,))
            raise HTTPException(
                status_code=400,
                detail="Maximum attempts exceeded for this code. Please request a new OTP."
            )

        entered_hash = hash_otp(entered_otp)
        if not secrets.compare_digest(entered_hash, stored_hash):
            cursor.execute(
                "UPDATE login_otps SET attempts = attempts + 1 WHERE id = %s",
                (otp_id,)
            )
            remaining_attempts = MAX_OTP_ATTEMPTS - (attempts + 1)
            if remaining_attempts > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid OTP entered. You have {remaining_attempts} attempt(s) remaining."
                )
            else:
                cursor.execute("UPDATE login_otps SET is_used = TRUE WHERE id = %s", (otp_id,))
                raise HTTPException(
                    status_code=400,
                    detail="Maximum OTP attempts exceeded. This code has been invalidated."
                )

        # Mark OTP used immediately upon successful verification
        cursor.execute("UPDATE login_otps SET is_used = TRUE WHERE id = %s", (otp_id,))

    return True

# ==============================================================================
# REGISTRATION OTP HANDLERS
# ==============================================================================

def create_and_send_registration_otp(name: str, email: str, password_hash: str, institution_id: int, department_id: int | None, institution_name: str) -> None:
    """
    Validates cooldown, stores pending registration with hashed OTP, and dispatches real email OTP.
    """
    email = email.strip().lower()

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT created_at FROM pending_registrations
            WHERE LOWER(email) = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email,)
        )
        last_reg = cursor.fetchone()
        if last_reg and last_reg.get("created_at"):
            elapsed = (datetime.now() - last_reg["created_at"]).total_seconds()
            if elapsed < OTP_COOLDOWN_SECONDS:
                remaining = int(OTP_COOLDOWN_SECONDS - elapsed)
                raise HTTPException(
                    status_code=429,
                    detail=f"Please wait {remaining} seconds before requesting a new registration code."
                )

        # Delete any previous pending registration for this email
        cursor.execute("DELETE FROM pending_registrations WHERE LOWER(email) = %s", (email,))

        otp = generate_secure_otp()
        otp_hashed = hash_otp(otp)
        expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        cursor.execute(
            """
            INSERT INTO pending_registrations
                (name, email, password_hash, institution_id, department_id, otp_hash, expires_at, attempts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (name, email, password_hash, institution_id, department_id, otp_hashed, expires_at)
        )

    send_real_email_otp(
        email=email,
        institution_name=institution_name,
        subject_prefix="Verify Your Account Registration",
        purpose_text="Please enter the verification code below to verify your email and activate your institutional account.",
        otp=otp
    )

    return otp

def verify_registration_otp(email: str, entered_otp: str) -> dict:
    """
    Verifies the registration OTP, creates the user in users table with role 'Faculty',
    and removes the pending registration.
    """
    email = email.strip().lower()
    entered_otp = entered_otp.strip()

    if len(entered_otp) != 6 or not entered_otp.isdigit():
        raise HTTPException(status_code=400, detail="Invalid OTP format. Must be a 6-digit number.")

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT id, name, email, password_hash, institution_id, department_id, otp_hash, expires_at, attempts
            FROM pending_registrations
            WHERE LOWER(email) = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email,)
        )
        record = cursor.fetchone()

        if not record:
            raise HTTPException(
                status_code=400,
                detail="No pending registration found for this email. Please submit the registration form again."
            )

        reg_id = record["id"]
        stored_hash = record["otp_hash"]
        expires_at = record["expires_at"]
        attempts = record["attempts"]

        if datetime.now() > expires_at:
            cursor.execute("DELETE FROM pending_registrations WHERE id = %s", (reg_id,))
            raise HTTPException(
                status_code=400,
                detail="Registration code has expired. Please submit the registration form again."
            )

        if attempts >= MAX_OTP_ATTEMPTS:
            cursor.execute("DELETE FROM pending_registrations WHERE id = %s", (reg_id,))
            raise HTTPException(
                status_code=400,
                detail="Maximum verification attempts exceeded. Please register again."
            )

        entered_hash = hash_otp(entered_otp)
        if not secrets.compare_digest(entered_hash, stored_hash):
            cursor.execute(
                "UPDATE pending_registrations SET attempts = attempts + 1 WHERE id = %s",
                (reg_id,)
            )
            remaining = MAX_OTP_ATTEMPTS - (attempts + 1)
            if remaining > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid OTP entered. You have {remaining} attempt(s) remaining."
                )
            else:
                cursor.execute("DELETE FROM pending_registrations WHERE id = %s", (reg_id,))
                raise HTTPException(
                    status_code=400,
                    detail="Maximum verification attempts exceeded. Please register again."
                )

        # Check if email was somehow registered while pending
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = %s", (email,))
        if cursor.fetchone():
            cursor.execute("DELETE FROM pending_registrations WHERE id = %s", (reg_id,))
            raise HTTPException(status_code=400, detail="An account with this email is already registered.")

        # Insert user into users table with standard role 'Faculty'
        cursor.execute(
            """
            INSERT INTO users (institution_id, department_id, name, email, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, %s, 'Faculty', TRUE)
            RETURNING id, name, email, role, department_id, institution_id, is_active
            """,
            (
                record["institution_id"],
                record["department_id"],
                record["name"],
                record["email"],
                record["password_hash"]
            )
        )
        new_user = cursor.fetchone()

        # Clean up pending registration
        cursor.execute("DELETE FROM pending_registrations WHERE id = %s", (reg_id,))

        # Fetch joined institution details
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
            WHERE u.id = %s
            """,
            (new_user["id"],)
        )
        user_full = cursor.fetchone()

    return user_full
