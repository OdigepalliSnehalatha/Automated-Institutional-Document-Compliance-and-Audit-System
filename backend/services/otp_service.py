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
OTP_COOLDOWN_SECONDS = 60

def hash_otp(otp: str) -> str:
    """Hashes the OTP using SHA-256 for secure storage."""
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()

def generate_secure_otp() -> str:
    """Generates a cryptographically random 6-digit numeric OTP."""
    return f"{secrets.randbelow(1000000):06d}"

def send_real_email_otp(email: str, institution_name: str, role: str, otp: str):
    """
    Sends the 6-digit OTP to the user's email via SMTP if credentials are configured.
    If credentials are not configured or delivery fails, continues gracefully without blocking the user.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_username or "noreply@institution.edu")

    if not smtp_host or not smtp_username or not smtp_password:
        print(f"[OTP NOTIFICATION] To: {email} | Institution: {institution_name} | Role: {role} | Passcode: {otp}")
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = f"Your Login Passcode ({otp}) - {institution_name}"
        msg["From"] = smtp_from
        msg["To"] = email

        plain_text = (
            f"INSTITUTIONAL COMPLIANCE & AUDIT SYSTEM\n"
            f"Institution: {institution_name}\n"
            f"Role: {role}\n\n"
            f"Your one-time login passcode is: {otp}\n\n"
            f"This code will expire in {OTP_EXPIRY_MINUTES} minutes.\n"
        )
        msg.set_content(plain_text)

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=8) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=8) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
    except Exception as e:
        print(f"[OTP NOTICE] SMTP delivery could not complete ({e}). Passcode generated for {email}: {otp}")

def create_and_send_otp(institution_name: str, email: str, role: str) -> str:
    """
    Invalidates prior unused OTPs, stores hashed OTP, transmits OTP via email if SMTP is configured,
    and returns the generated OTP string.
    """
    email = email.strip().lower()
    institution_name = institution_name.strip()

    with get_db_cursor(commit=True) as cursor:
        # Invalidate previous unused OTPs
        cursor.execute(
            """
            UPDATE login_otps
            SET is_used = TRUE
            WHERE LOWER(email) = %s AND role = %s AND is_used = FALSE
            """,
            (email, role)
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

    # Deliver via real email if SMTP is configured (or fallback to graceful logging)
    send_real_email_otp(email, institution_name, role, otp)
    return otp

def verify_login_otp(institution_name: str, email: str, role: str, entered_otp: str) -> bool:
    """
    Verifies the OTP against stored hash, 5-minute expiration, and max 5 attempts limit.
    Invalidates the OTP upon successful verification.
    """
    email = email.strip().lower()
    institution_name = institution_name.strip()
    entered_otp = entered_otp.strip()

    if len(entered_otp) != 6 or not entered_otp.isdigit():
        raise HTTPException(status_code=400, detail="Invalid OTP format. Must be a 6-digit number.")

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT id, otp_hash, expires_at, attempts, is_used
            FROM login_otps
            WHERE LOWER(email) = %s
              AND role = %s
              AND is_used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email, role)
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
        cursor.execute(
            "UPDATE login_otps SET is_used = TRUE WHERE id = %s",
            (otp_id,)
        )

    return True
