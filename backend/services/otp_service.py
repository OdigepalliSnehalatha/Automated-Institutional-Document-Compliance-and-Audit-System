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
    Sends the 6-digit OTP to the user's official email address via real SMTP (e.g. Gmail SMTP).
    Raises an HTTPException if SMTP configuration is missing or email delivery fails.
    Never logs or exposes the OTP or credentials.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_username or "noreply@institution.edu")

    if not smtp_host or not smtp_username or not smtp_password:
        raise HTTPException(
            status_code=503,
            detail=(
                "Email delivery service is not configured. Please ensure SMTP_HOST, "
                "SMTP_PORT, SMTP_USERNAME, and SMTP_PASSWORD are set in the .env file."
            )
        )

    msg = EmailMessage()
    msg["Subject"] = f"Your Login Passcode ({otp}) - {institution_name}"
    msg["From"] = smtp_from
    msg["To"] = email

    # Plaintext fallback
    plain_text = (
        f"INSTITUTIONAL COMPLIANCE & AUDIT SYSTEM\n"
        f"Institution: {institution_name}\n"
        f"Role: {role}\n\n"
        f"Your one-time login passcode is: {otp}\n\n"
        f"This code will expire in {OTP_EXPIRY_MINUTES} minutes and can only be used once.\n\n"
        f"SECURITY NOTICE:\n"
        f"Never share this verification code with anyone. If you did not request this login, "
        f"please contact your institution's System Administrator immediately.\n"
    )

    # HTML rich email
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
    .otp-badge {{ display: inline-block; font-size: 36px; font-weight: 800; letter-spacing: 6px; padding: 14px 28px; background: #eff6ff; color: #1d4ed8; border: 2px dashed #93c5fd; border-radius: 8px; margin: 20px 0; }}
    .expiry {{ font-size: 14px; color: #64748b; margin-bottom: 24px; }}
    .warning-box {{ background: #fffbeb; border-left: 4px solid #f59e0b; padding: 14px 16px; text-align: left; font-size: 13px; color: #92400e; border-radius: 4px; line-height: 1.5; }}
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
      <p style="font-size: 15px; margin-top: 0;">You requested a secure login passcode for role: <strong>{role}</strong></p>
      <div class="otp-badge">{otp}</div>
      <p class="expiry">⏱️ This code is valid for <strong>{OTP_EXPIRY_MINUTES} minutes</strong> and can only be used once.</p>
      <div class="warning-box">
        <strong>⚠️ Security Warning:</strong> Do not disclose this code to anyone. Our administrators will never ask for your one-time code. If you did not initiate this login attempt, please notify your institutional IT administrator immediately.
      </div>
    </div>
    <div class="footer">
      Automated Security Verification &bull; {institution_name}
    </div>
  </div>
</body>
</html>"""

    msg.set_content(plain_text)
    msg.add_alternative(html_content, subtype="html")

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=12) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=502,
            detail="SMTP Authentication failed. Please check your SMTP username and App Password."
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to dispatch verification email: {str(e)}"
        )

def create_and_send_otp(institution_name: str, email: str, role: str) -> None:
    """
    Validates cooldown, invalidates prior unused OTPs, stores hashed OTP,
    and transmits OTP via real email.
    """
    email = email.strip().lower()
    institution_name = institution_name.strip()

    with get_db_cursor(commit=True) as cursor:
        # Check cooldown on the latest active or recently issued OTP
        cursor.execute(
            """
            SELECT created_at
            FROM login_otps
            WHERE LOWER(email) = %s AND role = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email, role)
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

    # Deliver via real email only. If delivery fails, the exception bubbles up.
    send_real_email_otp(email, institution_name, role, otp)

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
