import os
import secrets
import hashlib
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from fastapi import HTTPException
from backend.database import get_db_cursor

OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 10
PROTOTYPE_MODE = True
PROTOTYPE_FIXED_OTP = "123456"

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()

def generate_otp() -> str:
    if PROTOTYPE_MODE:
        return PROTOTYPE_FIXED_OTP
    return f"{secrets.randbelow(1000000):06d}"

def send_otp_notification(email: str, institution_name: str, otp: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_username or "noreply@compliance-system.edu")

    # Always log OTP in server console for local testing / demo reliability
    print(f"\n=======================================================")
    print(f"[OTP NOTIFICATION] To: {email} | Institution: {institution_name}")
    print(f" >>> LOGIN OTP: {otp} <<<")
    print(f"Expires in: {OTP_EXPIRY_MINUTES} minutes")
    print(f"=======================================================\n")

    if smtp_host and smtp_username and smtp_password:
        try:
            msg = EmailMessage()
            msg["Subject"] = "Your Institutional System Login OTP"
            msg["From"] = smtp_from
            msg["To"] = email
            msg.set_content(
                f"Your login OTP is: {otp}\n\n"
                f"Institution: {institution_name}\n"
                f"This OTP expires in {OTP_EXPIRY_MINUTES} minutes.\n\n"
                f"If you did not request this login, please ignore this email."
            )
            with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        except Exception as e:
            print(f"[WARNING] SMTP delivery failed ({e}), continuing with local console OTP.")

def create_and_send_otp(institution_name: str, email: str, role: str) -> str:
    email = email.strip().lower()
    institution_name = institution_name.strip()
    otp = generate_otp()
    otp_hashed = hash_otp(otp)
    expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

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
        # Insert fresh OTP
        cursor.execute(
            """
            INSERT INTO login_otps
                (institution_name, email, role, otp_hash, expires_at, attempts, is_used)
            VALUES (%s, %s, %s, %s, %s, 0, FALSE)
            """,
            (institution_name, email, role, otp_hashed, expires_at)
        )

    send_otp_notification(email, institution_name, otp)
    return otp

def verify_login_otp(institution_name: str, email: str, role: str, entered_otp: str) -> bool:
    email = email.strip().lower()
    institution_name = institution_name.strip()
    entered_otp = entered_otp.strip()

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT id, otp_hash, expires_at, attempts, is_used
            FROM login_otps
            WHERE LOWER(email) = %s
              AND role = %s
              AND LOWER(institution_name) = LOWER(%s)
              AND is_used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email, role, institution_name)
        )
        record = cursor.fetchone()

        if not record:
            raise HTTPException(
                status_code=400,
                detail="No active OTP found. Please request a new OTP."
            )

        otp_id = record["id"]
        stored_hash = record["otp_hash"]
        expires_at = record["expires_at"]
        attempts = record["attempts"]

        is_prototype_valid = (PROTOTYPE_MODE and entered_otp == PROTOTYPE_FIXED_OTP)

        if not is_prototype_valid and datetime.now() > expires_at:
            raise HTTPException(
                status_code=400,
                detail="OTP has expired. Please request a new OTP."
            )

        if not is_prototype_valid and attempts >= MAX_OTP_ATTEMPTS:
            raise HTTPException(
                status_code=400,
                detail="Maximum OTP attempts exceeded. Please request a new OTP."
            )

        entered_hash = hash_otp(entered_otp)
        if not is_prototype_valid and not secrets.compare_digest(entered_hash, stored_hash):
            cursor.execute(
                "UPDATE login_otps SET attempts = attempts + 1 WHERE id = %s",
                (otp_id,)
            )
            raise HTTPException(status_code=400, detail="Invalid OTP entered.")

        # Mark OTP used
        cursor.execute(
            "UPDATE login_otps SET is_used = TRUE WHERE id = %s",
            (otp_id,)
        )

    return True
